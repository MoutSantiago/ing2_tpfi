"""Tests unitarios de la interfaz Iterator.

Se verifica el contrato del patrón iterator: la clase abstracta no puede
instanciarse, las implementaciones concretas son instancias de la interfaz y
el recorrido se comporta igual en todos los iteradores (has_more idempotente,
next avanza y, al agotarse, has_more da False y next lanza StopIteration).

Como las clases concretas del diseño (TableScanIterator y SingleRecordIterator)
todavía no existen en el código fuente, se usan dobles de prueba locales que
respetan el mismo contrato para poder ejercitarlo.
"""

import pytest

from IteratorCorporateData.app.exceptions import DataAccessError
from IteratorCorporateData.app.recordIterator import Iterator


class TableScanIterator(Iterator):
    """Doble de prueba: recorre todos los registros de un scan."""

    def __init__(self, records: list[dict]) -> None:
        self._records = list(records)
        self._index = 0

    def has_more(self) -> bool:
        return self._index < len(self._records)

    def next(self) -> dict:
        if not self.has_more():
            raise StopIteration
        record = self._records[self._index]
        self._index += 1
        return record


class SingleRecordIterator(Iterator):
    """Doble de prueba: recorre un único registro."""

    def __init__(self, record: dict) -> None:
        self._record = record
        self._consumed = False

    def has_more(self) -> bool:
        return not self._consumed

    def next(self) -> dict:
        if self._consumed:
            raise StopIteration
        self._consumed = True
        return self._record


RECORDS = [
    {"id": "registro-1"},
    {"id": "registro-2"},
    {"id": "registro-3"},
]


@pytest.fixture(params=["table_scan", "single_record"])
def iterator_and_expected(request):
    """Devuelve un iterador concreto y los registros que debe entregar."""
    if request.param == "table_scan":
        return TableScanIterator(RECORDS), RECORDS
    return SingleRecordIterator(RECORDS[0]), [RECORDS[0]]


def test_iterator_cannot_be_instantiated():
    """La interfaz abstracta no debe poder instanciarse."""
    with pytest.raises(TypeError):
        Iterator()  # type: ignore


def test_subclass_without_methods_stays_abstract():
    """Una subclase sin implementar los métodos sigue siendo abstracta."""

    class IncompleteIterator(Iterator):
        pass

    with pytest.raises(TypeError):
        IncompleteIterator()  # type: ignore


def test_table_scan_iterator_is_an_iterator():
    """TableScanIterator implementa la interfaz Iterator."""
    assert isinstance(TableScanIterator(RECORDS), Iterator)


def test_single_record_iterator_is_an_iterator():
    """SingleRecordIterator implementa la interfaz Iterator."""
    assert isinstance(SingleRecordIterator(RECORDS[0]), Iterator)


def test_has_more_is_idempotent(iterator_and_expected):
    """has_more no avanza el recorrido: repetirlo da el mismo resultado."""
    iterator, _ = iterator_and_expected

    first = iterator.has_more()
    assert first is True
    assert iterator.has_more() is first
    assert iterator.has_more() is first


def test_next_advances_and_returns_each_record(iterator_and_expected):
    """next devuelve los registros en orden y avanza el recorrido."""
    iterator, expected = iterator_and_expected

    for record in expected:
        assert iterator.has_more() is True
        assert iterator.next() == record


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


class FailingIterator(Iterator):
    """Doble de prueba: simula una falla de acceso a la base."""

    def has_more(self) -> bool:
        raise DataAccessError("No se pudo acceder a la base de datos.")

    def next(self) -> dict:
        raise DataAccessError("No se pudo acceder a la base de datos.")


def test_has_more_can_raise_data_access_error():
    """has_more puede lanzar DataAccessError si falla la base."""
    with pytest.raises(DataAccessError):
        FailingIterator().has_more()


def test_next_can_raise_data_access_error():
    """next puede lanzar DataAccessError si falla la base."""
    with pytest.raises(DataAccessError):
        FailingIterator().next()
