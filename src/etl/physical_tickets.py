import os
import sys

import pandas as pd

route = os.path.abspath(__file__)
index_route = route.find("BackendHookedDocs")
local_path = route[:index_route + len("BackendHookedDocs")]
global_route = os.path.join(local_path, "src")

sys.path.append(global_route)

def extract(tickets_path):
    files_path = tickets_path + 'Registro Ventas 05 May. 2024  Resumen       DIARIO     SII  Christian Pozo.xlsx'

    data = pd.read_excel(files_path)

    return data

def transform(data):
    # Eliminar las filas con valores nulos del DF
    data.dropna(inplace=True)

    # Convertir todos los valores del DF en enteros
    data = data.apply(lambda x: x.astype(int) if pd.api.types.is_numeric_dtype(x) else x)

    # Convertir la columna 'fecha' al formato deseado 'yyyy-mm-dd hh-mm-ss'
    data['fecha'] = pd.to_datetime(data['fecha']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    return data

def load(data, str_conn):
    """
    Carga los datos procesados en una base de datos (actualmente solo muestra los datos).
    
    Parámetros:
    - data: El diccionario con los datos procesados de la factura.
    - str_conn: La cadena de conexión a la base de datos (actualmente no utilizada).
    """
    print(f"PLACEHOLDER: data cargada")

def main(pyshical_tickets_path):
    """
    Función principal que coordina las etapas de extracción, transformación y carga de datos.
    """
    str_conn = "string de conexión a la BD oracle"  # Placeholder para la cadena de conexión a la base de datos

    data = extract(pyshical_tickets_path)

    data_final = transform(data)

    load(data_final, str_conn)
