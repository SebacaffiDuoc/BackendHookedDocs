import json
from .database import get_connection, close_connection

# Create
def create_invoice(data,table_name):
    """Insertar una nueva factura en la tabla invoices."""
    connection = get_connection()
    cursor = connection.cursor()
    
    # Convertir el diccionario de Python a JSON
    invoice_json = json.dumps(data)
    
    # Consulta de inserción
    insert_query = f"""
        INSERT INTO {table_name} (invoice_data)
        VALUES (:invoice_data)
    """
    
    # Ejecutar el insert
    cursor.execute(insert_query, invoice_data=invoice_json)
    
    # Confirmar los cambios
    connection.commit()
    
    # Cerrar cursor y conexión
    cursor.close()
    close_connection(connection)

# Read all data
def read_invoices(table_name):
    """Leer todas las facturas desde la tabla invoices."""
    connection = get_connection()
    cursor = connection.cursor()
    
    # Consulta de selección
    select_query = f"SELECT id, invoice_data FROM {table_name}"
    
    # Ejecutar la consulta
    cursor.execute(select_query)
    rows = cursor.fetchall()
    
    # Procesar los resultados
    invoices = [{"id": row[0], "data": row[1]} for row in rows]
    
    # Cerrar cursor y conexión
    cursor.close()
    close_connection(connection)
    
    return invoices

# Read invoice_number data
def read_select_invoice(table_name, invoice_number):
    """Leer todas las facturas desde la tabla invoices."""
    connection = get_connection()
    cursor = connection.cursor()
    
    # Consulta de selección
    select_query = f"SELECT * FROM {table_name}where json_value(invoice_data, '$.issuer.invoice_number') = {invoice_number}"
    
    # Ejecutar la consulta
    cursor.execute(select_query)
    rows = cursor.fetchall()
    
    # Procesar los resultados
    invoices = [{"id": row[0], "data": row[1]} for row in rows]
    
    # Cerrar cursor y conexión
    cursor.close()
    close_connection(connection)
    
    return invoices

# Update
def update_invoice(invoice_number, new_data, table_name):
    """Actualizar una factura existente en la tabla invoices."""
    connection = get_connection()
    cursor = connection.cursor()
    
    # Convertir el nuevo diccionario de Python a JSON
    new_invoice_json = json.dumps(new_data)

    if table_name.upper == 'INVOICES_ISSUED':
        json_value = "json_value(invoice_data, '$.issuer.invoice_number')"
    else:
        json_value = "json_value(invoice_data, '$.invoice_number')"
        
    
    # Consulta de actualización
    update_query = f"""
        UPDATE {table_name} 
        SET INVOICE_DATA = :new_invoice_data
        WHERE {json_value} = :invoice_number
    """
    
    # Ejecutar la actualización
    cursor.execute(update_query, new_invoice_data=new_invoice_json, invoice_id=invoice_number)
    
    # Confirmar los cambios
    connection.commit()
    
    # Cerrar cursor y conexión
    cursor.close()
    close_connection(connection)

# Update para columnas subtotal, tax, y total, parametros: numero de factura, nuevo subtotal, nuevo tax, nuevo total, tabla a modificar
def update_selected_invoice(invoice_number, new_subtotal, new_tax, new_total, table_name):
    """Actualizar campos específicos de una factura existente en la tabla especificada."""
    connection = get_connection()
    cursor = connection.cursor()
    
    if table_name.upper() == 'INVOICES_ISSUED':
        invoice_number_json_path = '$.issuer.invoice_number'
    else:
        invoice_number_json_path = '$.invoice_number'
        
    # Consulta de actualización utilizando JSON_TRANSFORM
    update_query = f"""
        UPDATE {table_name}
        SET invoice_data = JSON_TRANSFORM(invoice_data,
            SET '$.subtotal' = :new_subtotal,
            SET '$.tax' = :new_tax,
            SET '$.total' = :new_total
        )
        WHERE JSON_VALUE(invoice_data, '{invoice_number_json_path}') = :invoice_number
    """
    
    # Ejecutar la actualización
    cursor.execute(update_query, new_subtotal=new_subtotal, new_tax=new_tax, new_total=new_total, invoice_number=invoice_number)
    
    # Confirmar los cambios
    connection.commit()
    
    # Cerrar cursor y conexión
    cursor.close()
    close_connection(connection)


# Delete
def delete_invoice(invoice_id,table_name):
    """Eliminar una factura de la tabla invoices."""
    connection = get_connection()
    cursor = connection.cursor()
    
    # Consulta de eliminación
    delete_query = f"""
        DELETE FROM {table_name} WHERE id = :invoice_id
    """
    
    # Ejecutar la eliminación
    cursor.execute(delete_query, invoice_id=invoice_id)
    
    # Confirmar los cambios
    connection.commit()
    
    # Cerrar cursor y conexión
    cursor.close()
    close_connection(connection)
