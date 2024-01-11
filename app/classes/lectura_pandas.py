from abc import abstractmethod
from pydantic import BaseModel, ValidationError, validator, root_validator
from typing import Optional, Union

from app.settings import RUTA_INSUMOS, ARCHIVO_MERCADO_LIBRE, ARCHIVO_MERCADO_PAGO, ARCHIVO_ENTERPRISE, RUTA_RESULTADOS

import numpy as np
import pandas as pd
import json
import os

import logging

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

def convertir_fecha(fecha_original):

    from datetime import datetime
    import locale
    locale.setlocale(locale.LC_TIME, 'es_ES.utf8')

    if not fecha_original is None and fecha_original != '' and not pd.isna(fecha_original):
        if 'hs.' in fecha_original:
            fecha_formateada = datetime.strptime(fecha_original, '%d de %B de %Y %H:%M hs.')
        else:
            fecha_formateada = datetime.strptime(fecha_original, '%d de %B de %Y')
        return fecha_formateada
    return ''

class LecturaArchivos(BaseModel):
    ruta: Optional[str]
    errores: list[str] = []
    crear_archivo: bool = True
    df: Optional[pd.DataFrame]
    nombre_guardado:str = ''
    ruta_guardado: str = f'{RUTA_RESULTADOS}'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.ruta:
            self.archivo_correcto()




    class Config:
        arbitrary_types_allowed = True



    def leer_archivo(self) -> pd.DataFrame:
        return pd.read_excel(self.ruta)

    def set_ruta_guardado(self, nueva_ruta: str):
        self.ruta_guardado = nueva_ruta

    def set_crear_archivo(self, crear_archivo: bool):
        self.crear_archivo = crear_archivo

    def encontrar_inicio_columna(self, ruta_archivo: str, nombre_columna: str):
        nombre_columna = nombre_columna.lower()  # Convertir el nombre de la columna buscada a minúsculas

        for fila in range(0, 10):  # Asumimos que la columna está en las primeras 10 filas
            try:
                df_temp = pd.read_excel(ruta_archivo, header=fila)
                # Convertir los nombres de las columnas en el DataFrame a minúsculas antes de la comparación
                if nombre_columna in [col.lower() for col in df_temp.columns]:
                    return fila
            except Exception as e:
                print(f"Error en la fila {fila}: {e}")
                continue
        return None

    @abstractmethod
    def archivo_correcto(self):
        raise NotImplementedError("la funcion archivo_correcto no se ha implementado")



class LecturaMercadoLibre(LecturaArchivos):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.nombre_guardado = 'ML_configurado.xlsx'


    def archivo_correcto(self) -> Union[str, ValueError]:
        archivos_encontrados = [archivo for archivo in os.listdir(RUTA_INSUMOS) if archivo.startswith(ARCHIVO_MERCADO_LIBRE)]

        if len(archivos_encontrados) == 0:
            raise ValueError("No hay archivos que hace referencia al archivo de ventas de Mercado Libre")
        elif len(archivos_encontrados) > 1:
            raise ValueError("Hay varios archivos que hacen referencia a ventas de Mercado Libre. Debe haber solo un archvio de ventas mercado libre.")

        self.ruta = f'{RUTA_INSUMOS}\\{archivos_encontrados[0]}'

    def leer_archivo(self, *args, **kwargs) -> pd.DataFrame:

        fila_inicio = self.encontrar_inicio_columna(self.ruta, '# de venta')
        if fila_inicio is not None:

            self.df = pd.read_excel(self.ruta,  dtype={'# de venta':str}, skiprows=fila_inicio)
            logging.info('')

            logging.info(self.df.to_string())

            self.df.columns = [col.lower() for col in self.df.columns]

            self.df.rename(columns={'# de venta': 'order_id', 'fecha de venta':'fecha_venta'}, inplace=True)

            self.df['order_id'] = self.df['order_id'].str.strip()
            self.df['order_id'] = self.df['order_id'].fillna('')
            self.df = self.df[self.df['order_id']!='']

            #self.df['fecha_venta'] = self.df['fecha_venta'].astype('string')
            #self.df['fecha_venta'] = self.df['fecha_venta'].fillna('')
            #self.df['fecha_venta'] = self.df['fecha_venta'].str.strip()
            #self.df['fecha_venta'] = self.df['fecha_venta'].str.replace('0', '')

            #self.df['fecha_venta'] = self.df['fecha_venta'].apply(convertir_fecha)

            #self.df = self.df[(self.df['fecha_venta']>=self.fecha_inicio) & (self.df['fecha_venta']<=self.fecha_fin)]

            if self.crear_archivo:
                self.df.to_excel(f'{self.ruta_guardado}\\{self.nombre_guardado}')
            return self.df
        else:
            print("No se encontró la columna especificada.")
            return None

