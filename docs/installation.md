# Instalación

Pasos para dejar el proyecto funcionando partiendo de una clonación limpia del repositorio.

## 1. Pre-requisitos

| Pre-requisito      | Detalle                                             |
| ------------------ | --------------------------------------------------- |
| Python             | 3.12 (versión fijada en `.python-version`)          |
| Git                | cualquier versión vigente                           |
| AWS CLI            | v2, con credenciales y región configuradas          |
| Navegador/terminal | para las corridas de los tres programas aplicativos |

Además, completá la instalación y configuración de pre-requisitos indicada en la nota de aplicación
_"IS2_NAPP_Arquitectura AWS Python"_ antes de ejecutar cualquier desarrollo. Esa nota provee las
credenciales AWS y las tablas `CorporateData` y `CorporateLog` ya creadas.

## 2. Clonar el repositorio

```sh
git clone git@github.com:MoutSantiago/ing2_tpfi.git
cd ing2_tpfi
```

## 3. Ambiente virtual

Crear el ambiente virtual con la versión de Python del proyecto:

```sh
python -m venv .venv
source .venv/bin/activate
```

En Windows (PowerShell o CMD):

```powershell
.venv\Scripts\activate
```

Verificar que el ambiente quedó activo:

```sh
python --version   # debe responder Python 3.12.x
```

## 4. Instalar dependencias

Todas las dependencias (runtime, testing, lint y documentación) están pineadas en `requirements.txt`:

```sh
pip install --upgrade pip
pip install -r requirements.txt
```

Para actualizar el archivo de dependencias después de incorporar una librería:

```sh
pip freeze > requirements.txt
```

## 5. Configurar el entorno

### 5.1 Credenciales AWS

Las credenciales se resuelven con la cadena estándar de `boto3`, por lo que alcanza con:

```sh
aws configure
```

Ingresar `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` y `AWS_DEFAULT_REGION` (la región donde están
las tablas).

### 5.2 Tablas requeridas

Las tablas `CorporateData` y `CorporateLog` deben existir en DynamoDB **antes** de ejecutar los
programas. No se crean automáticamente.

## 6. Verificar la instalación

### 6.1 Chequeo de librerías y credenciales

El script de diagnóstico provisto por la cátedra valida `boto3`, las credenciales y el acceso a ambas
tablas:

```sh
python scripts/IS2_TPFI_test.py
```

Si termina con `Completed successfully`, el entorno está correctamente configurado.

### 6.2 Carga de datos de prueba (opcional)

```sh
python scripts/IS2_TPFI_insert.py
python scripts/IS2_TPFI_demo.py
```

### 6.3 Suite de tests

```sh
pytest
```

Los tests usan `moto` para emular DynamoDB, por lo que pueden ejecutarse sin tocar las tablas reales.
Para el detalle de los comandos de calidad ver [Comandos de desarrollo](development.md).

## 7. Instalación verificada

El proyecto queda operativo cuando:

- `python --version` responde 3.12 dentro del ambiente virtual.
- `python scripts/IS2_TPFI_test.py` imprime `Completed successfully`.
- `pytest` termina sin errores.

## Problemas frecuentes

**`ModuleNotFoundError: No module named 'boto3'`**
El ambiente virtual no está activo o las dependencias no se instalaron. Repetir los pasos 3 y 4.

**`NoCredentialsError` / `Could not connect to the endpoint URL`**
Faltan credenciales o región. Verificar con `aws sts get-caller-identity` y repetir `aws configure`.

**`ResourceNotFoundException: Requested resource not found`**
La tabla consultada no existe o el nombre no coincide exactamente. Confirmar los nombres
`CorporateData` y `CorporateLog`.

**`pyright` reporta `Import "boto3" could not be resolved`**
Pyright no detecta el intérprete del ambiente virtual. Ejecutarlo con
`pyright --pythonpath .venv/bin/python`.
