from pydantic import BaseModel, ValidationError, validator, root_validator
from typing import Optional, Union

from app.settings import RUTA_INSUMOS, ARCHIVO_MERCADO_LIBRE, ARCHIVO_MERCADO_PAGO, ARCHIVO_ENTERPRISE, RUTA_RESULTADOS

import numpy as np
import pandas as pd
import json
import os


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
    df: Optional[pd.DataFrame]


    class Config:
        arbitrary_types_allowed = True



    def leer_archivo(self) -> pd.DataFrame:
        return pd.read_excel(self.ruta)


class LecturaMercadoLibre(LecturaArchivos):

    fecha_inicio: str
    fecha_fin: str

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.archivo_correcto()
        self.validar_fecha_inicio()
        self.validar_fecha_fin()

    def archivo_correcto(self) -> Union[str, ValueError]:
        archivos_encontrados = [archivo for archivo in os.listdir(RUTA_INSUMOS) if archivo.startswith(ARCHIVO_MERCADO_LIBRE)]

        if len(archivos_encontrados) == 0:
            raise ValueError("No hay archivos que hace referencia al archivo de ventas de Mercado Libre")
        elif len(archivos_encontrados) > 1:
            raise ValueError("Hay varios archivos que hacen referencia a ventas de Mercado Libre. Debe haber solo un archvio de ventas mercado libre.")

        self.ruta = f'{RUTA_INSUMOS}\\{archivos_encontrados[0]}'



    def validar_fecha_inicio(self) -> Union[str, ValueError]:
        try:
            self.fecha_inicio = pd.to_datetime(self.fecha_inicio, format='%Y-%m-%d')
        except ValueError:
            raise ValueError("La fecha de inicio no tiene el formato correcto. Debe ser YYYY-mm-dd")

    def validar_fecha_fin(self) -> Union[str, ValueError]:
        try:
            self.fecha_fin = pd.to_datetime(self.fecha_fin, format='%Y-%m-%d')
        except:
            raise ValueError("La fecha de finalización no tiene el formato correcto. Debe ser YYYY-mm-dd")

    def leer_archivo(self, *args, **kwargs) -> pd.DataFrame:
        self.df = pd.read_excel(self.ruta,  dtype={'# de venta':str}, skiprows=2)
        self.df.rename(columns={'# de venta': 'ORDER_ID', 'Fecha de venta':'fecha_venta'}, inplace=True)
        self.df['ORDER_ID'] = self.df['ORDER_ID'].str.strip()
        self.df['ORDER_ID'] = self.df['ORDER_ID'].fillna('')
        self.df = self.df[self.df['ORDER_ID']!='']
        #self.df['fecha_venta'] = self.df['fecha_venta'].astype('string')
        #self.df['fecha_venta'] = self.df['fecha_venta'].fillna('')
        #self.df['fecha_venta'] = self.df['fecha_venta'].str.strip()
        #self.df['fecha_venta'] = self.df['fecha_venta'].str.replace('0', '')

        #self.df['fecha_venta'] = self.df['fecha_venta'].apply(convertir_fecha)

        #self.df = self.df[(self.df['fecha_venta']>=self.fecha_inicio) & (self.df['fecha_venta']<=self.fecha_fin)]

        self.df.to_excel(f'{RUTA_RESULTADOS}\\ML_configurado.xlsx')
        return self.df

