import json
import os

RUTA_RAIZ = os.path.dirname(os.path.abspath(__file__))
RUTA_INSUMOS = os.path.join(RUTA_RAIZ, 'insumos')
RUTA_RESULTADOS = os.path.join(RUTA_RAIZ, 'resultados')

with open(os.path.join(RUTA_RAIZ, 'secrets.json'), 'r') as f:
    variables_ambiente = json.load(f)

ARCHIVO_MERCADO_LIBRE = variables_ambiente['ARCHIVO_MERCADO_LIBRE']
ARCHIVO_MERCADO_PAGO = variables_ambiente['ARCHIVO_MERCADO_PAGO']
ARCHIVO_ENTERPRISE = variables_ambiente['ARCHIVO_ENTERPRISE']