class LecturaMercadoPago(LecturaArchivos):
    fecha_fin: str
    valor_evaluar: Optional[float]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.nombre_guardado = 'MP_configurado.xlsx'
        self.validar_fecha_fin()


    def validar_fecha_fin(self) -> Union[str, ValueError]:
        try:
            self.fecha_fin = pd.to_datetime(f'{self.fecha_fin}T23:59:59', format='%Y-%m-%dT%H:%M:%S')
        except:
            raise ValueError("La fecha de finalización no tiene el formato correcto. Debe ser YYYY-mm-dd")

    def archivo_correcto(self) -> Union[str, ValueError]:
        archivos_encontrados = [archivo for archivo in os.listdir(RUTA_INSUMOS) if archivo.startswith(ARCHIVO_MERCADO_PAGO)]
        if len(archivos_encontrados) == 0:
            raise ValueError("No hay archivos que hace referencia al archivo de ventas de Mercado Pago")
        elif len(archivos_encontrados) > 1:
            raise ValueError("Hay varios archivos que hacen referencia a ventas de Mercado Pago. Debe haber solo un archvio de ventas mercado libre.")

        self.ruta = f'{RUTA_INSUMOS}\\{archivos_encontrados[0]}'


    def obtener_impuestos_segregados(self, tax_type):
        return self.df['taxes_disaggregated'].apply(lambda x: sum([d['amount'] for d in x if 'financial_entity' in d.keys() and d['financial_entity'] == tax_type]))

    def leer_archivo(self) -> tuple[pd.DataFrame, float]:
        self.df = pd.read_excel(self.ruta, dtype={'ORDER_ID':str})

        self.df.columns = [col.lower() for col in self.df.columns]

        self.df['order_id'] = self.df['order_id'].str.strip()
        self.df['order_id'] = self.df['order_id'].fillna('')

        #logging.info(f'Fecha fin: {self.fecha_fin}')

        df_copia = self.df.copy()
        df_copia = df_copia[(df_copia['order_id']=='') & (df_copia['net_debit_amount']!=0.0 )][['source_id', 'net_debit_amount']]


        merged_df = df_copia.merge(self.df, left_on='net_debit_amount', right_on='net_credit_amount', how='inner')
        merged_df = merged_df[['order_id','source_id_x', 'source_id_y', 'net_debit_amount_x', 'net_credit_amount']]
        merged_df.rename(columns={'net_debit_amount_x': 'net_debit_amount'}, inplace=True)

        df_con_ordenes_alertas = merged_df.groupby('source_id_x')['order_id'].agg(lambda x: ','.join(x)).reset_index()
        df_con_ordenes_alertas = df_con_ordenes_alertas.rename(columns={'source_id_x': 'source_id', 'order_id': 'opciones_alertas'})

        self.df = self.df.merge(df_con_ordenes_alertas, left_on='source_id', right_on='source_id', how='left')

        self.df["release_date"]=self.df["release_date"].astype('string')
        self.df['release_date'] = pd.to_datetime(self.df['release_date'], format='%Y-%m-%dT%H:%M:%S.%f%z').dt.tz_localize(None)

        self.df = self.df[(self.df['release_date']<=self.fecha_fin)]

        self.df.rename(columns={'coupon_amount': 'cobro_por_descuento', 'mp_fee_amount':'comision_por_venta'}, inplace=True)
        self.df["description"] = self.df["description"].astype('string')

        self.df['comision_por_venta'] = abs(self.df['comision_por_venta'])

        pagos_en_rango = self.df.loc[self.df['description'] == 'payout']

        ultimo_indice = pagos_en_rango.index.max()
        indice_anterior = pagos_en_rango.index[-2] if len(pagos_en_rango) >= 2 else None

        df_rango = self.df.loc[indice_anterior:ultimo_indice]
        self.valor_evaluar = df_rango.loc[ultimo_indice]['net_debit_amount']

        self.df['taxes_disaggregated'] = self.df['taxes_disaggregated'].fillna('[]')
        #self.df['taxes_disaggregated'] = self.df['taxes_disaggregated'].apply(lambda x: json.loads(x))
        self.df['taxes_disaggregated'] = self.df['taxes_disaggregated'].apply(safe_json_loads)

        self.df['ica'] = self.obtener_impuestos_segregados('ica')
        self.df['fuente'] = self.obtener_impuestos_segregados('fuente')
        self.df['iva'] = self.obtener_impuestos_segregados('iva')

        self.df = self.df[indice_anterior:ultimo_indice]
        if self.crear_archivo:
            self.df.to_excel(f'{self.ruta_guardado}\\{self.nombre_guardado}')

        return self.df, self.valor_evaluar