class LecturaMercadoPago(LecturaArchivos):

    valor_evaluar: Optional[float]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.archivo_correcto()

    def archivo_correcto(self) -> Union[str, ValueError]:
        archivos_encontrados = [archivo for archivo in os.listdir(RUTA_INSUMOS) if archivo.startswith(ARCHIVO_MERCADO_PAGO)]
        if len(archivos_encontrados) == 0:
            raise ValueError("No hay archivos que hace referencia al archivo de ventas de Mercado Pago")
        elif len(archivos_encontrados) > 1:
            raise ValueError("Hay varios archivos que hacen referencia a ventas de Mercado Pago. Debe haber solo un archvio de ventas mercado libre.")

        self.ruta = f'{RUTA_INSUMOS}\\{archivos_encontrados[0]}'


    def obtener_impuestos_segregados(self, tax_type):
        return self.df['TAXES_DISAGGREGATED'].apply(lambda x: sum([d['amount'] for d in x if 'financial_entity' in d.keys() and d['financial_entity'] == tax_type]))

    def leer_archivo(self) -> tuple[pd.DataFrame, float]:
        self.df = pd.read_excel(self.ruta, dtype={'ORDER_ID':str})
        self.df['ORDER_ID'] = self.df['ORDER_ID'].str.strip()
        self.df['ORDER_ID'] = self.df['ORDER_ID'].fillna('')
        #self.df = self.df[self.df['ORDER_ID']!='']

        self.df.rename(columns={'COUPON_AMOUNT': 'cobro_por_descuento', 'MP_FEE_AMOUNT':'comision_por_venta'}, inplace=True)
        self.df["DESCRIPTION"] = self.df["DESCRIPTION"].astype('string')
        #self.df = self.df[self.df["DESCRIPTION"]!='refund']

        self.df['comision_por_venta'] = abs(self.df['comision_por_venta'])

        self.df = self.df[:-1]

        pagos_en_rango = self.df.loc[self.df['DESCRIPTION'] == 'payout']
        ultimo_indice = pagos_en_rango.index.max()
        indice_anterior = pagos_en_rango.index[-2] if len(pagos_en_rango) >= 2 else None

        df_rango = self.df.loc[indice_anterior:ultimo_indice]
        self.valor_evaluar = df_rango.loc[ultimo_indice]['NET_DEBIT_AMOUNT']

        listado_ordenes = df_rango['ORDER_ID'].unique().tolist()
        self.df = self.df[self.df['ORDER_ID'].isin(listado_ordenes)]
        #self.df = self.df[self.df["DESCRIPTION"]!='refund']
        #self.df = self.df[self.df["DESCRIPTION"]!='reserve_for_refund']
        #self.df = self.df[self.df["DESCRIPTION"]!='shipping_cancel']
        #self.df = self.df[self.df["DESCRIPTION"]!='reserve_for_bpp_shipping_return']
        #self.df = self.df[self.df["DESCRIPTION"]!='payout']
        #self.df = self.df[self.df["DESCRIPTION"]!='mediation']
        #self.df = self.df[self.df["DESCRIPTION"]!='reserve_for_dispute']


        print("#########################: ", self.valor_evaluar)
        print(ultimo_indice)
        print(indice_anterior)


        self.df['TAXES_DISAGGREGATED'] = self.df['TAXES_DISAGGREGATED'].fillna('[]')
        self.df['TAXES_DISAGGREGATED'] = self.df['TAXES_DISAGGREGATED'].apply(lambda x: json.loads(x))

        self.df['ica'] = self.obtener_impuestos_segregados('ica')
        self.df['fuente'] = self.obtener_impuestos_segregados('fuente')
        self.df['iva'] = self.obtener_impuestos_segregados('iva')

        self.df['total_impuestos'] = self.df['ica'] + self.df['fuente'] + self.df['iva']

        self.df['diferencias'] = np.round(abs(self.df['total_impuestos'] - self.df['TAXES_AMOUNT']), decimals=2)

        self.df['incongruente'] = ((self.df['TAXES_AMOUNT']>0.0) & (~self.df['DESCRIPTION'].str.contains('refund')) | (self.df['diferencias']!=0.0))
        self.df = self.df[(~pd.isna(self.df['ORDER_ID'])) & (self.df['ORDER_ID']!='')]
        self.df.to_excel(f'{RUTA_RESULTADOS}\\MP_configurado.xlsx')
        return self.df, self.valor_evaluar



class LecturaEnterprise(LecturaArchivos):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.archivo_correcto()

    def archivo_correcto(self) -> Union[str, ValueError]:
        archivos_encontrados = [archivo for archivo in os.listdir(RUTA_INSUMOS) if archivo.startswith(ARCHIVO_ENTERPRISE)]
        if len(archivos_encontrados) == 0:
            raise ValueError("No hay archivos que hace referencia al archivo de ventas de Mercado Pago")
        elif len(archivos_encontrados) > 1:
            raise ValueError("Hay varios archivos que hacen referencia a ventas de Mercado Pago. Debe haber solo un archvio de ventas mercado libre.")

        self.ruta = f'{RUTA_INSUMOS}\\{archivos_encontrados[0]}'

    def leer_archivo(self, *args, **kwargs) -> pd.DataFrame:
        self.df = pd.read_excel(self.ruta, dtype={'Nmero O.C. comercial':str, 'ORDER_ID':str})
        self.df.rename(columns={'Nmero O.C. comercial': 'ORDER_ID', 'Docto. causacin':'fve', 'Total COP':'valor'}, inplace=True)
        self.df['ORDER_ID'] = '200000' + self.df['ORDER_ID']
        self.df['ORDER_ID'] = self.df['ORDER_ID'].str.strip()
        self.df['ORDER_ID'] = self.df['ORDER_ID'].fillna('')
        self.df = self.df[self.df['ORDER_ID']!='']

        self.df.to_excel(f'{RUTA_RESULTADOS}\\enterprise.xlsx')

        return self.df