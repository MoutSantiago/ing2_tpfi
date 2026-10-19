"""Tests unitarios de TableScanIterator."""

import pytest
from botocore.exceptions import ClientError

from IteratorCorporateData.app.exceptions import DataAccessError
from IteratorCorporateData.app.recordIterator import Iterator
from IteratorCorporateData.app.tableScanIterator import TableScanIterator


class FakeTable:
    """Tabla falsa que devuelve respuestas predefinidas de scan."""

    def __init__(self, pages):
        self.pages = list(pages)
        self.scan_calls = []

    def scan(self, **kwargs):
        """Registra la llamada y devuelve la siguiente página."""
        self.scan_calls.append(kwargs)

        if not self.pages:
            raise AssertionError("Se solicitó una página inesperada.")

        page = self.pages.pop(0)

        if isinstance(page, Exception):
            raise page

        return page


def test_constructor_does_not_call_scan():
    """El constructor no debe consultar DynamoDB."""
    table = FakeTable([{"Items": [{"id": "1"}]}])

    TableScanIterator(table)

    assert table.scan_calls == []


def test_table_scan_iterator_implements_interface():
    """El iterador concreto implementa la interfaz."""
    iterator = TableScanIterator(FakeTable([]))

    assert isinstance(iterator, Iterator)


def test_multiple_pages_are_returned_in_order():
    """Recorre todas las páginas en el orden recibido."""
    records = [
        {"id": "1"},
        {"id": "2"},
        {"id": "3"},
    ]
    table = FakeTable(
        [
            {
                "Items": records[:2],
                "LastEvaluatedKey": {"id": "2"},
            },
            {"Items": records[2:]},
        ]
    )
    iterator = TableScanIterator(table)

    result = []

    while iterator.has_more():
        result.append(iterator.next())

    assert result == records
    assert len(table.scan_calls) == 2


def test_scan_is_lazy():
    """Solo pide la primera página al consumir el primer registro."""
    table = FakeTable(
        [
            {
                "Items": [{"id": "1"}, {"id": "2"}],
                "LastEvaluatedKey": {"id": "2"},
            },
            {"Items": [{"id": "3"}]},
        ]
    )
    iterator = TableScanIterator(table)

    assert iterator.next() == {"id": "1"}
    assert len(table.scan_calls) == 1


def test_empty_table_is_exhausted():
    """Una tabla vacía no tiene registros."""
    table = FakeTable([{"Items": []}])
    iterator = TableScanIterator(table)

    assert iterator.has_more() is False

    with pytest.raises(StopIteration):
        iterator.next()

    assert len(table.scan_calls) == 1


def test_empty_page_with_last_key_does_not_end_iteration():
    """Una página vacía puede estar seguida por otra página."""
    table = FakeTable(
        [
            {
                "Items": [],
                "LastEvaluatedKey": {"id": "cursor-1"},
            },
            {"Items": [{"id": "2"}]},
        ]
    )
    iterator = TableScanIterator(table)

    assert iterator.has_more() is True
    assert iterator.next() == {"id": "2"}
    assert len(table.scan_calls) == 2


def test_second_page_uses_last_evaluated_key():
    """La siguiente página comienza desde la clave anterior."""
    table = FakeTable(
        [
            {
                "Items": [{"id": "1"}],
                "LastEvaluatedKey": {"id": "1"},
            },
            {"Items": [{"id": "2"}]},
        ]
    )
    iterator = TableScanIterator(table)

    assert iterator.next() == {"id": "1"}
    assert iterator.next() == {"id": "2"}

    assert table.scan_calls[0] == {}
    assert table.scan_calls[1] == {"ExclusiveStartKey": {"id": "1"}}


def test_has_more_is_idempotent():
    """Repetir has_more no consume registros ni solicita páginas extra."""
    table = FakeTable(
        [
            {
                "Items": [{"id": "1"}, {"id": "2"}],
                "LastEvaluatedKey": {"id": "2"},
            },
            {"Items": [{"id": "3"}]},
        ]
    )
    iterator = TableScanIterator(table)

    assert iterator.has_more() is True
    assert iterator.has_more() is True
    assert iterator.has_more() is True
    assert len(table.scan_calls) == 1

    assert iterator.next() == {"id": "1"}
    assert len(table.scan_calls) == 1


def test_scan_error_is_wrapped_and_chained():
    """Un error de boto3 se convierte en DataAccessError conservando la causa."""
    original_error = ClientError(
        {
            "Error": {
                "Code": "InternalServerError",
                "Message": "Fallo simulado",
            }
        },
        "Scan",
    )
    table = FakeTable([original_error])
    iterator = TableScanIterator(table)

    with pytest.raises(DataAccessError) as exc_info:
        iterator.has_more()

    assert exc_info.value.__cause__ is original_error
