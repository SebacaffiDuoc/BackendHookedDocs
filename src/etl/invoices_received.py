import pytesseract
import json
import re
import os
import sys
import shutil
from pdf2image import convert_from_path
from src.core.crud import create_invoice, read_invoices, update_invoice, delete_invoice

# Configuración de rutas para agregar el directorio src al path de Python
route = os.path.abspath(__file__)
index_route = route.find("BackendHookedDocs")
local_path = route[:index_route + len("BackendHookedDocs")]
global_route = os.path.join(local_path, "src")

sys.path.append(global_route)

def extract(path_invoices):
    """
    Extrae el texto de facturas en formato PDF utilizando OCR.
    
    Parámetros:
    - path_invoices: Ruta de la carpeta que contiene los archivos de facturas.
    
    Retorna:
    - El texto extraído del archivo.
    """
    for file in os.listdir(path_invoices):
        if file.endswith(".pdf"):
            file_path = os.path.join(path_invoices, file)
            
            images = convert_from_path(file_path)  # Convierte las páginas del PDF en imágenes.
            extracted_text = ""
            for img in images:
                # Aplica OCR a cada imagen y concatena el texto extraído.
                text = pytesseract.image_to_string(img, lang='spa')
                extracted_text += text + "\n"
            
            # Procesar el archivo PDF
            data = transform(extracted_text)
            load(data)
            
            # Mover archivo a la carpeta "PROCESADOS" después de procesarlo
            move_to_processed(file_path, path_invoices)

