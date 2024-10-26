import pytesseract
import json
import re
import os
import sys
import shutil
from pdf2image import convert_from_path

# Configuración de rutas para agregar el directorio src al path de Python
route = os.path.abspath(__file__)
index_route = route.find("BackendHookedDocs")
local_path = route[:index_route + len("BackendHookedDocs")]
global_route = os.path.join(local_path, "src")

sys.path.append(global_route)

from core.crud import create_invoice

def extract(path_invoices):
    """
    Extrae el texto de facturas en formato PDF utilizando OCR.
    
    Parámetros:
    - path_invoices: Ruta de la carpeta que contiene los archivos de facturas.
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

            # Procesar el archivo PDF según el proveedor
            data = transform(extracted_text)
            load(data)

            # Mover archivo a la carpeta "PROCESADOS" después de procesarlo
            move_to_processed(file_path, path_invoices)

def transform(extracted_text):
    """
    Transforma el texto extraído y extrae los datos estructurados según el proveedor.
    
    Parámetros:
    - extracted_text: El texto extraído del PDF de la factura.

    Retorna:
    - Un diccionario con los datos estructurados de la factura.
    """
    transformed_text = extracted_text.upper()

    # Verificar el proveedor
    if "PROFESSIONAL FISHING SPA" in transformed_text:
        return transform_professional_fishing(transformed_text)
    elif "MI TIENDA SPA" in transformed_text:
        return transform_mi_tienda(transformed_text)
    elif "RAPALA" in transformed_text:
        return transform_rapala(transformed_text)
    else:
        raise ValueError("Proveedor no reconocido en el documento.")

def transform_professional_fishing(text):
    """
    Extrae los datos de la factura de PROFESSIONAL FISHING SPA.
    
    Parámetros:
    - text: Texto extraído de la factura.
    
    Retorna:
    - Un diccionario con los datos estructurados.
    """

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
        text = text.replace(old, new)

    # Inicializa el diccionario de datos para almacenar los campos extraídos
    data = {
        "invoice_number": None,
        "issue_date": None,
        "pay_method": None,
        "items": [],
        "subtotal": None,
        "tax": None,
        "total": None,
        "issuer": {
            "name": "PROFESSIONAL FISHING SPA",
            "rut": None,
            "address": None,
            "email": None,
            "phone": None
        }
    }

    # Extrae el nombre del emisor
    data["issuer"]["name"] = "PROFESSIONAL FISHING SPA"

    # Extrae el RUT del emisor
    rut_match = re.search(r'R\.U\.T:\s*(\d+\.\d+\.\d+-\d+)', text)
    if rut_match:
        data["issuer"]["rut"] = rut_match.group(1)

    # Extrae la dirección del emisor
    address_match = re.search(r'DIRECCION:\s*(.+?),\s*(\w+)', text)
    if address_match:
        data["issuer"]["address"] = address_match.group(1) + ", " + address_match.group(2)

    # Extrae el email del emisor
    email_match = re.search(r'EMAIL:\s*(\S+@\S+)', text)
    if email_match:
        data["issuer"]["email"] = email_match.group(1)

    # Extrae el número de teléfono del emisor
    phone_match = re.search(r'TELEFONO\(S\):\s*(\+?\d+)', text)
    if phone_match:
        data["issuer"]["phone"] = phone_match.group(1)

    # Extrae el número de factura
    invoice_number_match = re.search(r'FACTURA ELECTRONICA\s*N[º*]\s*(\d+)', text)
    if invoice_number_match:
        data["invoice_number"] = invoice_number_match.group(1)

    # Extrae la fecha de emisión
    issue_date_match = re.search(r'FECHA EMISION:\s*([0-9]{1,2} DE \w+ DE \d{4})', text)
    if issue_date_match:
        data["issue_date"] = issue_date_match.group(1)

    # Extrae el método de pago
    pay_method_match = re.search(r'FORMA PAGO:\s*(.+?)\s*(?:CANAL VENTA:|$)', text)
    if pay_method_match:
        data["pay_method"] = pay_method_match.group(1).strip()

    # Extrae los ítems de la factura
    items_section = re.search(
        r'CODIGO DESCRIPCION PRECIO DSCTO\.\(%\) RECARGO AF/EX VALOR\s*(.*?)\s*Nº LINEAS:', 
        text, 
        re.DOTALL
    )

    if items_section:
        items_text = items_section.group(1).strip()
        item_lines = items_text.splitlines()

        for line in item_lines:
            item_match = re.match(
                r'(?P<code>\S+)\s+(?P<description>.+?)\s+(?P<unit_price>[0-9,.]+)\s+AFECTO\s+(?P<total_price>[0-9,.]+)', 
                line
            )

            if item_match:
                item = {
                    "code": item_match.group("code").strip(),
                    "description": item_match.group("description").strip(),
                    "unit_price": float(item_match.group("unit_price").replace('.', '').replace(',', '.')),
                    "total_price": float(item_match.group("total_price").replace('.', '').replace(',', '.'))
                }
                data["items"].append(item)

    # Extrae el subtotal
    subtotal_match = re.search(r'SUBTOTAL:\s*\$\s*([0-9,.]+)', text)
    if subtotal_match:
        data["subtotal"] = float(subtotal_match.group(1).replace('.', '').replace(',', '.'))

    # Extrae el IVA
    tax_match = re.search(r'IVA \(19%\):\s*\$\s*([0-9,.]+)', text)
    if tax_match:
        data["tax"] = float(tax_match.group(1).replace('.', '').replace(',', '.'))

    # Extrae el total
    total_match = re.search(r'TOTAL:\s*\$\s*([0-9,.]+)', text)
    if total_match:
        data["total"] = float(total_match.group(1).replace('.', '').replace(',', '.'))

    return data

def transform_mi_tienda(text):
    """
    Extrae los datos de la factura de MI TIENDA SPA.
    
    Parámetros:
    - text: Texto extraído de la factura.
    
    Retorna:
    - Un diccionario con los datos estructurados.
    """

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
        'CBLUEFISHING.CL': '@BLUEFISHING.CL',
        'CHRISTIAN OELSENUELO.CL': 'CHRISTIAN@ELSENUELO.CL' ,
        '#$': '#'
    }

    # Aplica los reemplazos al texto
    for old, new in replacements.items():
        text = text.replace(old, new)

    print(text)

    data = {
        "invoice_number": None,
        "issue_date": None,
        "pay_method": "TRANSFERENCIA BANCARIA",
        "items": [],
        "subtotal": None,
        "tax": None,
        "total": None,
        "issuer": {
            "name": "MI TIENDA SPA",
            "rut": None,
            "address": "AV PROVIDENCIA 1208 OF 403",
            "email": "VENTAS@BLUEFISHING.CL",
            "phone": "+56938644642"
        }
    }

    # Extraer RUT del emisor
    rut_match = re.search(r'RUT:\s*(\d+\.\d+\.\d+-\d+)', text)
    if rut_match:
        data["issuer"]["rut"] = rut_match.group(1)

    # Extraer fecha de emisión
    issue_date_match = re.search(r'FECHA EMISION:\s*(\d{2}/\d{2}/\d{4})', text)
    if issue_date_match:
        data["issue_date"] = issue_date_match.group(1)

    # Extraer el número de factura
    invoice_number_match = re.search(r'N[º*]?\s*(\d+)', text)
    if invoice_number_match:
        data["invoice_number"] = invoice_number_match.group(1)

    # Extraer ítems de la factura
    items_section = re.findall(
        r'(\d+)\s+([A-Z0-9-]+)\s+([A-Z\s-]+)\s+\$ ([\d.,]+)\s+[\d.]+%\s+\$ ([\d.,]+)',
        text
    )
    for item in items_section:
        data["items"].append({
            "quantity": int(item[0]),
            "sku": item[1].strip(),
            "description": item[2].strip(),
            "unit_price": float(item[3].replace('.', '').replace(',', '.')),
            "subtotal": float(item[4].replace('.', '').replace(',', '.'))
        })

    # Extraer el subtotal
    subtotal_match = re.search(r'NETO\s*\(\$\)\s*([0-9,.]+)', text)
    if subtotal_match:
        data["subtotal"] = float(subtotal_match.group(1).replace('.', '').replace(',', '.'))

    # Extraer el IVA
    tax_match = re.search(r'I\.V\.A\.\s*19%\s*\$\s*([0-9,.]+)', text)
    if tax_match:
        data["tax"] = float(tax_match.group(1).replace('.', '').replace(',', '.'))

    # Extraer el total
    total_match = re.search(r'TOTAL\s*\(\$\)\s*([0-9,.]+)', text)
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
