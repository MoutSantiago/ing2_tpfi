# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

## [1.0.0] - 2026-10-20

### Added

- Incorporación del programa `IteratorCorporateData`: consulta de la tabla `CorporateData` de AWS DynamoDB mediante el patrón Iterator, con entry point ejecutable como `python3 src/IteratorCorporateData/iteratorcorporatedata.py --id=<id> {-v}`.
- Implementación de `IteratorCorporateData` (cliente del patrón Iterator), `CorporateDataCollection`, `TableScanIterator`, `SingleRecordIterator`, `Collection` e `Iterator` (interfaces), `JsonWrite` y excepciones propias.

## [0.3.0] - 2026-10-14

### Added

- Finalización del `ObserverClient`.
- Inicio del desarrollo del `SingletonObserver`.

## [0.2.0] - 2026-10-09

### Added

- Finalización del `Server`.
- Inicio del desarrollo del `ObserverClient`.

## [0.1.0] - 2026-10-02

### Added

- Creación del servidor `SingletonProxyObserverTPFI`.
