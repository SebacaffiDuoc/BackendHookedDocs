import oracledb

# Configuración de la base de datos
DB_CONFIG = {
    "username": "HookedDeveloper",
    "password": "HookedDeveloperDuoc2024",
    "host": "192.168.1.90",       #"172.17.0.1",  # IP del host de Oracle en Docker
    "port": 1521,               # Puerto del contenedor
    "sid": "XEPDB1"             # SID de la base de datos
}

def get_connection():
    #Crear y devolver una conexión a la base de datos.
    dsn = f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['sid']}"
    connection = oracledb.connect(
        user=DB_CONFIG['username'],
        password=DB_CONFIG['password'],
        dsn=dsn
    )
    return connection

def close_connection(connection):
    #Cerrar la conexión a la base de datos.
    if connection:
        connection.close()
