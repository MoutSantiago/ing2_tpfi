# Instalación

## Pre-requisitos

Asegúrese de haber completado la instalación y configuración de pre-requisitos según lo indicado en la nota de aplicación "IS2_NAPP_Arquitectura AWS Python" antes de ejecutar cualquier desarrollo.

## Ambiente virtual

Crear y activar el ambiente virtual Python:

```sh
python -m venv .venv
source .venv/bin/activate
```

Instalar dependencias:

```sh
pip install -r requirements.txt
```

## Configuración

Copiar el archivo de variables de entorno:

```sh
cp .env.example .env
```

Definir las credenciales y endpoint de AWS (DynamoDB) en `.env`.

Las tablas `CorporateData` y `CorporateLog` deben existir previamente en AWS DynamoDB antes de ejecutar los programas.