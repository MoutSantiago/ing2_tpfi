"""Tests unitarios y de integración de IteratorCorporateData.

Se verifica el constructor, las tres formas del resultado, el retorno de
run y la propagación de las excepciones de los iteradores. La prueba de
integración combina una tabla falsa con los componentes reales
(TableScanIterator y JsonWrite).
"""

import json

import pytest

from IteratorCorporateData.app.exceptions import (
    DataAccessError,
    RecordNotFoundError,
)
from IteratorCorporateData.app.iterable_collection import Collection
from IteratorCorporateData.app.iterator_corporate_data import (
    IteratorCorporateData,
)
from IteratorCorporateData.app.json_write import JsonWrite
from IteratorCorporateData.app.recordIterator import Iterator
from IteratorCorporateData.app.tableScanIterator import TableScanIterator

RECORDS = [
    {"id": "registro-1", "nombre": "Ana"},
    {"id": "registro-2", "nombre": "Luis"},
    {"id": "registro-3", "nombre": "Carla"},
]


class FakeIterator(Iterator):
    """Iterador de prueba que recorre registros en memoria."""

    def __init__(self, records: list[dict]) -> None:
        self._records = list(records)
        self._index = 0

    def has_more(self) -> bool:
        """Indica si quedan registros sin avanzar el recorrido."""
        return self._index < len(self._records)

    def next(self) -> dict:
        """Devuelve el siguiente registro y avanza el recorrido."""
        if not self.has_more():
            raise StopIteration

        record = self._records[self._index]
        self._index += 1
        return record


class FailingIterator(Iterator):
    """Iterador de prueba que falla al recorrer."""

    def __init__(self, error: Exception, fail_on: str = "has_more") -> None:
        self._error = error
        self._fail_on = fail_on

    def has_more(self) -> bool:
        """Lanza el error configurado al consultar si quedan registros."""
        if self._fail_on == "has_more":
            raise self._error

        return True

    def next(self) -> dict:
        """Lanza el error configurado al pedir el siguiente registro."""
        raise self._error


class FakeCollection(Collection):
    """Colección de prueba que devuelve un iterador predefinido."""

    def __init__(self, iterator: Iterator) -> None:
        self._iterator = iterator
        self.create_iterator_calls = 0

    def create_iterator(self) -> Iterator:
        """Devuelve el iterador de prueba y registra la llamada."""
        self.create_iterator_calls += 1
        return self._iterator


class FakeWriter:
    """Escritor de prueba que guarda los resultados recibidos."""

    def __init__(self) -> None:
        self.results: list[object] = []

    def write(self, result: object) -> None:
        """Guarda el resultado en lugar de emitirlo."""
        self.results.append(result)


class FakeTable:
    """Tabla falsa que devuelve respuestas predefinidas de scan."""

    def __init__(self, pages: list[dict]) -> None:
        self.pages = list(pages)
        self.scan_calls: list[dict] = []

    def scan(self, **kwargs) -> dict:
        """Registra la llamada y devuelve la siguiente página."""
        self.scan_calls.append(kwargs)

        if not self.pages:
            raise AssertionError("Se solicitó una página inesperada.")

        return self.pages.pop(0)


class TableCollection(Collection):
    """Colección de prueba que crea el TableScanIterator real."""

    def __init__(self, table: FakeTable) -> None:
        self._table = table

    def create_iterator(self) -> Iterator:
        """Crea un TableScanIterator real sobre la tabla falsa."""
        return TableScanIterator(self._table)


def test_constructor_stores_dependencies_and_default_flag():
    """El constructor guarda las dependencias y single_record vale False."""
    collection = FakeCollection(FakeIterator(RECORDS))
    writer = FakeWriter()

    client = IteratorCorporateData(collection, writer)

    assert client._collection is collection
    assert client._writer is writer
    assert client._single_record is False


def test_constructor_does_not_query_the_database():
    """El constructor no crea el iterador ni escribe el resultado."""
    collection = FakeCollection(FakeIterator(RECORDS))
    writer = FakeWriter()

    IteratorCorporateData(collection, writer)

    assert collection.create_iterator_calls == 0
    assert writer.results == []


