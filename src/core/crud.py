import json
import datetime
from .database import get_connection, close_connection

# CREA nuevos registros en facturas emitidas o recibidas
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


# CREA nuevos registros en boletas fisicas
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


# CREA nuevos registros en boletas electronicas
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


# LEE registro de validaciones en log
def read_log():
    """Leer todas las facturas desde la tabla invoices."""
    connection = get_connection()
    cursor = connection.cursor()
    
    # Consulta de selección
    select_query = f"SELECT PROCESS, INVOICE_ID, ISSUE_DATE, VALIDATION_MESSAGE FROM invoice_audit_log"
    
    # Ejecutar la consulta
    cursor.execute(select_query)
    rows = cursor.fetchall()
    
    # Procesar los resultados
    invoices = [{"PROCESS": row[0], "INVOICE_ID": row[1], "ISSUE_DATE": row[2], "VALIDATION_MESSAGE": row[3]} for row in rows]
    
    # Cerrar cursor y conexión
    cursor.close()
    close_connection(connection)
    
    return invoices


# LEE campos validados segun funcionabilidad
def read_select_invoice(doc_number, functionalitie):
    """Leer una factura o documento específico desde la base de datos."""
    import datetime

    connection = get_connection()
    cursor = connection.cursor()

    if functionalitie == 1:
        # Consulta de selección para facturas recibidas
        select_query = """SELECT  
                            subtotal, SUM(t2.item_total_price) AS item_total_price,tax, total,
                            pay_method,issuer_name,issuer_rut,invoice_number
                        FROM flat_invoices_received t1
                        join flat_invoices_received_items t2 on t1.invoice_number = t2.invoice_number_fk 
                        WHERE t1.invoice_number = :doc_number
                        group by subtotal, tax, total, pay_method, issuer_name, 
                        issuer_rut, invoice_number"""
        date_fields = ['ISSUE_DATE']
    elif functionalitie == 2:
        # Consulta de selección para facturas emitidas
        select_query = """SELECT 
                            subtotal, SUM(T2.item_total_price) AS item_total_price, tax, total, 
                            pay_method, issuer_rut, invoice_number, invoice_type, buyer_name, buyer_rut	
                        FROM flat_invoices_issued t1
                        JOIN flat_invoices_issued_items T2 ON t1.invoice_number = T2.invoice_number_fk 
                        WHERE t1.invoice_number = :doc_number
                        GROUP BY subtotal, tax, total, pay_method, issuer_rut, 
                        invoice_number, invoice_type, buyer_name, buyer_rut"""
        date_fields = ['ISSUE_DATE']
    elif functionalitie == 3:
        # Consulta de selección para boletas físicas
        select_query = """SELECT 
                            FOLIO, NETO, IVA, TOTAL, 
                            FECHA, RUT_VENDEDOR, SUCURSAL
                          FROM physical_tickets
                          WHERE folio = :doc_number"""
        date_fields = ['FECHA']
    elif functionalitie == 4:
        # Consulta de selección para boletas electrónicas
        select_query = """SELECT 
                            TIPO_DOCUMENTO, FOLIO, EMISION, MONTO_NETO, 
                            MONTO_EXENTO, MONTO_IVA, MONTO_TOTAL
                          FROM electronic_tickets
                          WHERE folio = :doc_number"""
        date_fields = ['EMISION']
    else:
        # Manejo de funcionalidad no reconocida
        cursor.close()
        close_connection(connection)
        return []

    # Ejecutar la consulta con parámetros para evitar inyección SQL
    cursor.execute(select_query, doc_number=doc_number)
    rows = cursor.fetchall()

    # Procesar los resultados según la funcionalidad
    invoices = []
    if functionalitie ==1:
        for row in rows:
            
            invoice = {
                "subtotal": row[0],
                "item_total_price": row[1],
                "tax": row[2],
                "total": row[3],
                "pay_method": row[4],
                "issuer_name": row[5],
                "issuer_rut": row[6],
                "invoice_number": row[7]
            }
            invoices.append(invoice)
    elif functionalitie == 2:
        for row in rows:

            invoice = {
                "subtotal": row[0],
                "item_total_price": row[1],
                "tax": row[2],
                "total": row[3],
                "pay_method": row[4],
                "issuer_rut": row[5],
                "invoice_number": row[6],
                "invoice_type": row[7],
                "buyer_name": row[8],
                "buyer_rut": row[9],
            }
            invoices.append(invoice)
    elif functionalitie == 3:
        for row in rows:
            # Convertir FECHA a cadena con formato DD/MM/YYYY
            fecha = row[4]
            if fecha:
                fecha_str = fecha.strftime('%d/%m/%Y')
            else:
                fecha_str = ''

            invoice = {
                "FOLIO": row[0],
                "NETO": row[1],
                "IVA": row[2],
                "TOTAL": row[3],
                "FECHA": fecha_str,
                "RUT_VENDEDOR": row[5],
                "SUCURSAL": row[6]
            }
            invoices.append(invoice)
    elif functionalitie == 4:
        for row in rows:
            # Convertir EMISION a cadena con formato DD/MM/YYYY
            emision = row[2]
            if emision:
                emision_str = emision.strftime('%d/%m/%Y')
            else:
                emision_str = ''

            invoice = {
                "TIPO_DOCUMENTO": row[0],
                "FOLIO": row[1],
                "EMISION": emision_str,
                "MONTO_NETO": row[3],
                "MONTO_EXENTO": row[4],
                "MONTO_IVA": row[5],
                "MONTO_TOTAL": row[6]
            }
            invoices.append(invoice)

    # Cerrar cursor y conexión
    cursor.close()
    close_connection(connection)

    return invoices


