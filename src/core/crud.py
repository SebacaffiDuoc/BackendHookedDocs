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

    #ejecuta auditoria
    if table_name == 'invoices_issued' :
        cursor.callproc('pkg_issued.main')
    else:
        cursor.callproc('pkg_received.main')
    
    
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

def read_select_invoice(number, functionalitie):
    """Leer todas las facturas desde la tabla invoices."""
    connection = get_connection()
    cursor = connection.cursor()

    if functionalitie == 1:
        # Consulta de selección para facturas recibidas
        select_query = """SELECT  
                            INVOICE_NUMBER, ISSUE_DATE, SUBTOTAL, 
                            TAX, TOTAL, PAY_METHOD, ISSUER_NAME, ISSUER_ADDRESS
                          FROM flat_invoices_received t1
                          JOIN flat_invoices_received_items t2 ON (t1.INVOICE_NUMBER = t2.INVOICE_NUMBER_FK)
                          WHERE t1.invoice_number = %s"""
    elif functionalitie == 2:
        # Consulta de selección para facturas emitidas
        select_query = """SELECT 
                            INVOICE_NUMBER, ISSUE_DATE, SUBTOTAL, 
                            TAX, TOTAL, PAY_METHOD, ISSUER_NAME, ISSUER_ADDRESS
                          FROM flat_invoices_issued t1
                          JOIN flat_invoices_issued_items t2 ON (t1.INVOICE_NUMBER = t2.INVOICE_NUMBER_FK)
                          WHERE t1.invoice_number = %s"""
    elif functionalitie == 3:
        # Consulta de selección para boletas electrónicas
        select_query = """SELECT 
                            TIPO_DOCUMENTO, FOLIO, EMISION, MONTO_NETO, 
                            MONTO_EXENTO, MONTO_IVA, MONTO_TOTAL
                          FROM electronic_tickets
                          WHERE folio = %s"""
    elif functionalitie == 4:
        # Consulta de selección para boletas físicas
        select_query = """SELECT 
                            FOLIO, NETO, IVA, TOTAL, 
                            FECHA, RUT_VENDEDOR, SUCURSAL
                          FROM physical_tickets
                          WHERE folio = %s"""
    else:
        # Manejo de funcionalidad no reconocida
        cursor.close()
        close_connection(connection)
        return []

    # Ejecutar la consulta con parámetros para evitar inyección SQL
    cursor.execute(select_query, (number,))
    rows = cursor.fetchall()

    # Procesar los resultados según la funcionalidad
    invoices = []
    if functionalitie in [1, 2]:
        for row in rows:
            invoice = {
                "INVOICE_NUMBER": row[0],
                "ISSUE_DATE": row[1],
                "SUBTOTAL": row[2],
                "TAX": row[3],
                "TOTAL": row[4],
                "PAY_METHOD": row[5],
                "ISSUER_NAME": row[6],
                "ISSUER_ADDRESS": row[7]
            }
            invoices.append(invoice)
    elif functionalitie == 3:
        for row in rows:
            invoice = {
                "TIPO_DOCUMENTO": row[0],
                "FOLIO": row[1],
                "EMISION": row[2],
                "MONTO_NETO": row[3],
                "MONTO_EXENTO": row[4],
                "MONTO_IVA": row[5],
                "MONTO_TOTAL": row[6]
            }
            invoices.append(invoice)
    elif functionalitie == 4:
        for row in rows:
            invoice = {
                "FOLIO": row[0],
                "NETO": row[1],
                "IVA": row[2],
                "TOTAL": row[3],
                "FECHA": row[4],
                "RUT_VENDEDOR": row[5],
                "SUCURSAL": row[6]
            }
            invoices.append(invoice)

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

