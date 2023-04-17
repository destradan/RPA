from pydantic import BaseModel, ValidationError

from .lectura_pandas import LecturaMercadoLibre, LecturaMercadoPago, LecturaEnterprise
from app.settings import RUTA_RESULTADOS

import pandas as pd


class ProcesamientoArchivos(BaseModel):
    df_mp: pd.DataFrame
    df_ml: pd.DataFrame
    df_et: pd.DataFrame
    valor_evaluar: float


    class Config:
        arbitrary_types_allowed = True


    def consolidado_ventas_pagos(self):
        df_mp_reducido = self.df_mp[['DESCRIPTION','ORDER_ID', 'cobro_por_descuento', 'comision_por_venta', 'ica', 'fuente', 'iva']]

        lista_mp_no_payment = df_mp_reducido[~df_mp_reducido['DESCRIPTION'].isin(['payout', 'payment'])]['ORDER_ID'].unique().tolist()
        df_mp_no_payment = df_mp_reducido[(df_mp_reducido['ORDER_ID'].isin(lista_mp_no_payment)) & (df_mp_reducido['DESCRIPTION']=='payment')]

        df_mp_reducido = df_mp_reducido[df_mp_reducido['DESCRIPTION']=='payment']


        df_mp_reducido = df_mp_reducido.drop('DESCRIPTION', axis=1)
        df_mp_reducido = df_mp_reducido.groupby('ORDER_ID', as_index=False)[['cobro_por_descuento', 'comision_por_venta', 'ica', 'fuente', 'iva']].sum()

        df_concantenado = pd.merge(self.df_ml, df_mp_reducido, how='right', on='ORDER_ID')
        df_concantenado = df_concantenado[df_concantenado['ORDER_ID']!='']

        df_et_reducido = self.df_et[['ORDER_ID', 'fve', 'valor']]

        df_consolidado = pd.merge(df_concantenado, df_et_reducido, how='left', on='ORDER_ID')
        df_consolidado = df_consolidado.drop_duplicates(subset=['ORDER_ID'])

        ordenes_no_mp_en_ml = df_consolidado[(df_consolidado['CC']=='') | (df_consolidado['CC'].isnull())]['ORDER_ID'].unique().tolist()
        ordenes_no_et_en_ml = df_consolidado[(df_consolidado['fve']=='') | (df_consolidado['fve'].isnull())]['ORDER_ID'].unique().tolist()

        df_consolidado['comision_por_venta'] = df_consolidado['comision_por_venta']
        df_consolidado['ica'] = abs(df_consolidado['ica'])
        df_consolidado['fuente'] = abs(df_consolidado['fuente'])
        df_consolidado['iva'] = abs(df_consolidado['iva'])

        df_mp_no_payment = df_consolidado[df_consolidado['ORDER_ID'].isin(df_mp_no_payment['ORDER_ID'].to_list())]
        df_consolidado = df_consolidado[~df_consolidado['ORDER_ID'].isin(df_mp_no_payment['ORDER_ID'].to_list())]

        df_no_mp_en_ml = df_consolidado[df_consolidado['ORDER_ID'].isin(ordenes_no_mp_en_ml)]
        df_no_et_en_ml = df_consolidado[df_consolidado['ORDER_ID'].isin(ordenes_no_et_en_ml)]

        df_consolidado = df_consolidado[~df_mp_reducido['ORDER_ID'].isin(ordenes_no_mp_en_ml + ordenes_no_et_en_ml)]
        print("HEY")
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
        sum_row = pd.DataFrame({'Observaciones': ['TOTAL'], 'D': [df_resumen['D'].sum()], 'C': [df_resumen['C'].sum()]})
        df_resumen = pd.concat([df_resumen, sum_row], ignore_index=True)

        resultado = df_resumen.loc[5]['D'] - df_resumen.loc[5]['C']
        df_resumen['diferencia'] = [0, 0, 0, 0, 0, resultado]

        #print(df_resumen)
        # Creamos un objeto ExcelWriter utilizando xlsxwriter
        writer = pd.ExcelWriter(f'{RUTA_RESULTADOS}\\consolidado_MP_ML.xlsx', engine='xlsxwriter')
        df_consolidado.to_excel(writer, sheet_name='Consolidado')
        df_resumen.to_excel(writer, sheet_name='Resumen')
        df_mp_no_payment.to_excel(writer, sheet_name='No payment')
        df_no_mp_en_ml.to_excel(writer, sheet_name='No registro MP en ML')
        df_no_et_en_ml.to_excel(writer, sheet_name='No registro ET en ML')

        # Guardamos el archivo
        writer.close()

        return df_consolidado

def ejecutar_procesamiento():

    try:
        fecha_ini = '2023-01-31'
        fecha_fin = '2023-02-5'
        mercado_pago, valor_evaluar = LecturaMercadoPago(errores=[]).leer_archivo()
        mercado_libre = LecturaMercadoLibre(errores=[], fecha_inicio=fecha_ini, fecha_fin=fecha_fin).leer_archivo()
        enterpirse = LecturaEnterprise(errores=[]).leer_archivo()
        print("")
        procesamiento = ProcesamientoArchivos(df_mp=mercado_pago, df_ml=mercado_libre, df_et=enterpirse, valor_evaluar=valor_evaluar)
        procesamiento.consolidado_ventas_pagos()

    except ValidationError as e:
        print(e)