class LecturaEnterprise(LecturaArchivos):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.nombre_guardado = 'enterprise.xlsx'



    def archivo_correcto(self) -> Union[str, ValueError]:
        archivos_encontrados = [archivo for archivo in os.listdir(RUTA_INSUMOS) if archivo.startswith(ARCHIVO_ENTERPRISE)]
        if len(archivos_encontrados) == 0:
            raise ValueError("No hay archivos que hace referencia al archivo de ventas de Mercado Pago")
        elif len(archivos_encontrados) > 1:
            raise ValueError("Hay varios archivos que hacen referencia a ventas de Mercado Pago. Debe haber solo un archvio de ventas mercado libre.")

        self.ruta = f'{RUTA_INSUMOS}\\{archivos_encontrados[0]}'

    def leer_archivo(self, *args, **kwargs) -> pd.DataFrame:
        
        self.df = pd.read_excel(self.ruta, dtype={'Nmero O.C. comercial':str})
        print(self.df['Nmero O.C. comercial'].to_string())

        self.df['Nmero O.C. comercial'] = self.df['Nmero O.C. comercial'].str.replace(r'[^\d]', '', regex=True)


        print(' -------------------------------------------------------- ')
        print(self.df['Nmero O.C. comercial'].to_string())


        self.df.columns = [col.lower() for col in self.df.columns]

        self.df = self.df.apply(lambda row: row.apply(to_lower), axis=1)

        self.df.rename(columns={'nmero o.c. comercial': 'order_id', 'docto. causacin':'fve', 'total cop':'valor'}, inplace=True)
        self.df['order_id'] = '200000' + self.df['order_id']
        self.df['order_id'] = self.df['order_id'].str.strip()

        self.df['order_id'] = self.df['order_id'].fillna('')
        self.df = self.df[self.df['order_id']!='']

        if self.crear_archivo:
            self.df.to_excel(f'{self.ruta_guardado}\\{self.nombre_guardado}')

        return self.df
    

def safe_json_loads(x):
    try:
        # Eliminar comillas dobles externas si están presentes
        if x.startswith("\"") and x.endswith("\""):
            x = x[1:-1]
        return json.loads(x)
    except json.JSONDecodeError as e:
        print(f"Error al cargar JSON: {e} - en el dato: {x}")
        return None
    
def to_lower(x):
    return x.lower() if isinstance(x, str) else x