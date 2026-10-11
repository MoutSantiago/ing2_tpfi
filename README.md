# ing2_tpfi

**Trabajo Práctico Final Integrador — Patrón Proxy / Singleton / Observer en entorno AWS**

Ingeniería de Software II — UADER-FCyT-IS2 (2026)

---

## Descripción

Sistema distribuido de datos centralizados que expone los datos corporativos de la
institución (dirección oficial, CUIT, teléfono de contacto e identificador único de
secuencia) a través de un servidor de aplicaciones, sobre dos tablas de **AWS DynamoDB**:

| Tabla           | Descripción                                                         |
| --------------- | ------------------------------------------------------------------- |
| `CorporateData` | Contiene los datos centralizados.                                   |
| `CorporateLog`  | Contiene la pista de auditoría de los accesos y las modificaciones. |

El sistema implementa tres funciones principales: **recuperar** datos corporativos
(`get`), **modificar** datos corporativos (`set`) y **listar** la base completa
(`list`).

```
[Cliente] --JSON/TCP--> [Servidor de Aplicaciones] ---> (AWS) <---> [CorporateData]
                                                             <---> [CorporateLog]
```

Los datos de CPU que se auditan (UUID, plataforma) se obtienen de `uuid.getnode()` y
del paquete `platform`; el identificador de sesión de cada operación, de `uuid.uuid4()`.

## Estado del proyecto

> **Estado actual: en desarrollo. Solo el servidor de aplicaciones está implementado.**

### Componente `SingletonProxyObserverTPFI` — servidor (implementado)

Es el único componente con código funcional en `src/`. Servidor TCP que opera
simultáneamente como **proxy** (acceso a la base), **singleton** (conexión compartida a
DynamoDB) y **observer** (notificación de cambios a los suscriptores), generando además
el registro de auditoría.

### Componentes `SingletonClient` y `ObserverClient` — clientes (pendientes)

Los directorios `src/SingletonClient/` y `src/ObserverClient/` están reservados pero aún
**no contienen implementación**. Los entry points `singletonclient.py` y
`observerclient.py` quedan pendientes de desarrollo.

| Programa                    | Acción                               | Estado          |
| --------------------------- | ------------------------------------ | --------------- |
| `singletonproxyobserver.py` | `get` / `set` / `list` / `subscribe` | ✅ Implementado |
| `singletonclient.py`        | `get` / `set` / `list`               | ⏳ Pendiente    |
| `observerclient.py`         | `subscribe`                          | ⏳ Pendiente    |

#### Trabajo pendiente

- [ ] Cableado del entry point `singletonproxyobserver.py`: hoy `main()` solo parsea los
      argumentos e imprime un mensaje; falta instanciar los DAOs, el
      `SubscriptionManager`, el `CorporateDataProxy` y el `Server`, y dejar el proceso
      sirviendo hasta `Ctrl+C`.
- [ ] Implementar `SingletonClient` con los argumentos `-i`, `-o` y `-v`.
- [ ] Implementar `ObserverClient` con los argumentos `-s`, `-p`, `-o` y `-v`,
      incluyendo la reconexión cada 30 segundos (parametrizable).
- [ ] Casos de prueba de aceptación de la sección _Validación y Verificación_ del
      enunciado (argumentos malformados, servidor caído, doble levantamiento del
      servidor, verificación de los patrones).
- [ ] Diagramas UML de actividad (proxy) y de estado (observer).

## Arquitectura del servidor

El acceso a los datos está atravesado por los tres patrones exigidos por la consigna:

```
Servidor TCP  ──►  CorporateDataProxy  ──►  CorporateDataDAO   (DynamoDB: CorporateData)
   (server.py)     (patrón Proxy)          (patrón Singleton)
         │                │
         │                └──►  CorporateLogDAO  (DynamoDB: CorporateLog)
         │                      (patrón Singleton)
         └──►  SubscriptionManager ──► ClientObserver   (patrón Observer)
```

| Capa             | Patrón        | Responsabilidad                                                                    |
| ---------------- | ------------- | ---------------------------------------------------------------------------------- |
| `app/server.py`  | —             | Escucha TCP, valida el JSON recibido y deriva la petición según su `ACTION`.       |
| `app/proxy/`     | **Proxy**     | Aplica las reglas de negocio: audita **antes** de operar y notifica los cambios.   |
| `app/singleton/` | **Singleton** | Acceso único y thread-safe a las tablas `CorporateData` y `CorporateLog`.          |
| `app/observer/`  | **Observer**  | Gestiona las suscripciones y difunde las notificaciones a los clientes suscriptos. |

