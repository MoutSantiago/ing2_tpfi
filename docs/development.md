# Comandos de desarrollo

Referencia de los comandos de testing, linting, análisis estático, seguridad y documentación.
Todos deben ejecutarse con el ambiente virtual activo (ver [Instalación](installation.md)).

La CI ejecuta exactamente este mismo set de comandos en cada pull request hacia `main`
(`.github/workflows/ci.yml`), por lo que un PR solo se mergea si toda la battery pasa.

## Atajos

```sh
source .venv/bin/activate
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
mypy src                        # igual que en la CI
mypy src --strict               # chequeo estricto
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
mypy src && \
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