def test_run_writes_all_records_as_list_in_order():
    """Con varios registros, el escritor recibe la lista ordenada."""
    collection = FakeCollection(FakeIterator(RECORDS))
    writer = FakeWriter()

    result = IteratorCorporateData(collection, writer).run()

    assert writer.results == [RECORDS]
    assert result == RECORDS


def test_run_with_single_record_writes_the_object_not_a_list():
    """Con single_record=True, el escritor recibe el primer registro."""
    collection = FakeCollection(FakeIterator(RECORDS))
    writer = FakeWriter()

    result = IteratorCorporateData(
        collection, writer, single_record=True
    ).run()

    assert writer.results == [RECORDS[0]]
    assert result == RECORDS[0]
    assert not isinstance(result, list)


def test_run_with_empty_collection_writes_id_none():
    """Con una colección vacía, el escritor recibe {"id": None}."""
    collection = FakeCollection(FakeIterator([]))
    writer = FakeWriter()

    result = IteratorCorporateData(collection, writer).run()

    assert writer.results == [{"id": None}]
    assert result == {"id": None}


def test_run_returns_the_same_result_written():
    """run retorna exactamente lo mismo que recibió el escritor."""
    collection = FakeCollection(FakeIterator(RECORDS))
    writer = FakeWriter()

    result = IteratorCorporateData(collection, writer).run()

    assert result is writer.results[0]


def test_run_propagates_data_access_error_from_has_more():
    """Un DataAccessError de has_more se propaga y no se escribe nada."""
    error = DataAccessError("No se pudo acceder a la base de datos.")
    collection = FakeCollection(FailingIterator(error, fail_on="has_more"))
    writer = FakeWriter()

    with pytest.raises(DataAccessError) as exc_info:
        IteratorCorporateData(collection, writer).run()

    assert exc_info.value is error
    assert writer.results == []


def test_run_propagates_record_not_found_error_from_next():
    """Un RecordNotFoundError de next se propaga y no se escribe nada."""
    error = RecordNotFoundError("No existe el registro solicitado.")
    collection = FakeCollection(FailingIterator(error, fail_on="next"))
    writer = FakeWriter()

    with pytest.raises(RecordNotFoundError) as exc_info:
        IteratorCorporateData(collection, writer).run()

    assert exc_info.value is error
    assert writer.results == []


def test_run_propagates_oserror_from_writer():
    """Un OSError del escritor se propaga y no se captura."""
    collection = FakeCollection(FakeIterator(RECORDS))
    writer = FakeWriter()

    def failing_write(result: object) -> None:
        raise OSError("No se pudo escribir la salida.")

    writer.write = failing_write

    with pytest.raises(OSError, match="No se pudo escribir la salida."):
        IteratorCorporateData(collection, writer).run()


def test_integration_full_table_produces_json_list(capsys):
    """Con TableScanIterator y JsonWrite reales se emite la lista completa."""
    table = FakeTable([{"Items": RECORDS}])
    client = IteratorCorporateData(TableCollection(table), JsonWrite())

    result = client.run()

    output = json.loads(capsys.readouterr().out)
    assert output == RECORDS
    assert result == RECORDS


def test_integration_single_record_produces_json_object(capsys):
    """Una consulta por id emite el registro como objeto, no como lista."""
    record = {"id": "registro-1", "nombre": "Ana"}
    table = FakeTable([{"Items": [record]}])
    client = IteratorCorporateData(
        TableCollection(table), JsonWrite(), single_record=True
    )

    result = client.run()

    output = json.loads(capsys.readouterr().out)
    assert output == record
    assert result == record


def test_integration_empty_table_produces_id_none(capsys):
    """Con la tabla vacía se emite {"id": null} y se termina normalmente."""
    table = FakeTable([{"Items": []}])
    client = IteratorCorporateData(TableCollection(table), JsonWrite())

    result = client.run()

    output = json.loads(capsys.readouterr().out)
    assert output == {"id": None}
    assert result == {"id": None}
