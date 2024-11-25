import os
import sys
import shutil
import pandas as pd
from src.core.crud import *

# Configuración de rutas para agregar el directorio src al path de Python
route = os.path.abspath(__file__)
index_route = route.find("BackendHookedDocs")
local_path = route[:index_route + len("BackendHookedDocs")]
global_route = os.path.join(local_path, "src")

sys.path.append(global_route)

def extract(tickets_path):
    """
    Extrae los datos de cada archivo Excel en la carpeta especificada.
    
    Parámetros:
    - tickets_path: Ruta de la carpeta que contiene los archivos de Excel.
    
    Retorna:
    - Una lista de tuplas (dataframe, archivo) con los datos extraídos y el nombre del archivo.
    """
    extracted_data = []

    for file in os.listdir(tickets_path):
        if file.endswith(".xls") or file.endswith(".xlsx"):
            file_path = os.path.join(tickets_path, file)
            try:
                # Leer archivo Excel
                data = pd.read_excel(file_path)
                extracted_data.append((data, file_path))
            except Exception as e:
                print(f"Error al leer el archivo {file_path}: {e}")

    return extracted_data

def transform(data):
    """
    Transforma el DataFrame, eliminando las columnas innecesarias.
    
    Parámetros:
    - data: DataFrame con los datos extraídos.

    Retorna:
    - DataFrame transformado con los datos necesarios.
    """
    tarjetas_aceptadas = ['VISA', 'MASTERCARD', 'AMEX', 'AMERICAN EXPRESS', 'DISCOVER']

    data = data[data['TARJETA'].isin(tarjetas_aceptadas)]

    data = data.drop(['impuestos', 'fecha_intercambio', 'estado_intercambio', 'informacion_intercambio', 
                      'estado_reclamo_mercaderia', 'uri', 'referencias', 'indservicio', 'condicion_pago', 
                      'tipofactesp', 'rutusuarioemisor', 'fecha_vencimiento', 'fecha_reclamo_mercaderia', 
                      'estado_reclamo_contenido', 'fecha_reclamo_contenido', 'receptor', 'emisor', 
                      'informacion_sii'], axis=1, errors='ignore')
    
    data['publicacion'] = pd.to_datetime(data['publicacion']).dt.strftime('%Y%m%d')
    data['emision'] = pd.to_datetime(data['emision']).dt.strftime('%Y%m%d')
    data['fecha_sii'] = pd.to_datetime(data['fecha_sii']).dt.strftime('%Y%m%d')
    
    return data

def load(data):
    """
    Carga los datos procesados en una base de datos (actualmente solo muestra los datos).
    
    Parámetros:
    - data: El DataFrame con los datos procesados de la factura.
    """
    create_electronic_tickets(data)
    print(data.head())

def move_to_processed(file_path, base_path):
    """
    Mueve el archivo procesado a una carpeta llamada "PROCESADOS".
    
    Parámetros:
    - file_path: Ruta del archivo a mover.
    - base_path: Ruta base donde se encuentra la carpeta "PROCESADOS".
    """
    processed_folder = os.path.join(base_path, "PROCESADOS")

    if not os.path.exists(processed_folder):
        os.makedirs(processed_folder)

    shutil.move(file_path, processed_folder)

def main(electronic_tickets_path):
    """
    Función principal que coordina las etapas de extracción, transformación y carga de datos.
    """
    # Etapa de extracción: leer todos los archivos Excel de la carpeta
    extracted_data_list = extract(electronic_tickets_path)
    processed_count = 0  # Inicializa el contador

    for data, file_path in extracted_data_list:
        # Etapa de transformación: normaliza el DataFrame
        data_final = transform(data)

        # Etapa de carga: inserta o muestra los datos en la base de datos
        load(data_final)

        # Mover el archivo a la carpeta "PROCESADOS" después de procesarlo
        move_to_processed(file_path, electronic_tickets_path)
        processed_count += 1  # Incrementa el contador por cada archivo movido

    return processed_count
    