# Ingeniería de Software II — Guía Final de Examen

**Trabajo Práctico Integrador: Patrones Proxy, Singleton, Observer e Iterator en AWS**
*Versión ampliada*

> **ACLARACIÓN**
> Cómo leer esta guía: el texto normal es el contenido de la guía original. Todo lo que está en un recuadro como éste (un bloque con el rótulo **ACLARACIÓN**) es un agregado o una corrección. Cuando una aclaración corrige algo que decía la guía original, lo indica expresamente.

---

## 1. CONCEPTOS FUNDAMENTALES EXPLICADOS SIMPLE

Para defender tu trabajo final con soltura ante el tribunal, es indispensable dominar la terminología técnica reduciéndola a conceptos cotidianos:

| Término técnico | Explicación sencilla para el examen |
|---|---|
| **Entorno virtual (venv)** | Caja de aislamiento donde residen las librerías específicas del proyecto sin interferir con el sistema operativo. |
| **AWS CLI & Boto3** | Herramienta de consola (AWS CLI) y librería de Python (Boto3) que traducen tus peticiones a comandos nativos de AWS en la nube. |
| **DynamoDB** | Base de datos NoSQL de alta velocidad en AWS que guarda la información como registros de tipo documento (JSON). |
| **Socket TCP** | Canal de comunicación bidireccional permanente ("cable de red virtual") entre cliente y servidor. |
| **DAO (Data Access Object)** | Patrón estructural que encapsula y aísla el acceso directo a la base de datos del resto de la aplicación. |

> **ACLARACIÓN**
> Más términos que conviene saber explicar (no estaban en la guía original):

| Término | Qué es, en simple |
|---|---|
| **Cliente / servidor** | El servidor es un programa que queda encendido esperando pedidos; el cliente es el que hace el pedido y espera la respuesta. |
| **Puerto (8080)** | El "número de puerta" por donde entran las conexiones al servidor. Un mismo equipo puede tener muchos puertos. |
| **localhost** | Significa "esta misma computadora". |
| **JSON** | Formato de texto para enviar datos, por ejemplo `{"ID": "X", "ACTION": "get"}`. |
| **Thread (hilo)** | Permite que el servidor atienda a varios clientes a la vez: cada cliente recibe su propio hilo. |
| **Lock (candado)** | Evita que dos hilos modifiquen lo mismo al mismo tiempo; deja pasar de a uno. |
| **UUID** | Número que identifica algo. Acá `uuid.getnode()` identifica tu CPU y `uuid4()` genera un número al azar por sesión. |
| **Interfaz / clase abstracta (ABC)** | "Molde" que obliga a las clases que lo heredan a tener ciertos métodos, sin implementarlos. |
| **Auditoría (log)** | Registro de quién hizo qué y cuándo. En el proyecto es la tabla CorporateLog. |
| **Argumento / opción (flag)** | Letra que se agrega al ejecutar un programa para configurarlo, como `-p 8080`. |
| **Excepción** | Aviso de error que el programa captura para no romperse y responder de forma ordenada. |

---

## 2. ARQUITECTURA DE LOS 4 PATRONES IMPLEMENTADOS

### PATRÓN 1 — Singleton

Garantiza que exista una única instancia global de acceso a la base de datos (CorporateDataDAO y CorporateLogDAO), evitando reabrir innecesariamente la conexión a AWS DynamoDB.

> **ACLARACIÓN**
> **Corrección:** la guía original decía "evitando reaperturas de sockets o conexiones". Lo que el Singleton cuida es la **conexión con DynamoDB**, no los sockets TCP.
>
> Cómo está hecho: el método `get_instance()` crea la instancia la primera vez y después devuelve siempre la misma. Usa un **Lock** para que dos hilos no creen dos instancias a la vez, y el constructor lanza `RuntimeError` si se lo llama directamente.

### PATRÓN 2 — Proxy

Funciona como un intermediario o "filtro de seguridad". Intercepta las llamadas antes de tocar la base de datos para registrar la pista de auditoría en la tabla CorporateLog.

