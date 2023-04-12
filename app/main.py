from app.settings import RUTA_RAIZ, RUTA_INSUMOS, ARCHIVO_MERCADO_LIBRE, ARCHIVO_MERCADO_PAGO

from app.classes.procesamiento_archivos import ejecutar_procesamiento

import glob
import pandas as pd

ruta_archivo_ML = glob.glob(f'{RUTA_INSUMOS}\\{ARCHIVO_MERCADO_LIBRE}*.xlsx')
ruta_archivo_MP = glob.glob(f'{RUTA_INSUMOS}\\{ARCHIVO_MERCADO_PAGO}*.xlsx')

print(f'{RUTA_RAIZ}')
print(RUTA_INSUMOS)
if len(ruta_archivo_ML) > 1:
    raise ValueError("Se encontraron múltiples que coincide con el nombre del archivo 'Ventas_CO_Mercado_Libre'. Por favor verifique y asegúrese de que solo haya un archivo 'Ventas_CO_Mercado_Libre' en la carpeta 'insumos'")

if len(ruta_archivo_ML) == 0:
    raise ValueError('No se encontro el archivo de ventas de Mercado Libre. Por favor verifique que el archivo este o que su nombre empiece por "Ventas_CO_Mercado_Libre".')

if len(ruta_archivo_MP) > 1:
    raise ValueError("Se encontraron múltiples archivos que coinciden con el nombre 'reserve-release' generado en Mercado Pago. Asegúrese de que solo haya un archivo 'reserve-release' en la carpeta 'insumos'")

if len(ruta_archivo_MP) == 0:
    raise ValueError("No se encontró el archivo generado por Mercado Pago. Por favor verifique que el archivo 'reserve-release' esté en la carpeta 'insumos' y que el nombre del archivo comience con 'reserve-release'")


print(ruta_archivo_ML)
print(ruta_archivo_MP)

ejecutar_procesamiento()