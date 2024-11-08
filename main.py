import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import json
import os
import sys
import ttkthemes

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

        # Cargar configuraciones previas si existen
        self.config_data = self.load_config()

        # Aplicar tema visual
        self.style = ttkthemes.ThemedStyle(self.root)
        self.available_themes = self.style.theme_names()
        self.current_theme = self.config_data.get("theme", "breeze")  # Cargar tema del config o usar "breeze" por defecto
        self.style.set_theme(self.current_theme)

        # Crear la barra de menú
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # Crear un menú de configuración
        config_menu = tk.Menu(menu_bar, tearoff=0)
        config_menu.add_command(label="Configuración de Carpetas", command=self.config_folders)
        config_menu.add_command(label="Seleccionar Tema", command=self.select_theme_window)
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
        process_button = ttk.Button(frame, text=f"Procesar {title}", command=lambda: self.process_documents(title))
        process_button.pack(pady=10)

        # Botón para actualizar facturas o boletas
        update_button = ttk.Button(frame, text=f"Actualizar {title}", command=lambda: self.open_update_window(title, functionality_number))
        update_button.pack(pady=10)

        # Botón para eliminar facturas o boletas
        delete_button = ttk.Button(frame, text=f"Eliminar {title}", command=lambda: self.delete_document(title, functionality_number))
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
            label = ttk.Label(config_window, text=f"{func}:")
            label.grid(row=index, column=0, padx=10, pady=5, sticky="w")

            entry = ttk.Entry(config_window, width=40)
            entry.grid(row=index, column=1, padx=10, pady=5)
            self.entries[func] = entry

            # Cargar valores previos si existen o asignar un valor vacío
            entry.insert(0, self.config_data.get(func, ""))

            button = ttk.Button(config_window, text="Seleccionar", command=lambda e=entry: self.select_folder(e))
            button.grid(row=index, column=2, padx=10, pady=5)

        # Botón para guardar configuraciones
        save_button = ttk.Button(config_window, text="Guardar", command=self.save_config)
        save_button.grid(row=len(functionalities), column=1, pady=20)

    def select_folder(self, entry):
        # Abrir diálogo para seleccionar la carpeta
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            entry.delete(0, tk.END)
            entry.insert(0, folder_selected)

    def save_config(self):
        # Recopilar datos de las entradas y guardarlos en un archivo JSON
        config_data = {
            "Facturas Recibidas": self.facturas_recibidas_path,
            "Facturas Emitidas": self.facturas_emitidas_path,
            "Boletas Físicas": self.boletas_fisicas_path,
            "Boletas Electrónicas": self.boletas_electronicas_path,
            "theme": self.current_theme  # Guardar el tema actual
        }

        with open("config.json", "w") as config_file:
            json.dump(config_data, config_file, indent=4)

        messagebox.showinfo("Guardado", "Las configuraciones se han guardado correctamente.")

    def load_config(self):
        # Cargar configuraciones previas si existe el archivo config.json
        if os.path.exists("config.json"):
            with open("config.json", "r") as config_file:
                return json.load(config_file)
        return {}
    
    def select_theme_window(self):
        # Ventana para seleccionar el tema
        theme_window = tk.Toplevel(self.root)
        theme_window.title("Seleccionar Tema Visual")
        theme_window.geometry("400x200")

        theme_label = ttk.Label(theme_window, text="Seleccione un tema:")
        theme_label.pack(pady=10)

        theme_combobox = ttk.Combobox(theme_window, values=self.available_themes)
        theme_combobox.set(self.current_theme)
        theme_combobox.pack(pady=10)

        apply_button = ttk.Button(theme_window, text="Aplicar", command=lambda: self.apply_theme(theme_combobox.get()))
        apply_button.pack(pady=10)

    def apply_theme(self, theme_name):
        if theme_name in self.available_themes:
            self.style.set_theme(theme_name)
            self.current_theme = theme_name
            self.config_data["theme"] = theme_name  # Guardar el tema actual en la configuración
            self.save_config()  # Guardar la configuración actualizada
            messagebox.showinfo("Tema Aplicado", f"Tema '{theme_name}' aplicado exitosamente.")
        else:
            messagebox.showwarning("Error", f"El tema '{theme_name}' no está disponible.")

    def open_update_window(self, document_type, functionality_number):
        self.current_document_type = document_type
        self.current_functionality_number = functionality_number
        update_window = tk.Toplevel(self.root)
        update_window.title(f"Actualizar {document_type}")
        update_window.geometry("600x800")

        search_label = ttk.Label(update_window, text="Número de Factura o Boleta:")
        search_label.pack(pady=5)

        search_entry = ttk.Entry(update_window)
        search_entry.pack(pady=5)

        search_button = ttk.Button(update_window, text="Buscar", command=lambda: self.search_invoice(search_entry))
        search_button.pack(pady=5)

        self.invoice_data_entries = {}

        # Definir los campos específicos según la funcionalidad
        fields = []
        if functionality_number == 1:  # Facturas Recibidas
            fields = ["Número Factura", "Nombre Proveedor", "RUT Proveedor", "Subtotal", "Precio Total Items", "IVA", "Total", "Método de Pago"]
        elif functionality_number == 2:  # Facturas Emitidas
            fields = ["Número Factura", "Nombre Comprador", "RUT Comprador", "RUT Proveedor", "Tipo de Factura", "Subtotal", "Precio Total Items", "IVA", "Total", "Método de Pago"]
        elif functionality_number == 3:  # Boletas Físicas
            fields = ["Folio", "RUT Vendedor", "Sucursal", "Fecha", "Neto", "IVA", "Total"]
        elif functionality_number == 4:  # Boletas Electrónicas
            fields = ["Folio", "Tipo Documento", "Emisión", "Monto Neto", "Monto Exento", "Monto IVA", "Monto Total"]

        for field in fields:
            label = ttk.Label(update_window, text=field)
            label.pack(pady=2)

            entry = ttk.Entry(update_window, width=50)
            entry.pack(pady=2)
            self.invoice_data_entries[field] = entry

        update_button = ttk.Button(update_window, text="Actualizar", command=self.update_invoice)
        update_button.pack(pady=20)

    def run_etl_process(self, path, etl_function, document_type):
        # Mostrar mensaje mientras se realiza el procesamiento
        try:
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Procesando")
            progress_label = ttk.Label(progress_window, text=f"Procesando {document_type} en la carpeta: {path}")
            progress_label.pack(pady=10)

            progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
            progress_bar.pack(pady=10, padx=20, fill='x')
            progress_bar.start()

            self.root.update()
            etl_function(path)

            progress_bar.stop()
            progress_window.destroy()

            messagebox.showinfo("Éxito", f"{document_type} procesadas exitosamente.")
        except Exception as e:
            print(f"Error al procesar {document_type}: {e}")
            messagebox.showerror("Error", f"Ocurrió un error al procesar {document_type}:{str(e)}")

    def process_documents(self, document_type):
        path = None
        etl_function = None

        if document_type == "Facturas Recibidas":
            path = self.facturas_recibidas_path
            etl_function = fun_ir
        elif document_type == "Facturas Emitidas":
            path = self.facturas_emitidas_path
            etl_function = fun_ii
        elif document_type == "Boletas Físicas":
            path = self.boletas_fisicas_path
            etl_function = fun_pt
        elif document_type == "Boletas Electrónicas":
            path = self.boletas_electronicas_path
            etl_function = fun_et

        if not path:
            messagebox.showwarning("Advertencia", f"La carpeta para {document_type} no está configurada.")
            return

        self.run_etl_process(path, etl_function, document_type)

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
                        'Número Factura': 'invoice_number',
                        'Nombre Proveedor': 'issuer_name',
                        'RUT Proveedor': 'issuer_rut',
                        'Subtotal': 'subtotal',
                        'Precio Total Items': 'item_total_price',
                        'IVA': 'tax',
                        'Total': 'total',
                        'Método de Pago': 'pay_method'
                    }
                elif self.current_functionality_number == 2:
                    key_mapping = {
                        'Número Factura': 'invoice_number',
                        'Nombre Comprador': 'buyer_name',
                        'RUT Comprador': 'buyer_rut',
                        'RUT Proveedor': 'issuer_rut',
                        'Tipo de Factura': 'invoice_type',
                        'Subtotal': 'subtotal',
                        'Precio Total Items': 'item_total_price',
                        'IVA': 'tax',
                        'Total': 'total',
                        'Método de Pago': 'pay_method'
                    }
                elif self.current_functionality_number == 3:
                    key_mapping = {
                        'Folio': 'folio',
                        'Neto': 'neto',
                        'IVA': 'iva',
                        'Total': 'total',
                        'Fecha': 'fecha',
                        'RUT Vendedor': 'rut_vendedor',
                        'Sucursal': 'sucursal'  
                    }
                elif self.current_functionality_number == 4:
                    key_mapping = {
                        'Tipo Documento': 'tipo_documento',
                        'Folio': 'folio',
                        'Emisión': 'emision',
                        'Monto Neto': 'monto_neto',
                        'Monto Exento': 'monto_exento',
                        'Monto IVA': 'monto_iva',
                        'Monto Total': 'monto_total'
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
                        
                    # Asegurarse de que value es una cadena y no None
                    if value is None:
                        value = ""
                    else:
                        value = str(value)
                    entry.insert(0, value)
            else:
                messagebox.showinfo("Información", "Documento no encontrado.")
                self.clear_invoice_entries()
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al buscar el documento: {str(e)}")
            self.clear_invoice_entries()

    def clear_invoice_entries(self):
        # Limpiar todos los campos de entrada en el formulario
        for entry in self.invoice_data_entries.values():
            entry.delete(0, tk.END)

    def update_invoice(self):
        # Obtener los datos actualizados desde la interfaz gráfica
        updated_data = {key.lower().replace(" ", "_"): entry.get() for key, entry in self.invoice_data_entries.items()}

        # Mapeo de claves ajustado para coincidir con updated_data
        if self.current_functionality_number == 1:
            key_mapping = {
                'número_factura': 'invoice_number',
                'nombre_proveedor': 'issuer_name',
                'rut_proveedor': 'issuer_rut',
                'subtotal': 'subtotal',
                'precio_total_items': 'item_total_price',
                'iva': 'tax',
                'total': 'total',
                'método_de_pago': 'pay_method'
            }
        elif self.current_functionality_number == 2:
            key_mapping = {
                'número_factura': 'invoice_number',
                'nombre_comprador': 'buyer_name',
                'rut_comprador': 'buyer_rut',
                'rut_proveedor': 'issuer_rut',
                'tipo_de_factura': 'invoice_type',
                'subtotal': 'subtotal',
                'precio_total_items': 'item_total_price',
                'iva': 'tax',
                'total': 'total',
                'método_de_pago': 'pay_method'
            }
        elif self.current_functionality_number == 3:
            # mapeo para boletas físicas
            key_mapping = {
                'folio': 'folio',
                'neto': 'neto',
                'iva': 'iva',
                'total': 'total',
                'fecha': 'fecha',
                'rut_vendedor': 'rut_vendedor',
                'sucursal': 'sucursal'
            }
        elif self.current_functionality_number == 4:
            # mapeo para boletas electrónicas
            key_mapping = {
                'tipo_documento': 'tipo_documento',
                'folio': 'folio',
                'emisión': 'emision',
                'monto_neto': 'monto_neto',
                'monto_exento': 'monto_exento',
                'monto_iva': 'monto_iva',
                'monto_total': 'monto_total'
            }
        else:
            messagebox.showerror("Error", "Funcionalidad no reconocida.")
            return

        # Aplicar el mapeo a los datos actualizados
        updated_data_mapped = {key_mapping.get(k, k): v for k, v in updated_data.items()}

        # Obtener el número de factura o folio
        if self.current_functionality_number in [1, 2]:
            invoice_number = updated_data_mapped.get('invoice_number')
        elif self.current_functionality_number == 3:
            invoice_number = updated_data_mapped.get('folio')
        elif self.current_functionality_number == 4:
            invoice_number = updated_data_mapped.get('folio')
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
        delete_window.geometry("300x150")

        delete_label = ttk.Label(delete_window, text="Número de Factura o Boleta a eliminar:")
        delete_label.pack(pady=5)

        delete_entry = ttk.Entry(delete_window)
        delete_entry.pack(pady=5)

        # Cambiar el botón para que pase delete_entry como objeto
        delete_button = ttk.Button(delete_window, text="Eliminar", command=lambda: self.perform_delete(functionality_number, delete_entry))
        delete_button.pack(pady=10)


    def perform_delete(self, functionality_number, delete_entry):
        # Obtener el valor del campo de entrada
        invoice_number = delete_entry.get()
        if not invoice_number:
            messagebox.showwarning("Advertencia", "Ingrese el número de factura o boleta a eliminar.")
            return

        try:
            # Eliminar la factura o boleta en la BD
            delete_invoice(functionality_number, invoice_number)
            messagebox.showinfo("Éxito", "Documento eliminado correctamente.")
            # Limpiar el campo de entrada del número de DTE
            delete_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al eliminar el documento: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = HookedDocsApp(root)
    root.mainloop()
