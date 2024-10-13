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

from etl.physical_tickets import main as fun_pt
from etl.electronic_tickets import main as fun_et
from etl.invoices_issued import main as fun_ii
from etl.invoices_received import main as fun_ir

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
        self.add_tab(notebook, "Facturas Recibidas", self.process_facturas_recibidas)
        self.add_tab(notebook, "Facturas Emitidas", self.process_facturas_emitidas)
        self.add_tab(notebook, "Boletas Físicas", self.process_boletas_fisicas)
        self.add_tab(notebook, "Boletas Electrónicas", self.process_boletas_electronicas)

        # Cargar configuraciones previas si existen
        self.config_data = self.load_config()

        # Variables para guardar rutas de carpetas
        self.facturas_recibidas_path = self.config_data.get("Facturas Recibidas", "")
        self.facturas_emitidas_path = self.config_data.get("Facturas Emitidas", "")
        self.boletas_fisicas_path = self.config_data.get("Boletas Físicas", "")
        self.boletas_electronicas_path = self.config_data.get("Boletas Electrónicas", "")

    def add_tab(self, notebook, title, command):
        # Crear un Frame para la pestaña
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=title)

        # Botón que ejecuta el proceso específico de cada pestaña
        process_button = tk.Button(frame, text=f"Procesar {title}", command=command)
        process_button.pack(pady=20)

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

    # Funciones independientes para procesar cada tipo de documento
    def process_facturas_recibidas(self):
        if not self.facturas_recibidas_path:
            messagebox.showwarning("Advertencia", "La carpeta para Facturas Recibidas no está configurada.")
        else:
            self.run_etl_process(self.facturas_recibidas_path, fun_ir, "Facturas Recibidas")

    def process_facturas_emitidas(self):
        if not self.facturas_emitidas_path:
            messagebox.showwarning("Advertencia", "La carpeta para Facturas Emitidas no está configurada.")
        else:
            self.run_etl_process(self.facturas_emitidas_path, fun_ii, "Facturas Emitidas")

    def process_boletas_fisicas(self):
        if not self.boletas_fisicas_path:
            messagebox.showwarning("Advertencia", "La carpeta para Boletas Físicas no está configurada.")
        else:
            self.run_etl_process(self.boletas_fisicas_path, fun_pt, "Boletas Físicas")

    def process_boletas_electronicas(self):
        if not self.boletas_electronicas_path:
            messagebox.showwarning("Advertencia", "La carpeta para Boletas Electrónicas no está configurada.")
        else:
            self.run_etl_process(self.boletas_electronicas_path, fun_et, "Boletas Electrónicas")

    def run_etl_process(self, path, etl_function, document_type):
        # Mostrar mensaje mientras se realiza el procesamiento
        try:
            messagebox.showinfo("Procesando", f"Procesando {document_type} en la carpeta: {path}")
            etl_function(path)
            messagebox.showinfo("Éxito", f"{document_type} procesadas exitosamente.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al procesar {document_type}:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HookedDocsApp(root)
    root.geometry("600x400")
    root.mainloop()
