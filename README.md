# Fishing Store Backend

## Descripción

Este proyecto es el backend para la tienda de artículos de pesca, diseñado para automatizar la extracción de datos de facturas y boletas utilizando OCR, realizar un proceso ETL con la data extraída e insertarla en una base de datos PostgreSQL. La información almacenada luego se utilizará para generar reportes y análisis en Power BI.

## Tecnologías

- **FastAPI**: Framework web moderno, rápido (de alto rendimiento), fácil de usar y ligero para Python.
- **Docker**: Contenedores para asegurar la portabilidad y fácil despliegue de la aplicación.
- **OCR**: Reconocimiento óptico de caracteres para la extracción de texto desde imágenes.
- **PostgreSQL**: Base de datos relacional utilizada para almacenar la información extraída.
- **Power BI**: Herramienta de inteligencia de negocios para la visualización de datos y generación de informes.

## Estructura del Proyecto

fishing-store-backend/
│
├── src/
│ ├── api/ # Controladores y rutas de FastAPI
│ │ └── ocr_api.py
│ ├── core/ # Configuraciones y dependencias principales
│ │ └── database.py
│ ├── models/ # Definición de modelos de datos
│ │ └── user.py
│ ├── services/ # Lógica de negocio, incluyendo OCR y ETL
│ ├── ocr/ # Código relacionado con la extracción de texto OCR
│ │ └── ocr_reader.py
│ └── main.py # Archivo principal para iniciar la aplicación
│
├── venv/ # Entorno virtual de Python
├── .gitignore # Archivos y carpetas ignorados por Git
└── requirements.txt # Dependencias del proyecto


## Instalación

### Requisitos Previos

- **Python 3.8+**
- **Docker** instalado y corriendo en tu máquina.

### Pasos para Configurar el Entorno

1. Clona el repositorio:
   git clone https://github.com/SebacaffiDuoc/BackendHookedDocs.git
   cd BackendHookedDocs
