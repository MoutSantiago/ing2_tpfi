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

| Tipo de rama | Propósito | Convención de nombre | Base | Merge a |
|--------------|-----------|---------------------|------|---------|
| `feature` | Nuevas funcionalidades | `feature/<nombre-descriptivo>` | `develop` | `develop` |
| `bugfix` | Correcciones no urgentes | `bugfix/<nombre-descriptivo>` | `develop` | `develop` |
| `release` | Preparación de una nueva versión | `release/<versión>` (ej.: `release/1.2.0`) | `develop` | `main` y `develop` |
| `hotfix` | Correcciones urgentes en producción | `hotfix/<versión>` (ej.: `hotfix/1.1.1`) | `main` | `main` y `develop` |

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