def update_selected_invoice(invoice_number, updated_fields, functionalitie):
    """
    Actualizar campos específicos de una factura existente según la funcionalidad.
    
    Parameters:
    - invoice_number: Número de factura o folio que identifica el registro a actualizar.
    - updated_fields: Diccionario con los campos y sus nuevos valores.
    - functionalitie: Número que indica la funcionalidad (1: Facturas Recibidas, 2: Facturas Emitidas, 3: Boletas Electrónicas, 4: Boletas Físicas).
    """
    connection = get_connection()
    cursor = connection.cursor()

    if functionalitie == 1:
        # Actualización para facturas recibidas
        table_name = 'flat_invoices_received'
        id_field = 'INVOICE_NUMBER'
        valid_fields = ['ISSUE_DATE', 'SUBTOTAL', 'TAX', 'TOTAL', 'PAY_METHOD', 'ISSUER_NAME', 'ISSUER_ADDRESS']
    elif functionalitie == 2:
        # Actualización para facturas emitidas
        table_name = 'flat_invoices_issued'
        id_field = 'INVOICE_NUMBER'
        valid_fields = ['ISSUE_DATE', 'SUBTOTAL', 'TAX', 'TOTAL', 'PAY_METHOD', 'ISSUER_NAME', 'ISSUER_ADDRESS']
    elif functionalitie == 3:
        # Actualización para boletas electrónicas
        table_name = 'electronic_tickets'
        id_field = 'FOLIO'
        valid_fields = ['TIPO_DOCUMENTO', 'EMISION', 'MONTO_NETO', 'MONTO_EXENTO', 'MONTO_IVA', 'MONTO_TOTAL']
    elif functionalitie == 4:
        # Actualización para boletas físicas
        table_name = 'physical_tickets'
        id_field = 'FOLIO'
        valid_fields = ['NETO', 'IVA', 'TOTAL', 'FECHA', 'RUT_VENDEDOR', 'SUCURSAL']
    else:
        # Manejo de funcionalidad no reconocida
        cursor.close()
        close_connection(connection)
        return

    # Filtrar los campos válidos a actualizar
    fields_to_update = {k: v for k, v in updated_fields.items() if k in valid_fields}

    if not fields_to_update:
        # Si no hay campos válidos para actualizar, salir de la función
        cursor.close()
        close_connection(connection)
        return

    # Construir la parte SET de la consulta
    set_clause = ', '.join([f"{field} = %s" for field in fields_to_update.keys()])
    params = list(fields_to_update.values())
    params.append(invoice_number)

    # Construir la consulta de actualización
    update_query = f"""
        UPDATE {table_name}
        SET {set_clause}
        WHERE {id_field} = %s
    """

    # Ejecutar la consulta de actualización con parámetros
    cursor.execute(update_query, params)

    # Confirmar los cambios
    connection.commit()

    # Cerrar cursor y conexión
    cursor.close()
    close_connection(connection)

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


#############################
def create_physical_tickets(data):
    """Insertar data en tabla physical_tickets."""
    connection = get_connection()
    if not connection:
        return
    
    cursor = connection.cursor()
       
    # Convertir el DataFrame en una lista de diccionarios
    data_to_insert = data.to_dict(orient='records')

    # Definir la sentencia SQL de inserción
    insert_sql = """
    INSERT INTO physical_tickets (
        folio,
        neto,
        iva,
        total,
        dte,
        fecha,
        rut_vendedor,
        sucursal
    ) VALUES (
        :folio,
        :neto,
        :iva,
        :total,
        :dte,
        to_date(:fecha, 'YYYYMMDD'),
        :vendedor,
        :sucursal
    )
    """

    try:
        # Ejecutar la inserción
        cursor.executemany(insert_sql, data_to_insert)
        
        # Confirmar los cambios
        connection.commit()
        print(f"{cursor.rowcount} registros insertados exitosamente.")
    except Exception as e:
        print("Error al insertar datos:", e)
        connection.rollback()
    finally:
        # Cerrar cursor y conexión
        cursor.close()
        close_connection(connection)


def create_electronic_tickets(data):
    """Insertar data en tabla electronic_tickets."""
    connection = get_connection()
    if not connection:
        return
    
    cursor = connection.cursor()
       
    # Convertir el DataFrame en una lista de diccionarios
    data_to_insert = data.to_dict(orient='records')

    # Definir la sentencia SQL de inserción
    insert_sql = """
    INSERT INTO electronic_tickets (
        tipo,
        tipo_documento,
        folio,
        razon_social_receptor,
        fecha_publicacion,
        emision,
        monto_neto,
        monto_exento,
        monto_iva,
        monto_total,
        fecha_sii ,
        estado_sii
    ) VALUES (
        :tipo,
        :tipo_documento,
        :folio,
        :razon_social_receptor,
        to_date(:publicacion,'YYYYMMDD'),
        to_date(:emision,'YYYYMMDD'),
        :monto_neto,
        :monto_exento,
        :monto_iva,
        :monto_total,
        to_date(:fecha_sii,'YYYYMMDD'),
        :estado_sii
    )
    """

    try:
        # Ejecutar la inserción
        cursor.executemany(insert_sql, data_to_insert)
        
        # Confirmar los cambios
        connection.commit()
        print(f"{cursor.rowcount} registros insertados exitosamente.")
    except Exception as e:
        print("Error al insertar datos:", e)
        connection.rollback()
    finally:
        # Cerrar cursor y conexión
        cursor.close()
        close_connection(connection)