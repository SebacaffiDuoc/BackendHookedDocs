import oracledb

# No llamamos a init_oracle_client() para usar el modo thin

# Configuración de la conexión
username = "HookedDeveloper"
password = "HookedDeveloperDuoc2024"
host = "172.17.0.1"  # IP del host de Oracle en Docker
port = 1521            # Puerto del contenedor
sid = "XEPDB1"         # SID de la base de datos

# Crear la conexión usando el modo "thin"
dsn = f"{host}:{port}/{sid}"
connection = oracledb.connect(user=username, password=password, dsn=dsn)

# Probar la conexión
cursor = connection.cursor()
cursor.execute("SELECT 'Conexión Exitosa', invoice_data FROM invoices_issued")
for row in cursor:
    print(row)

cursor.close()
connection.close()