def transform(extracted_text):
    """
    Transforma el texto extraído, realiza reemplazos de caracteres y extrae los datos estructurados de la factura.
    
    Parámetros:
    - extracted_text: El texto extraído del PDF de la factura.

    Retorna:
    - Un diccionario con los datos estructurados de la factura.
    """
    transformed_text = extracted_text.upper()

    # Diccionario de reemplazos para normalizar el texto
    replacements = {
        'Á': 'A', 
        'É': 'E', 
        'Í': 'I', 
        'Ó': 'O', 
        'Ú': 'U',
        'N*': 'Nº', 
        'N?': 'Nº', 
        'S.I.1': 'S.I.I.',
        'OPROFISHING.CL': '@PROFISHING.CL', 
        '#$': '#'
    }

    # Aplica los reemplazos al texto
    for old, new in replacements.items():
        transformed_text = transformed_text.replace(old, new)

    # Inicializa el diccionario de datos para almacenar los campos extraídos
    data = {
        "invoice_number": None,
        "issue_date": None,
        "pay_method": None,
        "sales_channel": None,
        "order_number": None,
        "items": [],
        "subtotal": None,
        "tax": None,
        "total": None,
        "issuer": {
            "name": None,
            "rut": None,
            "address": None,
            "email": None,
            "phone": None
        }
    }

    # Extrae el nombre del emisor
    issuer_name_match = re.search(r'PROFESSIONAL\s+FISHING\s+SPA', transformed_text)
    if issuer_name_match:
        data["issuer"]["name"] = issuer_name_match.group(0)

    # Extrae el RUT del emisor
    rut_match = re.search(r'R\.U\.T:\s*(\d+\.\d+\.\d+-\d+)', transformed_text)
    if rut_match:
        data["issuer"]["rut"] = rut_match.group(1)

    # Extrae la dirección del emisor
    address_match = re.search(r'DIRECCION:\s*(.+?),\s*(\w+)', transformed_text)
    if address_match:
        data["issuer"]["address"] = address_match.group(1) + ", " + address_match.group(2)

    # Extrae el email del emisor
    email_match = re.search(r'EMAIL:\s*(\S+@\S+)', transformed_text)
    if email_match:
        data["issuer"]["email"] = email_match.group(1)

    # Extrae el número de teléfono del emisor
    phone_match = re.search(r'TELEFONO\(S\):\s*(\+?\d+)', transformed_text)
    if phone_match:
        data["issuer"]["phone"] = phone_match.group(1)

    # Extrae el número de factura
    invoice_number_match = re.search(r'FACTURA ELECTRONICA\s*N[º*]\s*(\d+)', transformed_text)
    if invoice_number_match:
        data["invoice_number"] = invoice_number_match.group(1)

    # Extrae la fecha de emisión
    issue_date_match = re.search(r'FECHA EMISION:\s*([0-9]{1,2} DE \w+ DE \d{4})', transformed_text)
    if issue_date_match:
        data["issue_date"] = issue_date_match.group(1)

    # Extrae el método de pago
    pay_method_match = re.search(r'FORMA PAGO:\s*(.+?)\s*(?:CANAL VENTA:|$)', transformed_text)
    if pay_method_match:
        data["pay_method"] = pay_method_match.group(1).strip()

    # Extrae el canal de venta
    sales_channel_match = re.search(r'CANAL VENTA:\s*(.+?)\s*\|', transformed_text)
    if sales_channel_match:
        data["sales_channel"] = sales_channel_match.group(1).strip()

    # Extrae el número de pedido
    order_number_match = re.search(r'N[º*] PEDIDO:\s*(\d+)', transformed_text)
    if order_number_match:
        data["order_number"] = order_number_match.group(1)

    # Extrae la sección de los ítems entre los delimitadores "CODIGO DESCRIPCION..." y "Nº LINEAS"
    items_section = re.search(
        r'CODIGO DESCRIPCION PRECIO DSCTO\.\(%\) RECARGO AF/EX VALOR\s*(.*?)\s*Nº LINEAS:', 
        transformed_text, 
        re.DOTALL
    )

    # Procesa cada línea de ítems
    if items_section:
        items_text = items_section.group(1).strip()
        item_lines = items_text.splitlines()

        for line in item_lines:
            # Extrae los detalles de cada ítem usando una expresión regular
            item_match = re.match(
                r'(?P<code>\S+)\s+(?P<description>.+?)\s+(?P<unit_price>[0-9,.]+)\s+AFECTO\s+(?P<total_price>[0-9,.]+)', 
                line
            )

            if item_match:
                # Agrega el ítem al diccionario de datos
                item = {
                    "code": item_match.group("code").strip(),
                    "description": item_match.group("description").strip(),
                    "unit_price": float(item_match.group("unit_price").replace('.', '').replace(',', '.')),
                    "total_price": float(item_match.group("total_price").replace('.', '').replace(',', '.'))
                }
                data["items"].append(item)

    # Extrae el subtotal
    subtotal_match = re.search(r'SUBTOTAL:\s*\$\s*([0-9,.]+)', transformed_text)
    if subtotal_match:
        data["subtotal"] = float(subtotal_match.group(1).replace('.', '').replace(',', '.'))

    # Extrae el IVA
    tax_match = re.search(r'IVA \(19%\):\s*\$\s*([0-9,.]+)', transformed_text)
    if tax_match:
        data["tax"] = float(tax_match.group(1).replace('.', '').replace(',', '.'))

    # Extrae el total
    total_match = re.search(r'TOTAL:\s*\$\s*([0-9,.]+)', transformed_text)
    if total_match:
        data["total"] = float(total_match.group(1).replace('.', '').replace(',', '.'))

    return data

def load(data):
    """
    Carga los datos procesados en la base de datos.
    
    Parámetros:
    - data: El diccionario con los datos procesados de la factura.
    """
    # Ejemplo de carga de datos en la base de datos (crear una nueva factura)
    create_invoice(data, 'invoices_received')
    print(data)

def move_to_processed(file_path, path_invoices):
    """
    Mueve el archivo procesado a la carpeta "PROCESADOS".
    
    Parámetros:
    - file_path: Ruta del archivo procesado.
    - path_invoices: Ruta de la carpeta que contiene los archivos de facturas.
    """
    processed_folder = os.path.join(path_invoices, "PROCESADOS")
    if not os.path.exists(processed_folder):
        os.makedirs(processed_folder)

    # Mover el archivo a la carpeta "PROCESADOS"
    processed_path = os.path.join(processed_folder, os.path.basename(file_path))
    shutil.move(file_path, processed_path)

    print(f"Archivo {file_path} movido a {processed_path}")

def main(invoices_received_path):
    """
    Función principal que coordina las etapas de extracción, transformación y carga de datos.
    
    Parámetros:
    - invoices_received_path: Ruta de la carpeta que contiene los archivos de facturas.
    """
    extract(invoices_received_path)