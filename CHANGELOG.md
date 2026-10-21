# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

## [1.0.1] - 2026-10-21

### Fixed

- Corrección del archivo `.gitignore`.

## [1.0.0] - 2026-10-20

### Added

- Incorporación del programa `IteratorCorporateData`: consulta de la tabla `CorporateData` de AWS DynamoDB mediante el patrón Iterator, con entry point ejecutable como `python3 src/IteratorCorporateData/iteratorcorporatedata.py --id=<id> {-v}`.
- Implementación de `IteratorCorporateData` (cliente del patrón Iterator), `CorporateDataCollection`, `TableScanIterator`, `SingleRecordIterator`, `Collection` e `Iterator` (interfaces), `JsonWriter` y excepciones propias.
- Punto de entrada completo del programa IteratorCorporateData.
- Actualización de la documentación del proyecto.

## [0.9.0] - 2026-10-19

### Added

- Implementación de `TableScanIterator` con pruebas unitarias.
- Implementación de `SingleRecordIterator` y `CorporateDataCollection`.
- Creación de la interfaz `Collection`.
- Clase `JsonWriter` para serialización de resultados.

### Fixed

- Correcciones en el iterador de `IteratorCorporateData`.
- Varios ajustes para pasar las pruebas unitarias.

## [0.8.0] - 2026-10-17

### Added

- Creación de la clase `JsonWriter`.
- Excepciones propias y pruebas unitarias para `IteratorCorporateData`.
- Estructura de carpetas `app` dentro de `IteratorCorporateData`.

## [0.7.0] - 2026-10-15

### Added

- Implementación de `SingletonClient`.
- Finalización del punto de entrada del `SingletonClient`.
- Clase `RequestLoader` para cargar peticiones.
- Clase `ServerConnection` para conexión con el servidor.
- Excepciones del `SingletonClient` con pruebas unitarias.

### Changed

- Correcciones en el flujo de respuesta del `SingletonClient`.
- Ajustes en `pyproject.toml` y `.gitignore`.
- Cambio de nombre de paquetes y módulos.

## [0.6.0] - 2026-10-14

### Added

- Finalización del `ObserverClient`.
- `notification_writer.py` con pruebas unitarias.
- Clase `ServerConnection` para el cliente Observer.
- `observerclient.py` con pruebas unitarias (issues 48).

### Fixed

- Arreglos para pasar pruebas de git.
- Corrección de nombres de archivos de prueba.

## [0.5.0] - 2026-10-13

### Added

- Logs de `ObserverClient`.
- Excepciones para el cliente Observer.
- Estructura de carpetas del cliente Observer.

## [0.4.0] - 2026-10-10

### Added

- Excepciones para el cliente Observer creadas.
- Estructura de carpetas del cliente Observer.

## [0.3.3] - 2026-10-14

### Added

- Finalización del `ObserverClient`.
- Implementación de `SingletonClient` con punto de entrada.

### Changed

- Corrección de flujos de trabajo de GitHub Actions.
- Ajustes en `pyproject.toml` y `.gitignore`.

## [0.3.0] - 2026-10-14

### Added

- Finalización del `ObserverClient`.
- Inicio del desarrollo del `SingletonObserver`.

## [0.2.1] - 2026-10-09

### Added

- Finalización del `Server`.
- Inicio del desarrollo del `ObserverClient`.

## [0.2.0] - 2026-10-09

### Added

- Cambio de versión.

## [0.1.1] - 2026-10-02

### Added

- Creación del servidor `SingletonProxyObserverTPFI`.

## [0.1.0] - 2026-10-02

### Added

- Estructura inicial del proyecto.
