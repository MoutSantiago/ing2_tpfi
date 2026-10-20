"""Tests unitarios de SingleRecordIterator.

Se verifica que el iterador de un único registro cumpla la interfaz
Iterator, que devuelva el registro pedido, que propague las excepciones
esperadas y que crear el iterador no consulte la tabla.
"""

import pytest

# pyrefly: ignore[missing-source-for-stubs]
from botocore.exceptions import ClientError

from IteratorCorporateData.app.exceptions import (
    DataAccessError,
    RecordNotFoundError,
)
from IteratorCorporateData.app.recordIterator import Iterator
from IteratorCorporateData.app.single_record_iterator import (
    SingleRecordIterator,
)


class FakeTable:
    """Tabla falsa que devuelve respuestas predefinidas de get_item."""

    def __init__(self, response: dict) -> None:
        self.response = response
        self.get_item_calls: list[dict] = []

    def get_item(self, Key: dict) -> dict:
        """Registra la llamada y devuelve la respuesta predefinida."""
        self.get_item_calls.append(Key)
        return self.response


class FailingTable:
    """Tabla falsa cuyo get_item siempre falla con un error de boto3."""

    def __init__(self, error: Exception) -> None:
        self._error = error

    def get_item(self, Key: dict) -> dict:
        raise self._error


RECORD = {"id": "registro-1", "nombre": "Ana"}


def test_single_record_iterator_is_an_iterator():
    """El iterador de registro único implementa la interfaz Iterator."""
    table = FakeTable({"Item": RECORD})
    assert isinstance(SingleRecordIterator(table, "registro-1"), Iterator)


def test_constructor_does_not_call_the_table():
    """Crear el iterador no invoca get_item en la tabla."""
    table = FakeTable({"Item": RECORD})
    SingleRecordIterator(table, "registro-1")
    assert table.get_item_calls == []


def test_existing_id_returns_record_and_has_more_becomes_false():
    """Un id existente devuelve el registro y luego has_more da False."""
    table = FakeTable({"Item": RECORD})
    iterator = SingleRecordIterator(table, "registro-1")

    assert iterator.has_more() is True
    assert iterator.next() == RECORD
    assert iterator.has_more() is False
    assert table.get_item_calls == [{"id": "registro-1"}]


def test_inexistent_id_raises_record_not_found_error():
    """Un id inexistente lanza RecordNotFoundError."""
    table = FakeTable({})
    iterator = SingleRecordIterator(table, "no-existe")

    with pytest.raises(RecordNotFoundError, match="no-existe"):
        iterator.next()

    assert iterator.has_more() is False


def test_second_next_raises_stop_iteration():
    """Un segundo next despues de entregar el registro lanza StopIteration."""
    table = FakeTable({"Item": RECORD})
    iterator = SingleRecordIterator(table, "registro-1")

    iterator.next()
    assert iterator.has_more() is False

    with pytest.raises(StopIteration):
        iterator.next()


def test_get_item_failure_raises_data_access_error_with_cause():
    """Si get_item falla, se lanza DataAccessError con la causa encadenada
    y has_more da False despues."""
    original_error = ClientError(
        {"Error": {"Code": "InternalError", "Message": "boom"}},
        "GetItem",
    )
    table = FailingTable(original_error)
    iterator = SingleRecordIterator(table, "registro-1")

    with pytest.raises(DataAccessError) as exc_info:
        iterator.next()

    assert exc_info.value.__cause__ is original_error
    assert iterator.has_more() is False


def test_has_more_is_idempotent_before_next():
    """Repetir has_more antes de next no debe avanzar ni consultar."""
    table = FakeTable({"Item": RECORD})
    iterator = SingleRecordIterator(table, "registro-1")

    first = iterator.has_more()
    assert first is True
    assert iterator.has_more() is first
    assert iterator.has_more() is first
    assert table.get_item_calls == []
