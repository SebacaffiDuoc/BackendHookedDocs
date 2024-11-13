# HookedDocs - Procesamiento de Documentos

![Logo](assets/icon.png)  <!-- Si tienes un logo, puedes colocarlo aquí -->

## Descripción del Proyecto

**HookedDocs** es una herramienta desarrollada en Python para la gestión automatizada de documentos de facturación, incluyendo Facturas Recibidas, Facturas Emitidas, Boletas Físicas y Electrónicas. La aplicación se especializa en procesar documentos de diversos tipos mediante procesos ETL (Extracción, Transformación, y Carga) y ofrece una interfaz amigable para la actualización, eliminación y revisión de errores en los documentos procesados.

El objetivo principal de **HookedDocs** es simplificar y automatizar el manejo de documentos contables para pequeñas y medianas empresas, permitiendo un fácil acceso y edición de los datos a través de una interfaz gráfica.

## Características

- **Procesamiento de Documentos**: Capacidad para procesar facturas y boletas de diferentes tipos.
- **Logs de Errores**: Visualización de los errores durante el procesamiento en una pestaña dedicada.
- **Interfaz Moderna**: Utiliza `ttkthemes` para ofrecer una experiencia visual amigable y moderna.
- **Temas Personalizables**: Posibilidad de elegir entre varios temas visuales.
- **Splash Screen**: Pantalla de bienvenida antes de la carga del programa.
- **CRUD Completo**: Funcionalidades completas para Crear, Leer, Actualizar y Eliminar registros.

## Requisitos

- Python 3.10 o superior
- Dependencias Python:
  - `ttkthemes`
  - `tkinter`
  - `Pillow`
  - `PyInstaller` (para crear el ejecutable)
- Sistema Operativo:
  - Windows (Recomendado para el uso del ejecutable)

## Instalación y Uso

### Instalación

1. **Clonar el Repositorio**

   ```bash
   git clone https://github.com/tu_usuario/HookedDocs.git
   cd HookedDocs
   ```

2. **Instalar Dependencias**

   Se recomienda crear un entorno virtual antes de instalar las dependencias:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Para Linux/Mac
   venv\Scripts\activate     # Para Windows
   pip install -r requirements.txt
   ```

### Ejecutar la Aplicación

Para ejecutar la aplicación, simplemente ejecuta:

```bash
python main.py
```

### Crear un Ejecutable (Windows)

Si deseas crear un archivo ejecutable para Windows, usa PyInstaller como se describe en la sección anterior:

```bash
pyinstaller --onefile --windowed --icon=assets/icon.ico HookedDocs.spec
```

El archivo ejecutable se generará en la carpeta `dist/`.

## Uso de la Aplicación

1. **Splash Screen**: Al abrir la aplicación, se mostrará un splash durante unos segundos.
2. **Interfaz Principal**:
   - **Procesamiento de Documentos**: Selecciona el tipo de documento y usa los botones para procesar, actualizar o eliminar registros.
   - **Logs de Errores**: Los errores se mostrarán en una pestaña dedicada y se pueden revisar en cualquier momento.
3. **Configuración**:
   - **Seleccionar Carpetas**: Puedes configurar las carpetas donde se almacenan los documentos.
   - **Cambiar Tema**: Selecciona entre varios temas para personalizar la apariencia de la aplicación.

## Estructura del Proyecto

```
BackendHookedDocs/
│
├── main.py                # Script principal para ejecutar la aplicación
├── src/
│   ├── etl/
│   │   ├── physical_tickets.py
│   │   ├── electronic_tickets.py
│   │   ├── invoices_issued.py
│   │   └── invoices_received.py
│   └── core/
│       └── crud.py        # Funciones CRUD y de logs
├── assets/
│   ├── icon.ico           # Ícono de la aplicación
│   └── splash.png         # Imagen para el splash screen
├── requirements.txt       # Dependencias del proyecto
└── README.md              # Información sobre el proyecto
```

## Contribuir

Las contribuciones son siempre bienvenidas. Por favor, sigue los siguientes pasos para contribuir:

1. **Fork** este repositorio.
2. **Crea una rama** para tu característica (`git checkout -b feature/AmazingFeature`).
3. **Commit** tus cambios (`git commit -m 'Add some AmazingFeature'`).
4. **Push** a la rama (`git push origin feature/AmazingFeature`).
5. **Crea un Pull Request**.

## Licencia

Este proyecto está bajo la Licencia MIT. Para más detalles, consulta el archivo `LICENSE`.

## Contacto

Desarrollado por [Tu Nombre].

Correo: [tu_email@dominio.com]
