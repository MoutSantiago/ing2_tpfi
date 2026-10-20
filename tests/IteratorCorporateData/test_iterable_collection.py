"""Tests unitarios de la interfaz Collection.

Se verifica que Collection sea abstracta, que create_iterator sea un
método abstracto, que una implementación concreta devuelva un Iterator
por llamada, que cada iterador sea independiente y que crear el
iterador no consulte la base de datos.
"""

from IteratorCorporateData.app.iterable_collection import Collection
from IteratorCorporateData.app.record_iterator import Iterator


class TableScanIterator(Iterator):
    """Doble de prueba que recorre todos los registros en memoria."""

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


class SpyCollection(Collection):
    """Colección de prueba que cuenta las llamadas a create_iterator."""

    def __init__(self, records: list[dict]) -> None:
        self._records = records
        self.create_iterator_calls = 0

    def create_iterator(self) -> Iterator:
        """Crea un iterador nuevo y registra la llamada."""
        self.create_iterator_calls += 1
        return TableScanIterator(self._records)


class NoDbCollection(Collection):
    """Colección de prueba cuyo create_iterator no consulta la BD."""

    def __init__(self, records: list[dict]) -> None:
        self._records = records
        self.queries: list[str] = []

    def create_iterator(self) -> Iterator:
        """Crea el iterador sin consultar la base de datos."""
        return TableScanIterator(self._records)

    def query_database(self) -> None:
        """Simula una consulta a la base de datos."""
        self.queries.append("SELECT * FROM corporate_data")


RECORDS = [
    {"id": "registro-1", "nombre": "Ana"},
    {"id": "registro-2", "nombre": "Luis"},
    {"id": "registro-3", "nombre": "Carla"},
]


def test_collection_is_abstract():
    """Collection no se puede instanciar directamente."""
    assert Collection.__abstractmethods__ == {"create_iterator"}


def test_create_iterator_is_abstract():
    """create_iterator es un método abstracto de Collection."""
    assert "create_iterator" in Collection.__abstractmethods__


def test_concrete_collection_is_not_abstract():
    """Una subclase que implementa create_iterator se puede instanciar."""
    collection = SpyCollection(RECORDS)

    assert isinstance(collection, Collection)


def test_create_iterator_returns_an_iterator():
    """create_iterator devuelve un objeto que implementa Iterator."""
    collection = SpyCollection(RECORDS)
    iterator = collection.create_iterator()

    assert isinstance(iterator, Iterator)


def test_each_call_returns_independent_iterator():
    """Cada llamada a create_iterator devuelve un iterador distinto."""
    collection = SpyCollection(RECORDS)

    first = collection.create_iterator()
    second = collection.create_iterator()

    assert first is not second
    assert collection.create_iterator_calls == 2


def test_iterators_have_independent_traversal():
    """Avanzar un iterador no afecta al recorrido del otro."""
    collection = SpyCollection(RECORDS)

    first = collection.create_iterator()
    second = collection.create_iterator()

    assert first.next() == RECORDS[0]
    assert second.next() == RECORDS[0]
    assert first.next() == RECORDS[1]


def test_create_iterator_does_not_consult_database():
    """Crear el iterador no dispara consultas a la base de datos."""
    collection = NoDbCollection(RECORDS)

    collection.create_iterator()

    assert collection.queries == []
