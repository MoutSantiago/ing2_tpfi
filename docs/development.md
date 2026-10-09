# Comandos de desarrollo

Referencia de los comandos de testing, linting, análisis estático, seguridad y documentación.
Todos deben ejecutarse con el ambiente virtual activo (ver [Instalación](installation.md)).

La CI ejecuta exactamente este mismo set de comandos en cada pull request hacia `main`
(`.github/workflows/ci.yml`), por lo que un PR solo se mergea si toda la battery pasa.

## Flujo de trabajo (GitFlow)

Este proyecto sigue el estándar [GitFlow](https://nvie.com/posts/a-successful-git-branching-model/).
Todas las ramas deben crearse respetando este modelo para mantener consistencia en el repositorio.

### Ramas principales

- `main`: Rama de producción. Contiene únicamente código estable y listo para desplegar.
- `develop`: Rama de integración. Aquí se integran todas las funcionalidades en desarrollo antes de pasar a producción.

### Ramas de soporte

| Tipo de rama | Propósito                           | Convención de nombre                       | Base      | Merge a            |
| ------------ | ----------------------------------- | ------------------------------------------ | --------- | ------------------ |
| `feature`    | Nuevas funcionalidades              | `feature/<nombre-descriptivo>`             | `develop` | `develop`          |
| `bugfix`     | Correcciones no urgentes            | `bugfix/<nombre-descriptivo>`              | `develop` | `develop`          |
| `release`    | Preparación de una nueva versión    | `release/<versión>` (ej.: `release/1.2.0`) | `develop` | `main` y `develop` |
| `hotfix`     | Correcciones urgentes en producción | `hotfix/<versión>` (ej.: `hotfix/1.1.1`)   | `main`    | `main` y `develop` |

### Pasos para crear una nueva rama

1. **Actualizar la rama base**:

   ```sh
   git checkout develop
   git pull origin develop
   ```

2. **Crear y cambiar a la nueva rama**:

   ```sh
   git checkout -b feature/<nombre-descriptivo>
   ```

3. **Hacer los cambios y commits** siguiendo las convenciones del proyecto.

4. **Subir la rama al remoto**:

   ```sh
   git push -u origin feature/<nombre-descriptivo>
   ```

5. **Abrir un Pull Request** hacia la rama base (`develop`, o `main` para hotfixes) cuando esté listo.

> **Nota:** un `hotfix` se crea desde `main`. Después de mergearlo a `main`, hay que integrar esos
> mismos cambios en `develop` (un `merge` de `main` sobre `develop`) para no perderlos.

## Atajos

```sh
source .venv/bin/activate
```

## Ejecutar el servidor

El punto de entrada es `singletonproxyobserver.py`, que expone un comando de Typer con las flags
`--port/-p` y `--verbose/-v`.

### Desde el directorio del paquete

```sh
cd src/SingletonProxyObserverTPFI
python3 singletonproxyobserver.py                 # puerto 8080, sin logs detallados
python3 singletonproxyobserver.py -v              # puerto 8080, con logs detallados
python3 singletonproxyobserver.py --port 5000     # puerto 5000
python3 singletonproxyobserver.py -p 5000 -v      # puerto 5000, con logs detallados
```

### Como módulo

```sh
cd src
python3 -m SingletonProxyObserverTPFI.singletonproxyobserver -p 5000 -v
```

Ver la ayuda de las flags:

```sh
python3 singletonproxyobserver.py --help
```

### Códigos de salida

| Código | Significado                                                                     |
| ------ | ------------------------------------------------------------------------------- |
| `0`    | Terminación normal. Ocurre al cancelar con `Ctrl+C`, que dispara el apagado ordenado |
| `1`    | Error de ejecución: puerto ya ocupado o no se pudo acceder a DynamoDB           |
| `2`    | Argumentos malformados (lo devuelve Typer por defecto)                          |

Los errores fatales de arranque se informan con un mensaje claro, nunca con un traceback.

### Requisitos para arrancar

El servidor abre la conexión a DynamoDB al inicio (no de forma diferida), así que sin acceso a la
tabla `CorporateData` o `CorporateLog` falla al arrancar con código `1` en lugar de fallar con el
primer cliente.

## Probar el servidor a mano

El protocolo es TCP con un mensaje JSON por línea, terminado en `\n`.
Las acciones válidas son `get`, `set`, `list` y `subscribe`.

Todos los comandos siguientes se ejecutan en **otra terminal** con el servidor ya corriendo.

### `list` — recuperar todos los registros

```sh
echo '{"UUID":"cliente-1","ACTION":"list"}' | nc localhost 8080
```

Respuesta esperada: un JSON array con todos los registros de `CorporateData`.

### `get` — recuperar un registro por clave

```sh
echo '{"UUID":"cliente-1","ACTION":"get","ID":"1"}' | nc localhost 8080
```

Si el registro no existe, la respuesta es `{"Error":"No existe un registro con id='1' en CorporateData"}`.

### `set` — crear o modificar un registro

Para un registro nuevo, los campos no informados quedan en blanco:

```sh
echo '{"UUID":"cliente-1","ACTION":"set","ID":"1","CUIT":"30-12345678-9","sede":"Central"}' | nc localhost 8080
```

Un `set` exige al menos un campo de `CorporateData` además del `ID`. Los campos válidos son `cp`,
`CUIT`, `domicilio`, `idreq`, `idSeq`, `localidad`, `provincia`, `sede`, `seqID`, `telefono` y `web`.

### `subscribe` — recibir los cambios en tiempo real

```sh
echo '{"UUID":"cliente-2","ACTION":"subscribe"}' | nc localhost 8080
```

La conexión queda abierta: `subscribe` no responde ni cierra el socket. Cada `set` de otro cliente
llega por esa misma conexión como un JSON con `"ACTION":"change"`.

Para verlo, dejá el `nc` de `subscribe` abierto en una terminal y ejecutá un `set` en otra.

### Probar el error de puerto ocupado

```sh
python3 singletonproxyobserver.py -p 8080   # con el servidor ya corriendo en 8080
```

Salida esperada: un mensaje de error de socket y código de salida `1`.

### Probar la cancelación manual

Con el servidor corriendo, `Ctrl+C` en su terminal. La salida debe mostrar el apagado ordenado y
terminar con código de salida `0`.

### Sin `nc`

Si no tenés `netcat`, podés mandar las peticiones con Python:

```sh
python3 -c "import socket; s=socket.create_connection(('localhost',8080),5); s.sendall(b'{\"UUID\":\"cliente-1\",\"ACTION\":\"list\"}\n'); print(s.recv(65536).decode())"
```

Para `subscribe` (que deja la conexión abierta), reemplazá `recv` por un loop que imprima cada
línea conforme llega:

```sh
python3 -c "import socket; s=socket.create_connection(('localhost',8080),5); s.sendall(b'{\"UUID\":\"cliente-2\",\"ACTION\":\"subscribe\"}\n'); f=s.makefile('rb'); [print(l.decode().strip()) for l in f]"
```

## Tests

```sh
pytest                                              # suite completa
pytest -v                                           # con detalle de cada test
pytest tests/main_test.py                           # un archivo puntual
pytest -k "sumar"                                   # filtrar por nombre
pytest -x                                           # cortar en el primer fallo
pytest --cov=src --cov-fail-under=85                # igual que en la CI
pytest --cov=src --cov-report=term-missing          # ver líneas sin cubrir
```

La cobertura mínima exigida es **85%**. `pyproject.toml` ya define `pythonpath = ["src"]`, por lo que
no hace falta instalar el proyecto en modo editable.

`moto` está entre las dependencias para emular DynamoDB en los tests y no depender de AWS.

## Lint y formato

```sh
ruff check .                    # reglas de lint (rápido, es el que corre la CI)
ruff check --fix .              # autofixes seguros
ruff check --diff .             # muestra qué cambiaría sin tocar archivos
ruff format .                   # formateo con ruff
black .                         # aplica formato consistent
black --check .                 # solo verifica formato (usado en la CI)
```

## Estilo (PEP 8 / PEP 257)

```sh
pycodestyle src                 # PEP 8
pydocstyle src                  # PEP 257 (docstrings)
```

## Análisis estático de tipos

```sh
python -m mypy src                       # igual que en la CI
python -m mypy src --strict               # chequeo estricto
pyright                         # igual que en la CI
pyright --pythonpath .venv/bin/python   # necesario para resolver boto3/pytest
```

Sin `--pythonpath`, `pyright` no encuentra las librerías instaladas en el venv y reporta
`reportMissingImports` falsos.

## Seguridad

```sh
bandit -r src                   # igual que en la CI
bandit -r src -f screen -lll    # solo severidad alta/media
```

## Documentación

```sh
sphinx-build -b html docs docs/_build/html
```

La salida queda en `docs/_build/html/index.html` (ignorado por git).

## Ejecución completa (replica de la CI)

```sh
ruff check . && \
black --check . && \
pycodestyle src && \
pydocstyle src && \
python -m mypy src && \
pyright && \
bandit -r src && \
pytest --cov=src --cov-fail-under=85
```

## Agregar una dependencia

```sh
pip install <paquete>
pip freeze > requirements.txt
```

Actualizar `requirements.txt` es parte de la consigna, y el archivo debe seguir commiteado.