> **ACLARACIÓN**
> **Corrección:** la guía original agregaba "y validar requerimientos". Esa validación (que existan UUID, ACTION, ID y los campos necesarios) la hace el **servidor** (`server.py`, método `_validate`), no el Proxy.
>
> Qué hace realmente el Proxy: **primero audita** en CorporateLog y **después opera** sobre los datos. Si la auditoría falla, la operación no se ejecuta: ningún dato cambia sin quedar registrado. En un `set`, además, avisa a los suscriptores.
>
> El Proxy y el DAO implementan la **misma interfaz** (`CorporateDataInterface`), por eso el servidor no sabe ni necesita saber con cuál de los dos habla.

### PATRÓN 3 — Observer

Mecanismo de suscripción en tiempo real. Cuando una actualización (set) modifica los datos, el servidor notifica automáticamente a todos los ObserverClient suscriptos vía TCP.

> **ACLARACIÓN**
> Quién es quién: el **Publisher** es `SubscriptionManager` y cada observer del servidor es un `ClientObserver` (guarda el socket del cliente suscripto). El programa **ObserverClient** es el cliente remoto que recibe los avisos; el patrón en sí vive en el servidor.
>
> Solo el `set` genera avisos; `get` y `list` no. Si un suscriptor se cae, el servidor lo da de baja y sigue notificando a los demás.

### PATRÓN 4 — Iterator

Proporciona un mecanismo secuencial para recorrer los registros de la tabla CorporateData sin exponer la estructura ni los detalles internos de las consultas en DynamoDB.

> **ACLARACIÓN**
> A diferencia de los otros programas, **IteratorCorporateData no usa el servidor**: accede directo a DynamoDB con boto3.
>
> Hay dos iteradores: `SingleRecordIterator` (cuando se usa `--id`) y `TableScanIterator` (recorre toda la tabla página por página). Ambos tienen los métodos `has_more()` (¿quedan registros?) y `next()` (dame el siguiente). Si la tabla está vacía, devuelve `{"id": null}`.

> **ACLARACIÓN — Mapa general del sistema:**

```
SingletonClient --+                                   +--> CorporateData (datos)
                  +--> SERVIDOR ----> AWS DynamoDB ---+
ObserverClient ---+   (Proxy, Singleton,              +--> CorporateLog (auditoría)
                      Observer)

IteratorCorporateData ------------> AWS DynamoDB (directo, sin servidor)
```

> **ACLARACIÓN**
> **Dato clave para la defensa:** el programa `SingletonClient` **no es un singleton**. Es el cliente del servidor; los Singleton son los dos DAO que están dentro del servidor.

---

## 3. SECUENCIA DE EJECUCIÓN PASO A PASO

> **ACLARACIÓN**
> **Corrección del orden:** la guía original ejecutaba el SingletonClient (set) **antes** que el ObserverClient. Si hacés el `set` primero, el observer todavía no está suscripto y **no recibe ningún aviso**. El orden correcto para la demostración es: servidor, ObserverClient y después el SingletonClient. Por eso el ObserverClient pasó a ser el Paso 3.

### Paso 0 — Preparación del entorno desde cero

> **ACLARACIÓN**
> Este paso no estaba en la guía original. El zip del proyecto no trae el entorno virtual, así que hay que crearlo e instalar las librerías.

```
python -m venv .venv
.venv\Scripts\activate            (Windows)
source .venv/bin/activate         (macOS / Linux)
pip install -r requirements.txt
aws configure
```

> **ACLARACIÓN**
> En `aws configure` se cargan: Access Key ID, Secret Access Key, **región** (`us-east-1`, que es la que usa el código) y formato de salida (se puede dejar vacío). El proyecto usa la carpeta `.venv` (con punto).
>
> **Importante:** las credenciales de AWS **nunca** se suben a GitHub ni a ningún sitio público. La cuenta se bloquea de inmediato y reactivarla es un trámite lento. Para verificar que quedaron bien: `aws sts get-caller-identity`.

