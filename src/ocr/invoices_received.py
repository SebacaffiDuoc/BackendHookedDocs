import pytesseract
import json
import re
import os
import sys
from pdf2image import convert_from_path

route = os.path.abspath(__file__)
index_route = route.find("BackendHookedDocs")
local_path = route[:index_route + len("BackendHookedDocs")]
global_route = os.path.join(local_path, "src")

sys.path.append(global_route)

def pdf_to_text(pdf_path):
    # Convertir el PDF a imágenes
    images = convert_from_path(pdf_path)

    # Extraer texto de cada imagen usando OCR
    extracted_text = ""
    for img in images:
        text = pytesseract.image_to_string(img, lang='spa')
        extracted_text += text + "\n"
    process_text = clean_text(extracted_text)

    return process_text

def clean_text(text):

    text = text.upper()
    text = text.replace('Á', 'A')
    text = text.replace('É', 'E')
    text = text.replace('Í', 'I')
    text = text.replace('Ó', 'O')
    text = text.replace('Ú', 'U')
    text = text.replace('N*', 'Nº')
    text = text.replace('N?', 'Nº')
    text = text.replace('S.I.1', 'S.I.I.')
    text = text.replace('OPROFISHING.CL', '@PROFISHING.CL')
    text = text.replace('#$', '#')

    print(text)

    return text

def process_invoice_text(text):
    # Inicializar el diccionario de datos
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

    # Extraer la información del emisor de la factura
    issuer_name_match = re.search(r'PROFESSIONAL\s+FISHING\s+SPA', text)
    if issuer_name_match:
        data["issuer"]["name"] = issuer_name_match.group(0)

    rut_match = re.search(r'R\.U\.T:\s*(\d+\.\d+\.\d+-\d+)', text)
    if rut_match:
        data["issuer"]["rut"] = rut_match.group(1)

    address_match = re.search(r'DIRECCION:\s*(.+?),\s*(\w+)', text)
    if address_match:
        data["issuer"]["address"] = address_match.group(1) + ", " + address_match.group(2)

    email_match = re.search(r'EMAIL:\s*(\S+@\S+)', text)
    if email_match:
        data["issuer"]["email"] = email_match.group(1)

    phone_match = re.search(r'TELEFONO\(S\):\s*(\+?\d+)', text)
    if phone_match:
        data["issuer"]["phone"] = phone_match.group(1)

    # Extraer el número de factura
    invoice_number_match = re.search(r'FACTURA ELECTRONICA\s*N[º*]\s*(\d+)', text)
    if invoice_number_match:
        data["invoice_number"] = invoice_number_match.group(1)

    # Extraer la fecha de emisión
    issue_date_match = re.search(r'FECHA EMISION:\s*([0-9]{1,2} DE \w+ DE \d{4})', text)
    if issue_date_match:
        data["issue_date"] = issue_date_match.group(1)

    # Extraer el método de pago
    pay_method_match = re.search(r'FORMA PAGO:\s*(.+?)\s*(?:CANAL VENTA:|$)', text)
    if pay_method_match:
        data["pay_method"] = pay_method_match.group(1).strip()

    # Extraer el canal de venta
    sales_channel_match = re.search(r'CANAL VENTA:\s*(.+?)\s*\|', text)
    if sales_channel_match:
        data["sales_channel"] = sales_channel_match.group(1).strip()

    # Extraer el número de pedido
    order_number_match = re.search(r'N[º*] PEDIDO:\s*(\d+)', text)
    if order_number_match:
        data["order_number"] = order_number_match.group(1)

    # Paso 1: Extraer la sección de los ítems
    items_section = re.search(
        r'CODIGO DESCRIPCION PRECIO DSCTO\.\(%\) RECARGO AF/EX VALOR\s*(.*?)\s*Nº LINEAS:', 
        text, 
        re.DOTALL
    )

    if items_section:
        # Extraer la sección de los ítems
        items_text = items_section.group(1).strip()
        # Dividir el texto en líneas para procesar cada ítem
        item_lines = items_text.splitlines()

        # Paso 2: Procesar cada ítem línea por línea
        for line in item_lines:
            # Expresión regular para capturar los datos de cada ítem
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

    # Extraer el subtotal
    subtotal_match = re.search(r'SUBTOTAL:\s*\$\s*([0-9,.]+)', text)
    if subtotal_match:
        data["subtotal"] = float(subtotal_match.group(1).replace('.', '').replace(',', '.'))

    # Extraer el IVA
    tax_match = re.search(r'IVA \(19%\):\s*\$\s*([0-9,.]+)', text)
    if tax_match:
        data["tax"] = float(tax_match.group(1).replace('.', '').replace(',', '.'))

    # Extraer el total
    total_match = re.search(r'TOTAL:\s*\$\s*([0-9,.]+)', text)
    if total_match:
        data["total"] = float(total_match.group(1).replace('.', '').replace(',', '.'))

    return data


def extract_invoice_data(pdf_path):
    # Extraer el texto de la factura
    process_text = pdf_to_text(pdf_path)
    
    # Procesar el texto para extraer los datos en formato JSON
    invoice_data = process_invoice_text(process_text)
    
    return invoice_data

if __name__ == "__main__":
    pdf_path = "docs/invoce/33-8510.pdf"
    
    # Extraer y procesar los datos de la factura
    invoice_json = extract_invoice_data(pdf_path)
    
    # Imprimir el JSON resultante
    print(json.dumps(invoice_json, indent=4, ensure_ascii=False))