Decisiones de diseño relevantes:

- **Auditoría antes que operación.** El proxy escribe primero en `CorporateLog`; si esa
  escritura falla, la acción no se ejecuta. Ningún dato cambia sin quedar auditado.
- **Conexión compartida.** Los DAOs son singletons con `threading.Lock`, porque el
  servidor atiende cada cliente en su propio hilo y todos comparten la misma conexión.
- **Inyección de dependencias.** `Server` recibe el proxy y el publisher por constructor y
  trabaja contra la interfaz `CorporateDataInterface`, por lo que los tests pueden
  sustituir el DAO real por un mock.

## Protocolo

Comunicación por **socket TCP**, intercambiando mensajes JSON terminados en `\n`.

### Peticiones

| Acción      | Campos mínimos                             | Respuesta                                |
| ----------- | ------------------------------------------ | ---------------------------------------- |
| `get`       | `UUID`, `ACTION`, `ID`                     | Registro solicitado o `{"Error": ...}`   |
| `set`       | `UUID`, `ACTION`, `ID` + al menos un campo | Registro resultante o `{"Error": ...}`   |
| `list`      | `UUID`, `ACTION` (sin `ID`)                | Array con todos los registros            |
| `subscribe` | `UUID`, `ACTION`                           | Sin respuesta; la conexión queda abierta |

Los campos del tuple `CorporateData` son: `id` (clave de partición), `cp`, `CUIT`,
`domicilio`, `idreq`, `idSeq`, `localidad`, `provincia`, `sede`, `seqID`, `telefono` y
`web`. En un `set`, los campos no informados no se modifican; si el registro no existía,
se crea con esos campos en blanco.

Cada petición —incluida la suscripción— genera un registro en `CorporateLog` con UUID,
sesión, acción, ID (cuando aplica) y timestamp.

## Estructura del proyecto

```
ing2_tpfi/
├── src/
│   ├── SingletonProxyObserverTPFI/   # Servidor (implementado)
│   │   ├── singletonproxyobserver.py # Entry point
│   │   └── app/
│   │       ├── server.py             # Servidor TCP
│   │       ├── exceptions.py         # Excepciones propias
│   │       ├── observer/             # Patrón Observer
│   │       ├── proxy/                # Patrón Proxy
│   │       └── singleton/            # Patrón Singleton (DAOs)
│   ├── SingletonClient/              # ⏳ Pendiente
│   └── ObserverClient/               # ⏳ Pendiente
├── tests/                            # Pytest (moto para emular DynamoDB)
├── docs/                             # Documentación Sphinx
├── scripts/                          # Utilidades de la cátedra
├── .github/workflows/ci.yml          # Pipeline de CI/CD
├── REQUIREMENTS.md                   # Enunciado de la consigna
├── VERSION / BUILD                   # Versionado y número de build
└── CHANGELOG.md                      # Registro de cambios
```

## Requisitos

- Python 3.12 (fijado en `.python-version`), dentro de un entorno virtual.
- Credenciales AWS configuradas y las tablas `CorporateData` y `CorporateLog` ya creadas
  (ver la nota de aplicación _"IS2_NAPP_Arquitectura AWS Python"_).

## Instalación

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
aws configure
```

La guía completa está en [`docs/installation.md`](docs/installation.md).

## Uso

Servidor (único componente ejecutable por el momento):

```sh
python src/SingletonProxyObserverTPFI/singletonproxyobserver.py {-p=8080} {-v}
```

Los clientes, cuando estén implementados, se invocarán como:

```sh
python src/SingletonClient/singletonclient.py -i=input.json {-o=output.json} {-v}
python src/ObserverClient/observerclient.py {-s=localhost} {-p=8080} {-o=output.json} {-v}
```

## Desarrollo y calidad

El proyecto se adhiere a GitFlow y ejecuta en cada PR hacia `main` o `develop` la
batería completa de lint, análisis estático, seguridad y tests con cobertura mínima de
85%. Los comandos exactos están documentados en [`docs/development.md`](docs/development.md).

```sh
ruff check . && black --check . && pycodestyle src && pydocstyle src && \
  mypy src && pyright && bandit -r src && pytest --cov=src --cov-fail-under=85
```

## Documentación

```sh
sphinx-build -b html docs docs/_build/html
```

## Autores

- Laiño Valentino
- Mout Santiago
- Sandillú Axel

## Licencia

MIT — ver [LICENSE](LICENSE).
