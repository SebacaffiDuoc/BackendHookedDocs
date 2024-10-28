import pdfplumber
import re
import os
import sys
import shutil

# Configuración de rutas
route = os.path.abspath(__file__)
index_route = route.find("BackendHookedDocs")
local_path = route[:index_route + len("BackendHookedDocs")]
global_route = os.path.join(local_path, "src")

from core.crud import *

sys.path.append(global_route)

def extract(path_invoices):
    """
    Extrae el texto de facturas en formato PDF utilizando pdfplumber.
    
    Parámetros:
    - path_invoices: Ruta de la carpeta que contiene los archivos de facturas.
    """
    for file in os.listdir(path_invoices):
        if file.endswith(".pdf"):
            file_path = os.path.join(path_invoices, file)
            try:
                # Utiliza pdfplumber para extraer el texto del PDF
                with pdfplumber.open(file_path) as pdf:
                    extracted_text = ''
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            extracted_text += page_text + '\n'
                
                # Procesar el archivo PDF
                data = transform(extracted_text)
                load(data)
                
                # Mover archivo a la carpeta "PROCESADOS" después de procesarlo
                move_to_processed(file_path, path_invoices)
            except Exception as e:
                print(f"Error al procesar el archivo {file}: {e}")

def transform(extracted_text):
    """
    Transforma el texto extraído y extrae los datos estructurados de la factura.
    
    Parámetros:
    - extracted_text: El texto extraído del PDF de la factura.
    
    Retorna:
    - Un diccionario con los datos estructurados de la factura.
    """
    transformed_text = extracted_text.upper()

    # Diccionario de reemplazos para normalizar el texto
    replacements = {
        'Á': 'A', 
        'Ã': 'Ñ',
        'É': 'E', 
        'Í': 'I', 
        'Ó': 'O', 
        'Ú': 'U',
        'N*': 'Nº', 
        'N?': 'Nº', 
        'S.1.1': 'S.I.I.',
        'S.I.1': 'S.I.I',
        '#$': '#',
        'OGMAIL': '@GMAIL',
        'AM MONTO NETO': 'MONTO NETO',
        'KN LV.A.': 'I.V.A.',
        '" H IMPUESTO': 'IMPUESTO',
        'Ñ TOTAL': 'TOTAL',
    }

    # Aplica los reemplazos al texto
    for old, new in replacements.items():
        transformed_text = transformed_text.replace(old, new)

    # Inicializa el diccionario de datos para almacenar los campos extraídos
    data = {
        "pay_method": None,
        "items": [],
        "subtotal": None,
        "tax": None,
        "total": None,
        "issuer": {
            "name": None,
            "rut": None,
            "economic_activity": None,
            "address": None,
            "email": None,
            "phone": None,
            "invoice_number": None,
            "invoice_type": None,
            "issue_date": None,
        },
        "buyer": {
            "name": None,
            "rut": None,
            "economic_activity": None,
            "address": None,
            "commune": None
        }
    }

    # Diccionario para convertir meses en español a números
    months = {
        'ENERO': '01',
        'FEBRERO': '02',
        'MARZO': '03',
        'ABRIL': '04',
        'MAYO': '05',
        'JUNIO': '06',
        'JULIO': '07',
        'AGOSTO': '08',
        'SEPTIEMBRE': '09',
        'OCTUBRE': '10',
        'NOVIEMBRE': '11',
        'DICIEMBRE': '12'
    }

    # Función para parsear valores numéricos
    def parse_float(num_str):
        num_str = num_str.replace('.', '').replace(',', '.')
        return float(num_str)

    # Extracción de datos usando expresiones regulares

    # Emisor
    # Extracción del RUT y nombre del emisor
    issuer_rut_match = re.search(r'R\.U\.T\.?:\s*([\d\.\-\s]+)', transformed_text)
    if issuer_rut_match:
        data['issuer']['rut'] = issuer_rut_match.group(1).strip().replace('.', '').replace(' ', '').replace('-', '')
        # Ahora capturamos el nombre que está después del RUT
        rut_end_index = issuer_rut_match.end()
        # Capturar todas las líneas hasta encontrar 'FACTURA ELECTRONICA' o 'GIRO:'
        lines_after_rut = transformed_text[rut_end_index:].split('\n')
        name_lines = []
        for line in lines_after_rut:
            line = line.strip()
            if line and 'FACTURA ELECTRONICA' not in line and 'GIRO:' not in line:
                name_lines.append(line)
            else:
                break
        data['issuer']['name'] = ' '.join(name_lines)

    # Extracción del tipo de factura
    issuer_invoice_type_match = re.search(r'\n(FACTURA ELECTRONICA)\n', transformed_text)
    if issuer_invoice_type_match:
        data["issuer"]["invoice_type"] = issuer_invoice_type_match.group(1)

    # Extracción del número de factura
    invoice_number_match = re.search(r'N[ºN]?\s*(\d+)', transformed_text)
    if invoice_number_match:
        data["issuer"]["invoice_number"] = invoice_number_match.group(1).strip()

    # Extracción del giro
    issuer_economic_activity_match = re.search(r'GIRO:\s*(.*?)(?:N[ºN]|BLANCO|EMAIL|R\.U\.T\.:)', transformed_text, re.DOTALL)
    if issuer_economic_activity_match:
        data["issuer"]["economic_activity"] = issuer_economic_activity_match.group(1).strip().replace('\n', ' ')

    # Extracción de la dirección
    address_match = re.search(r'\n(BLANCO.*)', transformed_text)
    if address_match:
        data["issuer"]["address"] = address_match.group(1).strip()

    # Extracción del email
    email_match = re.search(r'EMAIL\s*:\s*(\S+@\S+)', transformed_text)
    if email_match:
        data["issuer"]["email"] = email_match.group(1)

    # Extracción del teléfono
    phone_match = re.search(r'TELEFONO\s*:\s*((?:\d+\s*)+)', transformed_text, re.DOTALL)
    if phone_match:
        phone = phone_match.group(1)
        phone = ''.join(re.findall(r'\d+', phone))
        data["issuer"]["phone"] = phone

    # Extracción de la fecha de emisión
    issue_date_match = re.search(r'FECHA EMISION:\s*([0-9]{1,2}) DE (\w+) DEL (\d{4})', transformed_text)
    if issue_date_match:
        day = issue_date_match.group(1).zfill(2)
        month_name = issue_date_match.group(2).upper()
        year = issue_date_match.group(3)
        month = months.get(month_name, '00')
        issue_date_formatted = f"{day}{month}{year}"
        data["issuer"]["issue_date"] = issue_date_formatted

    # Método de pago
    pay_method_match = re.search(r'FORMA DE PAGO:\s*(.*)', transformed_text)
    if pay_method_match:
        data["pay_method"] = pay_method_match.group(1).strip()

    # Items
    items_section_match = re.search(
        r'CODIGO DESCRIPCION CANTIDAD PRECIO.*?\n.*?\n(.*?)(?:FORMA DE PAGO|MONTO NETO)', 
        transformed_text, 
        re.DOTALL
    )
    if items_section_match:
        items_text = items_section_match.group(1).strip()
        item_lines = items_text.splitlines()
        for line in item_lines:
            line = line.strip()
            if not line:
                continue
            line_regex = r'-\s*(?P<description>.*?)\s+(?P<quantity>\d+\s*\d*)\s+(?P<unit_price>[\d.,]+)\s+(?P<total_price>[\d.,]+)'
            item_match = re.match(line_regex, line)
            if item_match:
                description = item_match.group('description').strip()
                quantity = item_match.group('quantity').strip().replace(" ","")
                unit_price = parse_float(item_match.group('unit_price'))
                total_price = parse_float(item_match.group('total_price'))
                item = {
                    'description': description,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': total_price,
                }
                data["items"].append(item)

    # Totales
    subtotal_match = re.search(r'MONTO NETO \$\s*([\d.,]+)', transformed_text)
    if subtotal_match:
        data['subtotal'] = parse_float(subtotal_match.group(1))

    tax_match = re.search(r'I\.V\.A\. 19% \$\s*([\d.,]+)', transformed_text)
    if tax_match:
        data['tax'] = parse_float(tax_match.group(1))

    total_match = re.search(r'TOTAL \$\s*([\d.,]+)', transformed_text)
    if total_match:
        data['total'] = parse_float(total_match.group(1))

    # Comprador
    buyer_section_match = re.search(
        r'SEÑOR\(ES\):\s*(.*?)\n(?:CONTACTO:|TIPO DE COMPRA:|CODIGO DESCRIPCION)', 
        transformed_text, 
        re.DOTALL
    )
    if buyer_section_match:
        buyer_section = buyer_section_match.group(1)

        # Nombre
        buyer_name_line = buyer_section.split('\n')[0].strip()
        data['buyer']['name'] = buyer_name_line

        # RUT
        buyer_rut_match = re.search(r'R\.U\.T\.:\s*([\d\.]+-\s*\d+)', buyer_section)
        if buyer_rut_match:
            data['buyer']['rut'] = buyer_rut_match.group(1).replace('.', '').replace(' ', '').replace('-', '')

        # Giro
        buyer_giro_match = re.search(r'GIRO:\s*(.*)', buyer_section)
        if buyer_giro_match:
            data['buyer']['economic_activity'] = buyer_giro_match.group(1).strip()

        # Dirección
        buyer_address_match = re.search(r'DIRECCION:\s*(.*)', buyer_section)
        if buyer_address_match:
            data['buyer']['address'] = buyer_address_match.group(1).strip()

        # Comuna
        buyer_comuna_match = re.search(r'COMUNA\s*(.*?)\s*CIUDAD:', buyer_section)
        if buyer_comuna_match:
            data['buyer']['commune'] = buyer_comuna_match.group(1).strip()

    return data



def load(data):
    """
    Carga los datos procesados en una base de datos (actualmente solo muestra los datos).
    
    Parámetros:
    - data: El diccionario con los datos procesados de la factura.
    """
    create_invoice(data, 'invoices_issued')
    # Puedes descomentar la siguiente línea si deseas imprimir los datos cargados
    # print(data)

def move_to_processed(file_path, path_invoices):
    """
    Mueve un archivo procesado a la carpeta "PROCESADOS".
    
    Parámetros:
    - file_path: Ruta del archivo procesado.
    - path_invoices: Ruta de la carpeta que contiene los archivos de facturas.
    """
    processed_folder = os.path.join(path_invoices, "PROCESADOS")
    if not os.path.exists(processed_folder):
        os.makedirs(processed_folder)
    shutil.move(file_path, os.path.join(processed_folder, os.path.basename(file_path)))

def main(invoices_issued_path):
    """
    Función principal que coordina las etapas de extracción, transformación y carga de datos.
    """
    extract(invoices_issued_path)