### Paso 1 — Activación del entorno y test diagnóstico AWS

Abrí la consola en la carpeta raíz del proyecto (ing2_tpfi-main), activá el entorno virtual y verificá la conexión contra la base de datos alojada en AWS:

```
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

# Test de credenciales y conexión con DynamoDB:
python IS2_TPFI_test.py
```

> **ACLARACIÓN**
> `IS2_TPFI_test.py` **no forma parte del zip**: lo entrega la cátedra en el aula virtual. Hay que copiarlo a la carpeta raíz para ejecutarlo. Si todo está bien, muestra un identificador de CPU y uno de sesión, sin errores.

### Paso 2 — Servidor principal (SingletonProxyObserverTPFI)

Iniciá el servidor en una terminal dedicada. Este programa permanecerá escuchando peticiones en el puerto TCP 8080:

```
python src/SingletonProxyObserverTPFI/singletonproxyobserver.py -p 8080 -v
```

> **ACLARACIÓN**
> `-v` muestra cada paso interno (ideal para la exposición). Para detener el servidor: **Ctrl+C**.

### Paso 3 — Suscripción en tiempo real (ObserverClient)

En una segunda terminal, levantá el cliente suscriptor. Este se mantendrá conectado en todo momento esperando actualizaciones:

```
python src/ObserverClient/observerclient.py -s localhost -p 8080 -o jsons/avisos.json -v
```

> **ACLARACIÓN**
> **Corrección:** la guía original guardaba la salida en `jsons/output.json`, el mismo archivo que usa el SingletonClient. Se pisan entre sí: el SingletonClient **sobreescribe** el archivo y el ObserverClient lo va **acumulando** como lista. Por eso acá se usa `jsons/avisos.json`.
>
> Si se corta la conexión, el ObserverClient reintenta solo cada 30 segundos y vuelve a suscribirse. Se cambia con `-r` (por ejemplo `-r 5`). Se detiene con **Ctrl+C**.

### Paso 4 — Peticiones puntuales (SingletonClient)

En una tercera terminal, ejecutá solicitudes de consulta (get), actualización (set) o listado completo (list) usando tus archivos dentro de jsons/:

```
# Consultar un registro por ID:
python src/SingletonClient/singletonclient.py -i jsons/get.json -o jsons/respuesta.json -v

# Actualizar o crear datos:
python src/SingletonClient/singletonclient.py -i jsons/set.json -o jsons/respuesta.json -v

# Listar todos los registros de la base:
python src/SingletonClient/singletonclient.py -i jsons/list.json -o jsons/respuesta.json -v
```

> **ACLARACIÓN**
> **Corrección:** se cambió `output.json` por `respuesta.json` para no pisar el archivo del observer.
>
> **La carpeta `jsons/` hay que crearla:** figura en el `.gitignore`, por lo que no viene en el repositorio ni en el zip. Contenido de los tres archivos de ejemplo (el UUID no se escribe: el programa agrega solo el identificador de tu CPU):

```
jsons/get.json     { "ACTION": "get", "ID": "TEST-GRUPO" }
jsons/set.json     { "ACTION": "set", "ID": "TEST-GRUPO", "telefono": "03442 43-1442" }
jsons/list.json    { "ACTION": "list" }
```

> **ACLARACIÓN**
> Reemplazá `TEST-GRUPO` por un ID que exista en tu tabla; podés ver los existentes con un `list` o con el Iterator.

### Paso 5 — Herramienta de recorrido (IteratorCorporateData)

Permite examinar y devolver registros en formato JSON directo utilizando el patrón Iterator:

```
# Recorrer la tabla completa:
python src/IteratorCorporateData/iteratorcorporatedata.py -v

# Buscar un registro específico por argumento:
python src/IteratorCorporateData/iteratorcorporatedata.py --id TEST-GRUPO -v
```

