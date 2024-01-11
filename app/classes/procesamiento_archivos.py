from pydantic import BaseModel, ValidationError

from .lectura_pandas import LecturaMercadoLibre, LecturaMercadoPago, LecturaEnterprise
from app.settings import RUTA_RESULTADOS

import pandas as pd
import os
import logging

logging.basicConfig(filename='app-pro.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

class ProcesamientoArchivos(BaseModel):
    df_mp: pd.DataFrame
    df_ml: pd.DataFrame
    df_et: pd.DataFrame
    valor_evaluar: float
    ruta_guardado: str
    nombre_carpeta: str


    class Config:
        arbitrary_types_allowed = True


    def consolidado_ventas_pagos(self):

        logging.info(f' --------------------------------- Consolidado de pagos --------------------------------- ')
        self.df_mp = self.df_mp[self.df_mp['description']!='payout']
        df_mp_reducido = self.df_mp[['description','order_id', 'cobro_por_descuento', 'comision_por_venta', 'ica', 'fuente', 'iva']]


        lista_mp_no_payment = df_mp_reducido[~df_mp_reducido['description'].isin(['payout', 'payment'])]['order_id'].unique().tolist()
        df_mp_no_payment = df_mp_reducido[df_mp_reducido['order_id'].isin(lista_mp_no_payment)]

        df_mp_no_order_id = self.df_mp[(pd.isna(self.df_mp['order_id'])) | (self.df_mp['order_id']=='')]
        net_debit_amount_sin_id = df_mp_no_order_id[df_mp_no_order_id['description']!='payment']['net_debit_amount'].unique().tolist()

        df_mp_no_payment = df_mp_no_payment[(~pd.isna(df_mp_no_payment['order_id'])) & (df_mp_no_payment['order_id']!='')]
        #df_mp_reducido = df_mp_reducido[df_mp_reducido['description']=='payment']

        df_mp_reducido = df_mp_reducido.drop('description', axis=1)
        df_mp_reducido = df_mp_reducido.groupby('order_id', as_index=False)[['cobro_por_descuento', 'comision_por_venta', 'ica', 'fuente', 'iva']].sum()

        df_concantenado = pd.merge(self.df_ml, df_mp_reducido, how='right', on='order_id')
        df_concantenado = df_concantenado[df_concantenado['order_id']!='']


        df_et_reducido = self.df_et[['order_id', 'fve', 'valor']]


        df_consolidado = pd.merge(df_concantenado, df_et_reducido, how='left', on='order_id')
        df_consolidado = df_consolidado.drop_duplicates(subset=['order_id'])

        df_consolidado['comision_por_venta'] = df_consolidado['comision_por_venta']
        df_consolidado['ica'] = abs(df_consolidado['ica'])
        df_consolidado['fuente'] = abs(df_consolidado['fuente'])
        df_consolidado['iva'] = abs(df_consolidado['iva'])

        df_consolidado['diferencia'] = df_consolidado['ingresos por productos (cop)'] - df_consolidado['valor']
        orden_columnas_original = ['ORDER_ID', 'Comprador', 'CC', 'fve', 'valor', 'diferencia', 'fecha_venta', 'Estado',
                        'Descripción del estado', 'Paquete de varios productos', 'Unidades',
                        'Ingresos por productos (COP)', 'Ingresos por envío (COP)',
                        'Cargo por venta e impuestos', 'Costos de envío',
                        'Anulaciones y reembolsos (COP)', 'Total (COP)', 'Venta por publicidad',
                        'cobro_por_descuento', 'comision_por_venta', 'ica', 'fuente', 'iva',
                        'SKU', '# de publicación', 'Tienda oficial',
                        'Título de la publicación', 'Variante',
                        'Precio unitario de venta de la publicación (COP)',
                        'Tipo de publicación', 'Factura adjunta',
                        'Datos personales o de empresa', 'Tipo y número de documento',
                        'Dirección', 'Tipo de contribuyente', 'Domicilio',
                        'Municipio o ciudad capital', 'Estado.1', 'Código postal', 'País',
                        'Forma de entrega', 'Fecha en camino', 'Fecha entregado',
                        'Transportista', 'Número de seguimiento', 'URL de seguimiento',
                        'Forma de entrega.1', 'Fecha en camino.1', 'Fecha entregado.1',
                        'Transportista.1', 'Número de seguimiento.1', 'URL de seguimiento.1',
                        'Reclamo abierto', 'Reclamo cerrado', 'Con mediación']
        
        orden_columnas = [col.lower() for col in orden_columnas_original]

        df_consolidado = df_consolidado.reindex(columns=orden_columnas)

        condicion_existe_cedula = ((df_consolidado['cc']!='') & (~df_consolidado['cc'].isnull()))
        condicion_erp = ((df_consolidado['fve']!='') & (~df_consolidado['fve'].isnull()))

        ordenes_mp_sinmlerp = df_consolidado[(~condicion_existe_cedula) & (~condicion_erp)]['order_id'].unique().tolist()
        ordenes_mperp_sinml = df_consolidado[(~condicion_existe_cedula) & (condicion_erp)]['order_id'].unique().tolist()
        ordenes_mpml_sinerp = df_consolidado[(condicion_existe_cedula) & (~condicion_erp)]['order_id'].unique().tolist()

        df_mp_sinmlerp = df_consolidado[df_consolidado['order_id'].isin(ordenes_mp_sinmlerp)]
        df_mperp_sinml = df_consolidado[df_consolidado['order_id'].isin(ordenes_mperp_sinml)]
        df_mpml_sinerp = df_consolidado[df_consolidado['order_id'].isin(ordenes_mpml_sinerp)]

        ordenes_mp_sinml = df_consolidado[(df_consolidado['cc']=='') | (df_consolidado['cc'].isnull())]['order_id'].unique().tolist()

        df_mp_no_payment = df_consolidado[df_consolidado['order_id'].isin(df_mp_no_payment['order_id'].to_list())]
        df_consolidado = df_consolidado[~df_consolidado['order_id'].isin(df_mp_no_payment['order_id'].to_list())]

        df_mp_sinml = df_consolidado[df_consolidado['order_id'].isin(ordenes_mp_sinml)]
        df_mpml_sinerp = df_consolidado[df_consolidado['order_id'].isin(ordenes_mpml_sinerp)]

        df_consolidado = df_consolidado[~df_consolidado['order_id'].isin(ordenes_mp_sinml + ordenes_mpml_sinerp + ordenes_mp_sinmlerp + ordenes_mperp_sinml)]

        valores_enterprise = df_consolidado['valor'].sum()
        comision = df_consolidado['comision_por_venta'].sum()
        ica = df_consolidado['ica'].sum()
        fuente = df_consolidado['fuente'].sum()
        iva = df_consolidado['iva'].sum()

        df_resumen = pd.DataFrame({
            'Observaciones':['BANCO', 'Comisión 12%', 'ReteICA (0.41%)', 'Retefuente (1,5%)', 'ReteIVA (15%)'],
            'D': [self.valor_evaluar, comision, ica, fuente, iva],
            'C': [valores_enterprise, 0, 0, 0, 0]
        })
        sum_row = pd.DataFrame({'Observaciones': ['total'], 'D': [df_resumen['D'].sum()], 'C': [df_resumen['C'].sum()]})
        df_resumen = pd.concat([df_resumen, sum_row], ignore_index=True)

        resultado = df_resumen.loc[5]['D'] - df_resumen.loc[5]['C']
        df_resumen['diferencia'] = [0, 0, 0, 0, 0, resultado]

        # Creamos un objeto ExcelWriter utilizando xlsxwriter
        logging.info(df_consolidado.to_string())
        writer = pd.ExcelWriter(f'{self.ruta_guardado}\\{self.nombre_carpeta} $ {self.valor_evaluar}.xlsx', engine='xlsxwriter')

        df_mp_no_order_id = df_mp_no_order_id[df_mp_no_order_id['description']!='reserve_for_payout']

        df_consolidado.to_excel(writer, sheet_name='Consolidado')
        df_resumen.to_excel(writer, sheet_name='Resumen')
        df_mp_no_payment.to_excel(writer, sheet_name='no_payment')
        df_mp_no_order_id.to_excel(writer, sheet_name='no_payment_no_order_id')
        df_mp_sinmlerp.to_excel(writer, sheet_name='mp_sinmlerp')
        df_mperp_sinml.to_excel(writer, sheet_name='mperp_sinml')
        df_mpml_sinerp.to_excel(writer, sheet_name='mpml_sinerp')

        # Guardamos el archivo
        writer.close()

        return df_consolidado
      
def ejecutar_procesamiento(fecha_fin: str, ml: LecturaMercadoLibre, mp: LecturaMercadoPago, et: LecturaEnterprise):
    nombre_carpeta_retiro = f'Ventas_CO_Mercado_Libre_RETIRO_{fecha_fin}'
    ruta_carpeta_retiro = f'{RUTA_RESULTADOS}/{nombre_carpeta_retiro}'
    if os.path.isdir(ruta_carpeta_retiro):
        raise ValueError(f'Ya existe una carpeta para ese retiro en la ruta: {ruta_carpeta_retiro}. Eliminela o cambiele el nombre antes de continuar')

    #try:
    os.mkdir(ruta_carpeta_retiro)

    ml.set_ruta_guardado(ruta_carpeta_retiro)
    mp.set_ruta_guardado(ruta_carpeta_retiro)
    et.set_ruta_guardado(ruta_carpeta_retiro)

    ml.set_crear_archivo(True)
    mp.set_crear_archivo(True)
    et.set_crear_archivo(True)

    mercado_pago, valor_evaluar = mp.leer_archivo()
    mercado_libre = ml.leer_archivo()
    enterpirse = et.leer_archivo()
    procesamiento = ProcesamientoArchivos(df_mp=mercado_pago, df_ml=mercado_libre, df_et=enterpirse, valor_evaluar=valor_evaluar, ruta_guardado=ruta_carpeta_retiro, nombre_carpeta=nombre_carpeta_retiro)
    procesamiento.consolidado_ventas_pagos()

    # except ValidationError as e:
    #     print(e)
    # except Exception as e:
    #     print(e)