# ACTUALIZA campos validados segun funcionabilidad
def update_selected_invoice(invoice_number, updated_fields, functionalitie):
    """
    Actualizar campos específicos de una factura existente según la funcionalidad.

    Parameters:
    - invoice_number: Número de factura o folio que identifica el registro a actualizar.
    - updated_fields: Diccionario con los campos y sus nuevos valores.
    - functionalitie: Número que indica la funcionalidad (1: Facturas Recibidas, 2: Facturas Emitidas, 3: Boletas Físicas, 4: Boletas Electrónicas).
    """
    connection = get_connection()
    cursor = connection.cursor()

    if functionalitie == 1:
        # Actualización para facturas recibidas
        table_name = 'flat_invoices_received'
        id_field = 'INVOICE_NUMBER'
        valid_fields = ['subtotal', 'item_total_price','tax', 'total','pay_method','issuer_name','issuer_rut','invoice_number']
    elif functionalitie == 2:
        # Actualización para facturas emitidas
        table_name = 'flat_invoices_issued'
        id_field = 'INVOICE_NUMBER'
        valid_fields = ['subtotal', 'item_total_price', 'tax', 'total', 'pay_method', 'issuer_rut', 'invoice_number', 'invoice_type', 'buyer_name', 'buyer_rut']
    elif functionalitie == 3:
        # Actualización para boletas físicas
        table_name = 'physical_tickets'
        id_field = 'FOLIO'
        valid_fields = ['NETO', 'IVA', 'TOTAL', 'FECHA', 'RUT_VENDEDOR', 'SUCURSAL']
        date_fields = ['FECHA']
    elif functionalitie == 4:
        # Actualización para boletas electrónicas
        table_name = 'electronic_tickets'
        id_field = 'FOLIO'
        valid_fields = ['TIPO_DOCUMENTO', 'EMISION', 'MONTO_NETO', 'MONTO_EXENTO', 'MONTO_IVA', 'MONTO_TOTAL']
        date_fields = ['EMISION']
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

    # Convertir los campos de fecha a objetos datetime
    for date_field in date_fields:
        if date_field in fields_to_update:
            date_str = fields_to_update[date_field]
            try:
                # Intentar detectar el formato de fecha
                date_obj = None
                for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
                    try:
                        date_obj = datetime.datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                if date_obj is None:
                    raise ValueError
                fields_to_update[date_field] = date_obj
            except ValueError:
                # Manejar el error si el formato no es correcto
                cursor.close()
                close_connection(connection)
                raise ValueError(f"Formato de fecha inválido para {date_field}: '{date_str}'. Use un formato válido como 'DD/MM/YYYY'.")

    # Construir la parte SET de la consulta
    set_clause = ', '.join([f"{field} = :{field}" for field in fields_to_update.keys()])

    # Añadir el invoice_number al diccionario de parámetros
    params = fields_to_update.copy()
    params['invoice_number'] = invoice_number

    # Construir la consulta de actualización
    update_query = f"""
        UPDATE {table_name}
        SET {set_clause}
        WHERE {id_field} = :invoice_number
    """
    
    # Ejecutar la consulta de actualización con parámetros
    cursor.execute(update_query, params)

    # Confirmar los cambios
    connection.commit()

    # Cerrar cursor y conexión
    cursor.close()
    close_connection(connection)


# ELIMINA registros segun funcionabilidad
def delete_invoice(functionalitie,invoice_number):
    """Eliminar una factura de la tabla invoices."""
    connection = get_connection()
    cursor = connection.cursor()
    
    # Segun funcionabilidad
    if functionalitie == 1:
    # Consulta de selección para facturas recibidas
        delete_query = """delete FROM flat_invoices_received WHERE invoice_number = :invoice_number"""
    elif functionalitie == 2:
        # Consulta de selección para facturas emitidas
        delete_query = """delete FROM flat_invoices_issued  WHERE invoice_number = :invoice_number"""
    elif functionalitie == 3:
        # Consulta de selección para boletas físicas
        delete_query = """delete FROM physical_tickets WHERE folio = :invoice_number"""
    elif functionalitie == 4:
        # Consulta de selección para boletas electrónicas
        delete_query = """delete FROM electronic_tickets WHERE folio = :invoice_number"""
    else:
        # Manejo de funcionalidad no reconocida
        cursor.close()
        close_connection(connection)
    
    # Ejecutar la eliminación
    cursor.execute(delete_query, invoice_number=invoice_number)
    
    # Confirmar los cambios
    connection.commit()
    
    # Cerrar cursor y conexión
    cursor.close()
    close_connection(connection)