> **ACLARACIÓN**
> Este programa usa la región configurada con `aws configure` (el servidor, en cambio, fija `us-east-1` en el código). Si la región está vacía o es otra, el Iterator falla aunque el servidor funcione. Si el ID pedido no existe, termina con error.

### Referencia de opciones (argumentos)

> **ACLARACIÓN**
> Tabla nueva. Las opciones se escriben después del nombre del programa; las que llevan valor se escriben así: `-p 8080`.

| Opción | Significa | Qué hace | Programas |
|---|---|---|---|
| `-i` | input | Archivo JSON con el pedido (obligatorio). | SingletonClient |
| `-o` | output | Archivo donde se guarda la salida. Sin esta opción, se muestra en pantalla. | SingletonClient, ObserverClient |
| `-s` | server | Nombre o dirección del servidor. Por defecto localhost. | SingletonClient, ObserverClient |
| `-p` | port | Puerto TCP (1 a 65535). Por defecto 8080. | Servidor y ambos clientes |
| `-r` | retry | Segundos entre reintentos de conexión. Por defecto 30. | ObserverClient |
| `--id` | id | Registro a recuperar. Sin esta opción lista toda la tabla. | IteratorCorporateData |
| `-v` | verbose | Muestra los mensajes internos paso a paso (también se acepta `--v` en el Iterator). | Todos |
| Ctrl+C | — | Detiene un programa que queda corriendo. | Servidor, ObserverClient |

---

## 4. CREACIÓN DE NUEVOS REGISTROS Y COMPORTAMIENTO DE DATOS

### ¿Cómo crear y persistir un nuevo archivo JSON en la base de datos?

Para ingresar un nuevo registro en AWS DynamoDB, creá un archivo dentro de jsons/ (ejemplo: nuevo_registro.json) usando la acción "set" y un "ID" que no exista previamente en la tabla:

```json
{ "ID": "MI-NUEVA-EMPRESA-2026", "ACTION": "set",
  "cp": "3260", "CUIT": "20-12345678-9", "domicilio": "Urquiza 123",
  "idreq": "101", "idSeq": "500", "localidad": "Concepción del Uruguay",
  "provincia": "Entre Ríos", "sede": "FCyT", "seqID": "99",
  "telefono": "03442 12-3456", "web": "http://www.uader.edu.ar" }
```

Luego, ejecutás el comando desde la consola:

```
python src/SingletonClient/singletonclient.py -i jsons/nuevo_registro.json -o jsons/respuesta.json -v
```

> **ACLARACIÓN**
> Reglas que valida el SingletonClient antes de enviar el pedido (si alguna falla, ni siquiera se conecta al servidor):
>
> - `get` y `set` requieren un `ID` no vacío.
> - `set` requiere al menos un campo a modificar, y solo acepta los campos del registro (cp, CUIT, domicilio, idreq, idSeq, localidad, provincia, sede, seqID, telefono, web). Un campo desconocido se rechaza.
> - `list` **no** debe incluir `ID`.

### Reglas de negocio en la base de datos (DynamoDB)

| Escenario de acción "set" | Comportamiento en AWS DynamoDB y sistema |
|---|---|
| **ID inexistente** | Crea un registro completamente nuevo en la tabla CorporateData, genera la auditoría en CorporateLog y notifica al ObserverClient. |
| **ID existente (datos nuevos)** | Modifica los campos informados del registro existente en CorporateData, audita en CorporateLog y notifica el cambio vía Observer. |
| **ID y datos idénticos (repetidos)** | La información en CorporateData se mantiene igual (sin duplicados), pero el evento sí se audita en CorporateLog y sí dispara la notificación en tiempo real. |

> **ACLARACIÓN**
> **Corrección:** la guía original decía que, con un ID existente, "actualiza/sobreescribe los campos del registro". Es más preciso: **solo se modifican los campos que se envían** en el JSON; los demás quedan como estaban.
>
> Cuando el ID no existe y se crea un registro nuevo, los campos que no se informaron quedan **en blanco**.

---

