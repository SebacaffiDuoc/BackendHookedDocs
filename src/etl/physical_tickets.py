import os
import sys
import shutil
import pandas as pd

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
    Transforma el DataFrame, eliminando las filas con valores nulos, convirtiendo los valores a enteros y formateando la columna de fecha.
    
    Parámetros:
    - data: DataFrame con los datos extraídos.

    Retorna:
    - DataFrame transformado con los datos necesarios.
    """
    # Eliminar las filas con valores nulos del DF
    data.dropna(inplace=True)

    # Convertir todos los valores del DF en enteros
    data = data.apply(lambda x: x.astype(int) if pd.api.types.is_numeric_dtype(x) else x)

    # Convertir la columna 'fecha' al formato deseado 'yyyy-mm-dd hh-mm-ss'
    if 'fecha' in data.columns:
        data['fecha'] = pd.to_datetime(data['fecha']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    return data

def load(data, str_conn):
    """
    Carga los datos procesados en una base de datos (actualmente solo muestra los datos).
    
    Parámetros:
    - data: El DataFrame con los datos procesados de la factura.
    - str_conn: La cadena de conexión a la base de datos (actualmente no utilizada).
    """
    print(f"PLACEHOLDER: data cargada")

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

def main(physical_tickets_path):
    """
    Función principal que coordina las etapas de extracción, transformación y carga de datos.
    """
    str_conn = "string de conexión a la BD oracle"  # Placeholder para la cadena de conexión a la base de datos

    # Etapa de extracción: leer todos los archivos Excel de la carpeta
    extracted_data_list = extract(physical_tickets_path)

    for data, file_path in extracted_data_list:
        # Etapa de transformación: normaliza el DataFrame
        data_final = transform(data)

        # Etapa de carga: inserta o muestra los datos en la base de datos
        load(data_final, str_conn)

        # Mover el archivo a la carpeta "PROCESADOS" después de procesarlo
        move_to_processed(file_path, physical_tickets_path)