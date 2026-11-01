# Ingeniería de Software II — Guía Final de Examen
**Trabajo Práctico Integrador:** Patrones Proxy, Singleton, Observer e Iterator en AWS  
**Institución:** Universidad Autónoma de Entre Ríos (UADER - FCyT)

---

## 1. Conceptos Fundamentales Explicados Simple

Para defender tu trabajo final con soltura ante el tribunal de evaluación, es indispensable dominar la terminología técnica reduciéndola a conceptos cotidianos y directos:

| Término Técnico | Explicación Sencilla para el Examen |
| :--- | :--- |
| **Entorno Virtual (`venv`)** | Caja de aislamiento local donde residen las librerías específicas del proyecto sin interferir con el sistema operativo ni otros proyectos. |
| **AWS CLI & Boto3** | La herramienta de consola (CLI) y el SDK oficial de Python (Boto3) que traducen las peticiones del código a comandos nativos en la nube de AWS. |
| **DynamoDB** | Base de datos NoSQL de alta velocidad alojada en AWS que guarda la información como registros de tipo documento (JSON). |
| **Socket TCP** | Canal de comunicación bidireccional permanente ("cable de red virtual") abierto entre un cliente y el servidor. |
| **DAO (Data Access Object)** | Patrón estructural que encapsula y aísla el acceso directo a la base de datos del resto de la lógica de aplicación. |
| **UUID / Session ID** | Identificadores únicos de máquina y de sesión utilizados para auditar y rastrear de forma unívoca cada petición. |

---

## 2. Arquitectura de los 4 Patrones Implementados

### 🔹 Patrón 1: Singleton
Garantiza que exista una **única instancia global** de acceso a la base de datos (`CorporateDataDAO` y `CorporateLogDAO`), evitando la apertura redundante de conexiones a AWS DynamoDB.

### 🔹 Patrón 2: Proxy
Funciona como un **intermediario o filtro de seguridad**. Intercepta las llamadas enviadas al servidor antes de tocar la base de datos para registrar la pista de auditoría en la tabla `CorporateLog` y validar los requerimientos de la petición.

### 🔹 Patrón 3: Observer
Mecanismo de **suscripción y notificación en tiempo real**. Cuando una actualización (`set`) modifica los datos en el servidor, este notifica automáticamente a todos los `ObserverClient` suscritos a través de la conexión TCP mantenida abierta.

### 🔹 Patrón 4: Iterator
Proporciona un **mecanismo secuencial estandarizado** para recorrer los registros de la tabla `CorporateData` sin exponer la estructura interna ni los detalles de implementación de las consultas en DynamoDB.

---

## 3. Secuencia de Ejecución Paso a Paso

### Paso 1: Activación de Entorno Virtual y Test Diagnóstico AWS
Abrí la consola en la carpeta raíz del proyecto (`ing2_tpfi-main`), activá el entorno virtual y verificá la conexión contra la base de datos alojada en AWS:

```bash
# En Windows:
venv\Scripts\activate

# En macOS / Linux:
source venv/bin/activate

# Test de credenciales y conexión con DynamoDB:
python IS2_TPFI_test.py
```
*(Debe retornar "Completed successfully" junto con el CPU ID y Session ID).*

---

### Paso 2: Servidor Principal (`SingletonProxyObserverTPFI`)
Iniciá el servidor en una terminal dedicada. Este programa permanecerá escuchando peticiones en el puerto TCP `8080`:

```bash
python src/SingletonProxyObserverTPFI/singletonproxyobserver.py -p 8080 -v
```

---

### Paso 3: Peticiones Puntuales (`SingletonClient`)
En una segunda terminal, ejecutá solicitudes de consulta (`get`), actualización (`set`) o listado completo (`list`) usando tus archivos dentro de la carpeta `jsons/`:

```bash
# Consultar un registro específico por ID:
python src/SingletonClient/singletonclient.py -i jsons/get.json -o jsons/output.json -v

# Actualizar o crear datos:
python src/SingletonClient/singletonclient.py -i jsons/set.json -o jsons/output.json -v

# Listar todos los registros de la base:
python src/SingletonClient/singletonclient.py -i jsons/list.json -o jsons/output.json -v
```

