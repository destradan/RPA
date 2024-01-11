from app.classes.lectura_pandas import LecturaMercadoPago, LecturaMercadoLibre, LecturaEnterprise
from app.classes.procesamiento_archivos import ejecutar_procesamiento

from datetime import datetime

import pandas as pd
import shutil
import os

carpeta = 'C:/RPA/Input/2024 - 9 enero'
ml = 'Ventas_CO_Mercado_Libre_2024-01-09_06-53hs_662282086.xlsx'
mp = 'reserve-release-662282086-2024-01-09-082245.xlsx'
et = 'CARTERA MERCADO LIBRE 09 DE ENERO DE 2024.xls'


#mercado_libre = LecturaMercadoLibre(errores=[], crear_archivo=False, ruta=f'{carpeta}/{ml}', df=None)
#mercado_pago = LecturaMercadoPago(errores=[], fecha_fin='2023-12-27', crear_archivo=False, ruta=f'{carpeta}/{mp}', df=None, valor_evaluar=0.0)
enterprise = LecturaEnterprise(errores=[], crear_archivo=False,  ruta=f'{carpeta}/{et}', df=None)


#mercado_libre.leer_archivo()
#mercado_pago.leer_archivo()
enterprise.leer_archivo()

#ejecutar_procesamiento('2024-01-09', mercado_libre, mercado_pago, enterprise)

