"""Tests unitarios de CorporateDataCollection.

Se verifica que la colección concreta cree el iterador correcto según se
pida o no un id, que cada llamada devuelva un iterador nuevo e
independiente, que crear el iterador no consulte la tabla y que cumpla la
interfaz Collection.
"""

from IteratorCorporateData.app.corporate_data_collection import (
    CorporateDataCollection,
)
from IteratorCorporateData.app.iterable_collection import Collection
from IteratorCorporateData.app.recordIterator import Iterator
from IteratorCorporateData.app.single_record_iterator import (
    SingleRecordIterator,
)
from IteratorCorporateData.app.tableScanIterator import TableScanIterator


class FakeTable:
    """Tabla falsa que cuenta las llamadas a get_item y scan."""

    def __init__(self) -> None:
        self.get_item_calls: list[dict] = []
        self.scan_calls: list[dict] = []

    def get_item(self, Key: dict) -> dict:
        """Registra la llamada y devuelve una respuesta vacía."""
        self.get_item_calls.append(Key)
        return {}

    def scan(self, **kwargs) -> dict:
        """Registra la llamada y devuelve una página vacía."""
        self.scan_calls.append(kwargs)
        return {"Items": []}


def test_collection_is_an_iterable_collection():
    """La colección concreta implementa la interfaz Collection."""
    assert isinstance(CorporateDataCollection(FakeTable()), Collection)


def test_create_iterator_without_id_returns_table_scan_iterator():
    """Sin id, create_iterator devuelve un TableScanIterator."""
    table = FakeTable()
    collection = CorporateDataCollection(table)

    iterator = collection.create_iterator()

    assert isinstance(iterator, TableScanIterator)
    assert isinstance(iterator, Iterator)


def test_create_iterator_with_id_returns_single_record_iterator():
    """Con id, create_iterator devuelve un SingleRecordIterator."""
    table = FakeTable()
    collection = CorporateDataCollection(table, "registro-1")

    iterator = collection.create_iterator()

    assert isinstance(iterator, SingleRecordIterator)
    assert isinstance(iterator, Iterator)


def test_create_iterator_returns_new_independent_objects():
    """Dos llamadas a create_iterator devuelven objetos distintos."""
    table = FakeTable()
    collection = CorporateDataCollection(table)

    first = collection.create_iterator()
    second = collection.create_iterator()

    assert first is not second
    assert type(first) is type(second)


def test_create_iterator_does_not_call_the_table():
    """Crear el iterador no invoca get_item ni scan en la tabla."""
    table = FakeTable()
    collection = CorporateDataCollection(table, "registro-1")

    collection.create_iterator()
    collection.create_iterator()

    assert table.get_item_calls == []
    assert table.scan_calls == []
