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

def extract(path_invoices):
    """
    Extrae el texto de una factura en formato PDF utilizando OCR.
    
    Parámetros:
    - path_invoices: Ruta del archivo PDF de la factura.

    Retorna:
    - El texto extraído del PDF.
    """
    images = convert_from_path(path_invoices)  # Convierte las páginas del PDF en imágenes.

    extracted_text = ""
    for img in images:
        # Aplica OCR a cada imagen y concatena el texto extraído.
        text = pytesseract.image_to_string(img, lang='spa')
        extracted_text += text + "\n"

    return extracted_text

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
        'Ã': 'Ñ',
        'É': 'E', 
        'Í': 'I', 
        'Ó': 'O', 
        'Ú': 'U',
        'N*': 'Nº', 
        'N?': 'Nº', 
        'S.1.1': 
        'S.I.I.',
        'S.I.1': 
        'S.I.I',
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

    # Parse valores numericos
    def parse_float(num_str):
        num_str = num_str.replace('.', '').replace(',', '.')
        return float(num_str)

    # Extrae nombre del remitente
    issuer_name_match = re.search(r'^(.*?)\n\s*GIRO:', transformed_text, re.DOTALL | re.MULTILINE)
    if issuer_name_match:
        data["issuer"]["name"] = issuer_name_match.group(1).strip().replace('\n', ' ')

    # Extrae RUT del remitente
    rut_match = re.search(r'R\.U\.T\.?:\s*([\d\.]+-\s*\d+)', transformed_text)
    if rut_match:
        data["issuer"]["rut"] = rut_match.group(1).replace(' ', '')

    # Extrae 'giro'
    giro_match = re.search(r'GIRO:\s*(.*?)\n(?:BLANCO|EMAIL|R\.U\.T\.:)', transformed_text, re.DOTALL)
    if giro_match:
        data["issuer"]["economic_activity"] = giro_match.group(1).strip().replace('\n', ' ')

    # Extrae direccion
    address_match = re.search(r'\n(BLANCO.*)', transformed_text)
    if address_match:
        data["issuer"]["address"] = address_match.group(1).strip()

    # Extrae email
    email_match = re.search(r'EMAIL\s*:\s*(\S+@\S+)', transformed_text)
    if email_match:
        data["issuer"]["email"] = email_match.group(1)

    # Extrae telefono
    phone_match = re.search(r'TELEFONO\s*:\s*((?:\d+\s*)+)', transformed_text, re.DOTALL)
    if phone_match:
        phone = phone_match.group(1)
        phone = ''.join(re.findall(r'\d+', phone))
        data["issuer"]["phone"] = phone


    # Extrae el tipo de factura
    invoice_type_match = re.search(r'\n(FACTURA ELECTRONICA)\n', transformed_text)
    if invoice_type_match:
        data["issuer"]["invoice_type"] = invoice_type_match.group(1)

    # Extrae el número de factura basado en el contexto
    invoice_number = None
    invoice_number_match = re.search(r'FACTURA ELECTRONICA\s*(.*?)\s*S\.I\.I\.\. - VALPARAISO', transformed_text, re.DOTALL)
    if invoice_number_match:
        between_text = invoice_number_match.group(1).strip()
        # Busca el primer número en el texto intermedio
        num_match = re.search(r'N[º2]?\s*(\d+)', between_text)
        if num_match:
            invoice_number = num_match.group(1).replace(' ', '')
            # Opcionalmente, corrige 'N2' a 'Nº' si es necesario
            invoice_number = invoice_number.replace('N2', 'Nº')
            data["issuer"]["invoice_number"] = invoice_number
        else:
            # Si no se encuentra, intenta extraer cualquier número
            num_match = re.search(r'(\d+)', between_text)
            if num_match:
                data["issuer"]["invoice_number"] = num_match.group(1)

    # Extrae fecha de emision
    issue_date_match = re.search(r'FECHA EMISION:\s*([0-9]{1,2}) DE (\w+) DEL (\d{4})', transformed_text)
    if issue_date_match:
        day = issue_date_match.group(1).zfill(2)  # Asegura que el día tenga dos dígitos
        month_name = issue_date_match.group(2).upper()
        year = issue_date_match.group(3)
        month = months.get(month_name, '00')  # Obtiene el número del mes; '00' si no se encuentra
        issue_date_formatted = f"{day}{month}{year}"
        data["issuer"]["issue_date"] = issue_date_formatted  # Almacena en 'data' principal


    # Extrae forma de pago
    pay_method_match = re.search(r'FORMA DE PAGO:\s*(.+)', transformed_text)
    if pay_method_match:
        data["pay_method"] = pay_method_match.group(1).strip()

    # Extrae la sección de los ítems entre los delimitadores "CODIGO DESCRIPCION.*?VALOR\s*(.*?)\s*FORMA DE PAGO"
    items_section_match = re.search(
        r'CODIGO DESCRIPCION.*?VALOR\s*(.*?)\s*FORMA DE PAGO:', 
        transformed_text, 
        re.DOTALL
    )
    if items_section_match:
        items_text = items_section_match.group(1).strip()
        item_lines = items_text.splitlines()
        for line in item_lines:
            # Extrae los detalles de cada ítem usando una expresión regular
            line = line.strip()
            if not line:
                continue
            line_regex = r'(?P<description>.*?)\s+(?P<quantity>\S+)\s+(?P<unit_price>[\d.,]+)\s+(?P<total_price>[\d.,]+)'
            item_match = re.match(line_regex, line)

            if item_match:
                 # Agrega el ítem al diccionario de datos
                item = {
                    'description': item_match.group('description').strip(),
                    'quantity': item_match.group('quantity').strip(),
                    'unit_price': parse_float(item_match.group('unit_price')),
                    'total_price': parse_float(item_match.group('total_price')),
                }
                data["items"].append(item)

    # Extrae subtotal
    subtotal_match = re.search(r'MONTO NETO \$\s*([\d.,]+)', transformed_text)
    if subtotal_match:
        data['subtotal'] = parse_float(subtotal_match.group(1))

    # Extrae impuesto
    tax_match = re.search(r'I\.V\.A\. 19% \$\s*([\d.,]+)', transformed_text)
    if tax_match:
        data['tax'] = parse_float(tax_match.group(1))

    # Extrae total
    total_match = re.search(r'TOTAL \$\s*([\d.,]+)', transformed_text)
    if total_match:
        data['total'] = parse_float(total_match.group(1))

     # Extrae datos del comprador
    buyer_section_match = re.search(
        r'SEÑOR\(ES\):\s*(.*?)\n(?:CONTACTO:|TIPO DE COMPRA:|CODIGO DESCRIPCION)', 
        transformed_text, 
        re.DOTALL
    )
    if buyer_section_match:
        buyer_section = buyer_section_match.group(1)

        # Extrae NOMBRE del comprador
        buyer_name_line = buyer_section.split('\n')[0].strip()
        data['buyer']['name'] = buyer_name_line

        # Extrae RUT del comprador
        buyer_rut_match = re.search(r'R\.U\.T\.:\s*([\d\.]+-\s*\d+)', buyer_section)
        if buyer_rut_match:
            data['buyer']['rut'] = buyer_rut_match.group(1).replace(' ', '')

        # Extrae GIRO del comprador
        buyer_giro_match = re.search(r'GIRO:\s*(.*)', buyer_section)
        if buyer_giro_match:
            data['buyer']['economic_activity'] = buyer_giro_match.group(1).strip()

        # Extrae DIRECCION del comprador
        buyer_address_match = re.search(r'DIRECCION:\s*(.*)', buyer_section)
        if buyer_address_match:
            data['buyer']['address'] = buyer_address_match.group(1).strip()

        # Extrae COMUNA del comprador
        buyer_comuna_match = re.search(r'COMUNA\s*(.*?)\s*CIUDAD:', buyer_section)
        if buyer_comuna_match:
            data['buyer']['commune'] = buyer_comuna_match.group(1).strip()


    print(transformed_text)
    
    print(json.dumps(data, indent=4, ensure_ascii=False))

    return data

def load(data, str_conn):
    """
    Carga los datos procesados en una base de datos (actualmente solo muestra los datos).
    
    Parámetros:
    - data: El diccionario con los datos procesados de la factura.
    - str_conn: La cadena de conexión a la base de datos (actualmente no utilizada).
    """
    print(f"PLACEHOLDER: data cargada")


def main():
    """
    Función principal que coordina las etapas de extracción, transformación y carga de datos.
    """
    str_conn = "string de conexión a la BD oracle"  # Placeholder para la cadena de conexión a la base de datos
    path_invoices = "docs/electronic_tickets/FACTURA451.pdf"  # Ruta del archivo PDF de la factura
     
    # Etapa de extracción: convierte el PDF a texto usando OCR
    extracted_text = extract(path_invoices)
    
    # Etapa de transformación: normaliza el texto y extrae los datos clave
    data = transform(extracted_text)
    
    # Etapa de carga: inserta o muestra los datos en la base de datos
    load(data, str_conn)

if __name__ == "__main__":
    main()