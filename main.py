import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import json
import os
import sys

route = os.path.abspath(__file__)
index_route = route.find("BackendHookedDocs")
local_path = route[:index_route + len("BackendHookedDocs")]
global_route = os.path.join(local_path, "src")

sys.path.append(global_route)

from src.etl.physical_tickets import main as fun_pt
from src.etl.electronic_tickets import main as fun_et
from src.etl.invoices_issued import main as fun_ii
from src.etl.invoices_received import main as fun_ir
from src.core.crud import read_select_invoice, update_selected_invoice, delete_invoice

class HookedDocsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HookedDocs - Procesamiento de Documentos")

        # Crear la barra de menú
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # Crear un menú de configuración
        config_menu = tk.Menu(menu_bar, tearoff=0)
        config_menu.add_command(label="Configuración de Carpetas", command=self.config_folders)
        menu_bar.add_cascade(label="Configuración", menu=config_menu)

        # Crear el Notebook para las pestañas de funcionalidades
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill='both')

        # Pestaña para cada funcionalidad
        self.facturas_recibidas_tab = self.add_tab(notebook, "Facturas Recibidas", 1)
        self.facturas_emitidas_tab = self.add_tab(notebook, "Facturas Emitidas", 2)
        self.boletas_fisicas_tab = self.add_tab(notebook, "Boletas Físicas", 3)
        self.boletas_electronicas_tab = self.add_tab(notebook, "Boletas Electrónicas", 4)

        # Cargar configuraciones previas si existen
        self.config_data = self.load_config()

        # Variables para guardar rutas de carpetas
        self.facturas_recibidas_path = self.config_data.get("Facturas Recibidas", "")
        self.facturas_emitidas_path = self.config_data.get("Facturas Emitidas", "")
        self.boletas_fisicas_path = self.config_data.get("Boletas Físicas", "")
        self.boletas_electronicas_path = self.config_data.get("Boletas Electrónicas", "")

        # Variable para almacenar el tipo de documento actual
        self.current_document_type = None
        self.current_functionality_number = None

    def add_tab(self, notebook, title, functionality_number):
        # Crear un Frame para la pestaña
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=title)

        # Botón que ejecuta el proceso específico de cada pestaña
        process_button = tk.Button(frame, text=f"Procesar {title}", command=lambda: self.process_documents(title))
        process_button.pack(pady=10)

        # Botón para actualizar facturas o boletas
        update_button = tk.Button(frame, text=f"Actualizar {title}", command=lambda: self.open_update_window(title, functionality_number))
        update_button.pack(pady=10)

        # Botón para eliminar facturas o boletas
        delete_button = tk.Button(frame, text=f"Eliminar {title}", command=lambda: self.delete_document(title, functionality_number))
        delete_button.pack(pady=10)

        return frame

    def config_folders(self):
        # Ventana de configuración para seleccionar carpetas
        config_window = tk.Toplevel(self.root)
        config_window.title("Configuración de Carpetas")
        config_window.geometry("630x230")

        self.entries = {}

        # Lista de funcionalidades para crear la configuración de cada carpeta
        functionalities = ["Facturas Recibidas", "Facturas Emitidas", "Boletas Físicas", "Boletas Electrónicas"]

        for index, func in enumerate(functionalities):
            label = tk.Label(config_window, text=f"{func}:")
            label.grid(row=index, column=0, padx=10, pady=5, sticky="w")

            entry = tk.Entry(config_window, width=40)
            entry.grid(row=index, column=1, padx=10, pady=5)
            self.entries[func] = entry

            # Cargar valores previos si existen o asignar un valor vacío
            entry.insert(0, self.config_data.get(func, ""))

            button = tk.Button(config_window, text="Seleccionar", command=lambda e=entry: self.select_folder(e))
            button.grid(row=index, column=2, padx=10, pady=5)

        # Botón para guardar configuraciones
        save_button = tk.Button(config_window, text="Guardar", command=self.save_config)
        save_button.grid(row=len(functionalities), column=1, pady=20)

    def select_folder(self, entry):
        # Abrir diálogo para seleccionar la carpeta
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            entry.delete(0, tk.END)
            entry.insert(0, folder_selected)

    def save_config(self):
        # Recopilar datos de las entradas y guardarlos en un archivo JSON
        config_data = {func: entry.get() for func, entry in self.entries.items()}

        with open("config.json", "w") as config_file:
            json.dump(config_data, config_file, indent=4)

        # Actualizar las variables de rutas
        self.facturas_recibidas_path = config_data.get("Facturas Recibidas", "")
        self.facturas_emitidas_path = config_data.get("Facturas Emitidas", "")
        self.boletas_fisicas_path = config_data.get("Boletas Físicas", "")
        self.boletas_electronicas_path = config_data.get("Boletas Electrónicas", "")

        messagebox.showinfo("Guardado", "Las configuraciones se han guardado correctamente.")

    def load_config(self):
        # Cargar configuraciones previas si existe el archivo config.json
        if os.path.exists("config.json"):
            with open("config.json", "r") as config_file:
                return json.load(config_file)
        return {}

    def open_update_window(self, document_type, functionality_number):
        self.current_document_type = document_type
        self.current_functionality_number = functionality_number
        update_window = tk.Toplevel(self.root)
        update_window.title(f"Actualizar {document_type}")
        update_window.geometry("600x650")

        search_label = tk.Label(update_window, text="Número de Factura o Boleta:")
        search_label.pack(pady=5)

        search_entry = tk.Entry(update_window)
        search_entry.pack(pady=5)

        search_button = tk.Button(update_window, text="Buscar", command=lambda: self.search_invoice(search_entry))
        search_button.pack(pady=5)

        self.invoice_data_entries = {}

        # Definir los campos específicos según la funcionalidad
        fields = []
        if functionality_number == 1:  # Facturas Recibidas
            fields = ["Número DTE", "Fecha de Emisión", "Subtotal", "IVA", "Total", "Forma de Pago", "Emisor", "Dirección"]
        elif functionality_number == 2:  # Facturas Emitidas
            fields = ["Número DTE", "Fecha de Emisión", "Subtotal", "IVA", "Total", "Forma de Pago", "Cliente", "Dirección"]
        elif functionality_number == 3:  # Boletas Físicas
            fields = ["Folio", "Neto", "IVA", "Total", "Fecha", "RUT Vendedor", "Sucursal"]
        elif functionality_number == 4:  # Boletas Electrónicas
            fields = ["Tipo Documento", "Folio", "Emisión", "Monto Neto", "Monto Exento", "Monto IVA", "Monto Total"]

        for field in fields:
            label = tk.Label(update_window, text=field)
            label.pack(pady=2)

            entry = tk.Entry(update_window, width=50)
            entry.pack(pady=2)
            self.invoice_data_entries[field] = entry

        update_button = tk.Button(update_window, text="Actualizar", command=self.update_invoice)
        update_button.pack(pady=20)

    def search_invoice(self, search_entry):
        invoice_number = search_entry.get()
        if not invoice_number:
            messagebox.showwarning("Advertencia", "Ingrese el número de factura o boleta a buscar.")
            return

        try:
            # Buscar la factura o boleta en la BD
            invoices = read_select_invoice(invoice_number, self.current_functionality_number)
            if invoices:
                # Tomar el primer resultado (asumiendo que hay solo uno)
                invoice_data = invoices[0]

                # Crear un mapeo entre los nombres de los campos de la GUI y las claves del diccionario
                if self.current_functionality_number == 1:
                    key_mapping = {
                        'Número DTE': 'INVOICE_NUMBER',
                        'Fecha de Emisión': 'ISSUE_DATE',
                        'Subtotal': 'SUBTOTAL',
                        'IVA': 'TAX',
                        'Total': 'TOTAL',
                        'Forma de Pago': 'PAY_METHOD',
                        'Emisor': 'ISSUER_NAME',
                        'Dirección': 'ISSUER_ADDRESS'
                    }
                elif self.current_functionality_number == 2:
                    key_mapping = {
                        'Número DTE': 'INVOICE_NUMBER',
                        'Fecha de Emisión': 'ISSUE_DATE',
                        'Subtotal': 'SUBTOTAL',
                        'IVA': 'TAX',
                        'Total': 'TOTAL',
                        'Forma de Pago': 'PAY_METHOD',
                        'Cliente': 'ISSUER_NAME',
                        'Dirección': 'ISSUER_ADDRESS'
                    }
                elif self.current_functionality_number == 3:
                    key_mapping = {
                        'Folio': 'FOLIO',
                        'Neto': 'NETO',
                        'IVA': 'IVA',
                        'Total': 'TOTAL',
                        'Fecha': 'FECHA',
                        'RUT Vendedor': 'RUT_VENDEDOR',
                        'Sucursal': 'SUCURSAL'  
                    }
                elif self.current_functionality_number == 4:
                    key_mapping = {
                        'Tipo Documento': 'TIPO_DOCUMENTO',
                        'Folio': 'FOLIO',
                        'Emisión': 'EMISION',
                        'Monto Neto': 'MONTO_NETO',
                        'Monto Exento': 'MONTO_EXENTO',
                        'Monto IVA': 'MONTO_IVA',
                        'Monto Total': 'MONTO_TOTAL'
                    }
                else:
                    key_mapping = {}

                # Rellenar los campos con los datos de la factura o boleta
                for gui_field_name, entry in self.invoice_data_entries.items():
                    entry.delete(0, tk.END)
                    # Obtener la clave correspondiente en el diccionario invoice_data
                    data_key = key_mapping.get(gui_field_name)
                    if data_key:
                        value = invoice_data.get(data_key, "")
                    else:
                        value = ""
                    entry.insert(0, value)
            else:
                messagebox.showinfo("Información", "Documento no encontrado.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al buscar el documento: {str(e)}")

    def update_invoice(self):
        # Obtener los datos actualizados desde la interfaz gráfica
        updated_data = {key.lower().replace(" ", "_"): entry.get() for key, entry in self.invoice_data_entries.items()}

        # Mapeo de claves si es necesario
        if self.current_functionality_number == 1:
            # Mapeo para facturas recibidas/emitidas
            key_mapping = {
                'Número DTE': 'INVOICE_NUMBER',
                'Fecha de Emisión': 'ISSUE_DATE',
                'Subtotal': 'SUBTOTAL',
                'IVA': 'TAX',
                'Total': 'TOTAL',
                'Forma de Pago': 'PAY_METHOD',
                'Emisor': 'ISSUER_NAME',
                'Dirección': 'ISSUER_ADDRESS'
            }
        elif self.current_functionality_number == 2:
            key_mapping = {
                'Número DTE': 'INVOICE_NUMBER',
                'Fecha de Emisión': 'ISSUE_DATE',
                'Subtotal': 'SUBTOTAL',
                'IVA': 'TAX',
                'Total': 'TOTAL',
                'Forma de Pago': 'PAY_METHOD',
                'Cliente': 'ISSUER_NAME',
                'Dirección': 'ISSUER_ADDRESS'
            }
        elif self.current_functionality_number == 3:
            # Mapeo para boletas físicas
            key_mapping = {
                'folio': 'FOLIO',
                'neto': 'NETO',
                'iva': 'IVA',
                'total': 'TOTAL',
                'fecha': 'FECHA',
                'rut_vendedor': 'RUT_VENDEDOR',
                'sucursal': 'SUCURSAL'
            }
        elif self.current_functionality_number == 4:
            # Mapeo para boletas electrónicas
            key_mapping = {
                'tipo_de_documento': 'TIPO_DOCUMENTO',
                'folio': 'FOLIO',
                'emisión': 'EMISION',
                'monto_neto': 'MONTO_NETO',
                'monto_exento': 'MONTO_EXENTO',
                'monto_iva': 'MONTO_IVA',
                'monto_total': 'MONTO_TOTAL'
            }
        else:
            messagebox.showerror("Error", "Funcionalidad no reconocida.")
            return

        # Aplicar el mapeo a los datos actualizados
        updated_data_mapped = {key_mapping.get(k, k): v for k, v in updated_data.items()}

        # Obtener el número de factura o folio
        if self.current_functionality_number in [1, 2]:
            invoice_number = updated_data_mapped.get('INVOICE_NUMBER')
        elif self.current_functionality_number in [3, 4]:
            invoice_number = updated_data_mapped.get('FOLIO')
        else:
            messagebox.showerror("Error", "Funcionalidad no reconocida.")
            return

        if not invoice_number:
            messagebox.showwarning("Advertencia", "El número de factura o folio no está especificado.")
            return

        try:
            # Actualizar la factura o boleta en la BD
            update_selected_invoice(invoice_number, updated_data_mapped, self.current_functionality_number)
            messagebox.showinfo("Éxito", "Documento actualizado correctamente.")
        except ValueError as ve:
            messagebox.showerror("Error", str(ve))
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al actualizar el documento: {str(e)}")

    def delete_document(self, document_type, functionality_number):
        delete_window = tk.Toplevel(self.root)
        delete_window.title(f"Eliminar {document_type}")
        delete_window.geometry("400x200")

        delete_label = tk.Label(delete_window, text="Número de Factura o Boleta a eliminar:")
        delete_label.pack(pady=5)

        delete_entry = tk.Entry(delete_window)
        delete_entry.pack(pady=5)

        delete_button = tk.Button(delete_window, text="Eliminar", command=lambda: self.perform_delete(functionality_number, delete_entry.get()))
        delete_button.pack(pady=10)

    def perform_delete(self, functionality_number, invoice_number):
        if not invoice_number:
            messagebox.showwarning("Advertencia", "Ingrese el número de factura o boleta a eliminar.")
            return

        try:
            # Eliminar la factura o boleta en la BD
            delete_invoice(functionality_number, invoice_number)
            messagebox.showinfo("Éxito", "Documento eliminado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al eliminar el documento: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HookedDocsApp(root)
    root.mainloop()