## 5. PRUEBAS DE VALIDACIÓN Y VERIFICACIÓN

> **ACLARACIÓN**
> Sección nueva. El enunciado pide demostrar estos casos de prueba y la guía original no los incluía. Para cada uno se indica el comando y el resultado esperado.

### Código de salida de los programas

Todos los programas terminan con un código numérico que indica cómo les fue. Para verlo después de ejecutar un comando: `echo $?` (macOS/Linux) o `echo %errorlevel%` (Windows CMD).

> **ACLARACIÓN**
> Tabla de códigos de salida:

| Código | Significado |
|---|---|
| **0** | Terminó bien (en el servidor y el ObserverClient, también la cancelación con Ctrl+C). |
| **1** | Error de ejecución: servidor caído, puerto ocupado, registro inexistente, pedido inválido, falla de acceso a DynamoDB. |
| **2** | Argumentos malformados (lo devuelve la librería argparse). |

### Caso 1 — Argumentos malformados (probar en cada programa)

```
python src/SingletonClient/singletonclient.py
python src/SingletonClient/singletonclient.py -i jsons/get.json -p 99999
python src/ObserverClient/observerclient.py -p 0
python src/SingletonProxyObserverTPFI/singletonproxyobserver.py -p abc
python src/IteratorCorporateData/iteratorcorporatedata.py --id ""
```

> **ACLARACIÓN**
> Resultado esperado: mensaje de uso con el error y código de salida 2. El primero falla porque falta `-i`, que es obligatorio.

### Caso 2 — Pedido sin los datos mínimos

```
jsons/sin_id.json       { "ACTION": "get" }
jsons/sin_campos.json   { "ACTION": "set", "ID": "TEST-GRUPO" }

python src/SingletonClient/singletonclient.py -i jsons/sin_id.json -v
python src/SingletonClient/singletonclient.py -i jsons/sin_campos.json -v
```

> **ACLARACIÓN**
> Resultado esperado: error indicando qué falta (ID, o al menos un campo del registro) y código de salida 1. El pedido no llega a enviarse.

### Caso 3 — Servidor caído

```
# Con el servidor APAGADO:
python src/SingletonClient/singletonclient.py -i jsons/get.json -v
python src/ObserverClient/observerclient.py -r 5 -v
```

> **ACLARACIÓN**
> Resultado esperado: el SingletonClient informa "No se pudo conectar con localhost:8080" y termina con código 1. El ObserverClient no termina: avisa que perdió la conexión y reintenta cada 5 segundos. Si se enciende el servidor mientras reintenta, se conecta y se vuelve a suscribir solo.

### Caso 4 — Levantar dos veces el servidor

```
# Terminal 1 (queda corriendo):
python src/SingletonProxyObserverTPFI/singletonproxyobserver.py -p 8080 -v
# Terminal 2 (mismo comando):
python src/SingletonProxyObserverTPFI/singletonproxyobserver.py -p 8080 -v
```

> **ACLARACIÓN**
> Resultado esperado: la segunda instancia informa un error de socket ("¿puerto 8080 ocupado?") y termina con código 1; la primera sigue funcionando.

### Caso 5 — Camino feliz de cada acción y verificación en las tablas

> **ACLARACIÓN**
> Con el servidor y el ObserverClient en marcha, ejecutá un `get`, un `set` y un `list`, y verificá:
>
> - En el **ObserverClient** aparece un aviso solo con el `set` (acción "change").
> - En la consola de AWS (DynamoDB, Tablas, *Explorar elementos*) la tabla **CorporateData** refleja el cambio.
> - La tabla **CorporateLog** tiene un registro por cada acción, con los campos id, CPUid, sessionid, timestamp, action e item_id (este último no aparece en list ni subscribe, porque no afectan a un registro en particular). También queda registrada la suscripción del ObserverClient.

> **ACLARACIÓN**
> **Evidencia:** el enunciado pide logs o trazas de los casos de prueba. Con `-v` cada programa muestra su traza por salida estándar; se puede guardar con una redirección, por ejemplo `python ... -v > evidencia_get.txt`, o con capturas de pantalla.

