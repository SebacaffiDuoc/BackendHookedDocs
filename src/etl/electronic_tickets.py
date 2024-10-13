import os
import sys

import pandas as pd

route = os.path.abspath(__file__)
index_route = route.find("BackendHookedDocs")
local_path = route[:index_route + len("BackendHookedDocs")]
global_route = os.path.join(local_path, "src")

sys.path.append(global_route)

def extract(tickets_path):
    files_path = tickets_path + 'reporte_99459570.xls'

    data = pd.read_excel(files_path)

    return data

def transform(data):

    data = data.drop(['impuestos','fecha_intercambio','estado_intercambio','informacion_intercambio','estado_reclamo_mercaderia','uri',
                      'referencias','indservicio','condicion_pago','tipofactesp','rutusuarioemisor','fecha_vencimiento',
                      'fecha_reclamo_mercaderia','estado_reclamo_contenido','fecha_reclamo_contenido','receptor','emisor','informacion_sii'], axis=1)
    
    return data

def load(data, str_conn):
    """
    Carga los datos procesados en una base de datos (actualmente solo muestra los datos)
    
    Parámetros:
    - data: El diccionario con los datos procesados de la factura.
    - str_conn: La cadena de conexión a la base de datos (actualmente no utilizada).
    """
    print(f"PLACEHOLDER: data cargada")

def main(electronic_tickets_path):
    """
    Función principal que coordina las etapas de extracción, transformación y carga de datos.
    """
    str_conn = "string de conexión a la BD oracle"  # Placeholder para la cadena de conexión a la base de datos

    data = extract(electronic_tickets_path)

    data_final = transform(data)

    load(data_final, str_conn)
