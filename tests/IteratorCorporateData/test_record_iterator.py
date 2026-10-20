"""Tests unitarios de la interfaz Iterator.

Se verifica que la interfaz sea abstracta, que las implementaciones
respeten el contrato y que los errores de acceso a datos se propaguen.
"""

import pytest

from IteratorCorporateData.app.exceptions import DataAccessError
from IteratorCorporateData.app.record_iterator import Iterator


class TableScanIterator(Iterator):
    """Doble de prueba que recorre todos los registros."""

    def __init__(self, records: list[dict]) -> None:
        self._records = list(records)
        self._index = 0

    def has_more(self) -> bool:
        """Indica si quedan registros sin avanzar."""
        return self._index < len(self._records)

    def next(self) -> dict:
        """Devuelve el siguiente registro y avanza."""
        if not self.has_more():
            raise StopIteration

        record = self._records[self._index]
        self._index += 1
        return record


class SingleRecordIterator(Iterator):
    """Doble de prueba que recorre un único registro."""

    def __init__(self, record: dict) -> None:
        self._record = record
        self._consumed = False

    def has_more(self) -> bool:
        """Indica si el registro todavía no fue consumido."""
        return not self._consumed

    def next(self) -> dict:
        """Devuelve el registro una sola vez."""
        if self._consumed:
            raise StopIteration

        self._consumed = True
        return self._record


class FailingIterator(Iterator):
    """Doble de prueba que simula un fallo de acceso a datos."""

    def has_more(self) -> bool:
        """Simula un fallo al consultar si quedan registros."""
        raise DataAccessError("No se pudo acceder a la base de datos.")

    def next(self) -> dict:
        """Simula un fallo al recuperar el siguiente registro."""
        raise DataAccessError("No se pudo acceder a la base de datos.")


RECORDS = [
    {"id": "registro-1"},
    {"id": "registro-2"},
    {"id": "registro-3"},
]


@pytest.fixture(params=["table_scan", "single_record"])
def iterator_and_expected(request):
    """Devuelve un iterador y los registros que debe entregar."""
    if request.param == "table_scan":
        return TableScanIterator(RECORDS), RECORDS

    return SingleRecordIterator(RECORDS[0]), [RECORDS[0]]


def test_table_scan_iterator_is_an_iterator():
    """El iterador de recorrido completo implementa la interfaz."""
    assert isinstance(TableScanIterator(RECORDS), Iterator)


def test_single_record_iterator_is_an_iterator():
    """El iterador de registro único implementa la interfaz."""
    assert isinstance(SingleRecordIterator(RECORDS[0]), Iterator)


def test_has_more_is_idempotent(iterator_and_expected):
    """Repetir has_more no debe avanzar el recorrido."""
    iterator, _ = iterator_and_expected

    first_result = iterator.has_more()

    assert first_result is True
    assert iterator.has_more() is first_result
    assert iterator.has_more() is first_result


def test_next_advances_and_returns_each_record(iterator_and_expected):
    """next devuelve los registros esperados en el orden correcto."""
    iterator, expected = iterator_and_expected

    for record in expected:
        assert iterator.has_more() is True
        assert iterator.next() == record

    assert iterator.has_more() is False


def test_exhausted_iterator_has_more_false_and_next_raises(
    iterator_and_expected,
):
    """Al agotarse, has_more da False y next lanza StopIteration."""
    iterator, expected = iterator_and_expected

    for _ in expected:
        iterator.next()

    assert iterator.has_more() is False
    assert iterator.has_more() is False

    with pytest.raises(StopIteration):
        iterator.next()


def test_has_more_can_raise_data_access_error():
    """has_more puede propagar un error de acceso a datos."""
    iterator = FailingIterator()

    with pytest.raises(DataAccessError):
        iterator.has_more()


def test_next_can_raise_data_access_error():
    """next puede propagar un error de acceso a datos."""
    iterator = FailingIterator()

    with pytest.raises(DataAccessError):
        iterator.next()