---

### Paso 4: Suscripción en Tiempo Real (`ObserverClient`)
En una tercera terminal, levantá el cliente suscriptor. Este se mantendrá conectado en todo momento esperando actualizaciones:

```bash
python src/ObserverClient/observerclient.py -s localhost -p 8080 -o jsons/output.json -v
```

---

### Paso 5: Herramienta de Recorrido (`IteratorCorporateData`)
Permite examinar y devolver registros en formato JSON directo utilizando el patrón Iterator:

```bash
# Recorrer e imprimir la tabla completa:
python src/IteratorCorporateData/iteratorcorporatedata.py -v

# Buscar un registro específico por argumento:
python src/IteratorCorporateData/iteratorcorporatedata.py --id TEST-GRUPO -v
```

---

## 4. Creación de Nuevos Registros y Comportamiento de Datos

### 📝 ¿Cómo crear y persistir un nuevo archivo JSON en la Base de Datos?

Para ingresar un nuevo registro en AWS DynamoDB:

1. Creá un nuevo archivo dentro de tu carpeta `jsons/` (por ejemplo: `nuevo_registro.json`).
2. Asignale la acción `"set"` y un `"ID"` que **no exista previamente** en la base de datos:

```json
{
  "ID": "MI-NUEVA-EMPRESA-2026",
  "ACTION": "set",
  "cp": "3260",
  "CUIT": "20-12345678-9",
  "domicilio": "Urquiza 123",
  "idreq": "101",
  "idSeq": "500",
  "localidad": "Concepción del Uruguay",
  "provincia": "Entre Ríos",
  "sede": "FCyT",
  "seqID": "99",
  "telefono": "03442 12-3456",
  "web": "http://www.uader.edu.ar"
}
```

3. Ejecutá el cliente Singleton especificando la ruta al nuevo archivo:

```bash
python src/SingletonClient/singletonclient.py -i jsons/nuevo_registro.json -o jsons/output.json -v
```

---

### 📊 Reglas de Negocio y Persistencia en AWS DynamoDB

| Escenario de Acción `"set"` | Comportamiento en AWS DynamoDB | Auditoría (`CorporateLog`) | Evento Observer (`ObserverClient`) |
| :--- | :--- | :--- | :--- |
| **ID Inexistente** | Crea un registro totalmente nuevo en `CorporateData`. | Registra evento de creación con timestamp y UUID. | Notifica en tiempo real a todos los clientes suscritos. |
| **ID Existente (Datos Nuevos)** | Actualiza / Sobreescribe los campos del registro en `CorporateData`. | Registra evento de modificación con timestamp y UUID. | Notifica la actualización en tiempo real a los suscritos. |
| **ID y Datos Idénticos (Repetidos)** | DynamoDB realiza un *upsert* sin duplicar filas (los datos se mantienen igual). | **Sí se audita:** Genera un nuevo registro de entrada en `CorporateLog`. | **Sí se dispara:** Reenvía la notificación JSON al `ObserverClient`. |

---

## 5. El "Camino Feliz" Integrado para la Presentación

Para lucirte en la mesa de examen, ejecutá los componentes en este orden secuencial exacto:

1. **Terminal 1:** Levantá el Servidor (`singletonproxyobserver.py`).
2. **Terminal 2:** Iniciá el Suscriptor (`observerclient.py`). Quedará en escucha activa.
3. **Terminal 3:** Ejecutá un `set` desde el `singletonclient.py` con `jsons/set.json` o un JSON nuevo.
4. **Verificación en vivo:** Mostrale a tus profesores cómo la **Terminal 2** recibe la notificación al instante gracias al **Observer**, mientras que en la **Terminal 1** el **Proxy** registró la auditoría en `CorporateLog` y el **Singleton** administró el acceso a DynamoDB.
5. **Terminal 3 (Cierre):** Recorré los datos almacenados invocando `iteratorcorporatedata.py` para demostrar el funcionamiento del patrón **Iterator**.