---

## 6. CALIDAD, TESTS Y CI/CD

> **ACLARACIÓN**
> Sección nueva. Son los controles que pide el enunciado y los mismos que ejecuta el workflow de GitHub Actions. Se corren desde la carpeta raíz, con el entorno virtual activado.

| Herramienta | Qué verifica | Comando |
|---|---|---|
| **pytest + cobertura** | Tests unitarios; exige 85% o más de cobertura. | `pytest --cov=src --cov-fail-under=85` |
| **ruff** | Reglas de formato y errores de código. | `ruff check .` |
| **black** | Formato consistente del código. | `black --check .` |
| **pycodestyle** | Reglas PEP8. | `pycodestyle src` |
| **pydocstyle** | Convenciones PEP257 para docstrings. | `pydocstyle src` |
| **mypy** | Tipos estáticos, sin errores. | `python -m mypy src` |
| **pyright** | Segundo verificador de tipos. | `pyright` |
| **bandit** | Evaluación básica de seguridad, sin observaciones. | `bandit -r src` |
| **sphinx** | Genera la documentación HTML. | `sphinx-build -b html docs docs/_build/html` |

### Archivos de gestión del proyecto

> **ACLARACIÓN**
> Tabla nueva con los archivos de gestión que pide el enunciado:

| Archivo | Para qué sirve |
|---|---|
| **README.md** | Naturaleza del proyecto. Hay que actualizarlo antes de entregar: quedó desactualizado. |
| **CHANGELOG.md** | Registro de los cambios realizados. |
| **CONTEXT.md** | Prompts usados con herramientas de IA. |
| **VERSION y BUILD** | Registro de versión y número de build. El CI incrementa BUILD automáticamente. |
| **LICENSE** | Licencia MIT. |
| **requirements.txt** | Lista de librerías para recrear el entorno virtual. |
| **docs/** | Documentación generada con Sphinx. |
| **.github/workflows/ci.yml** | Workflow de CI/CD. |

### Etapas del workflow de GitHub Actions

> **ACLARACIÓN**
> El archivo `ci.yml` se ejecuta en cada Pull Request y en cada push a develop o main. Tiene estas etapas:
>
> - **lint**: ruff, black, pycodestyle, pydocstyle, mypy y pyright.
> - **security**: bandit.
> - **tests**: pytest con cobertura mínima del 85%.
> - **update-build**: si las tres anteriores pasan, incrementa BUILD (en develop).
> - **docs** y **docs-save**: construyen la documentación con Sphinx y, tras el merge a main, la guardan en docs/build.

---

## 7. ERRORES COMUNES Y SOLUCIONES

> **ACLARACIÓN**
> Sección nueva, útil para resolver imprevistos durante la demostración.

| Mensaje o síntoma | Causa probable y solución |
|---|---|
| **"no hay una región de AWS configurada"** | Falta la región. Ejecutar `aws configure` y cargar `us-east-1`. |
| **"no hay credenciales de AWS configuradas"** | Ejecutar `aws configure`. Verificar con `aws sts get-caller-identity`. |
| **"No se pudo acceder a DynamoDB" al arrancar el servidor** | Credenciales o región incorrectas, o las tablas no existen en esa cuenta. |
| **"No se pudo conectar con localhost:8080"** | El servidor está apagado o se usó otro puerto en `-p`. |
| **"Error de socket (¿puerto 8080 ocupado?)"** | Ya hay un servidor corriendo. Cerrarlo o usar otro puerto con `-p`. |
| **El ObserverClient no muestra avisos** | Se suscribió después del set; usa otro puerto; o la acción fue get/list, que no notifican. |
| **El archivo de salida pierde contenido** | Dos programas escriben en el mismo archivo. Usar archivos distintos (`respuesta.json` y `avisos.json`). |
| **"python" no se reconoce** | Probar con `python3`, o revisar que el entorno virtual esté activado. |
