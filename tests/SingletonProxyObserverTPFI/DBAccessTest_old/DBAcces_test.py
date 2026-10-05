import pytest

from SingletonProxyObserverTPFI.app.DBAccess_old.DBAccess import (
    DBAccess,
    SingletonMeta,
)


@pytest.fixture(autouse=True)
def reset_singleton():
    SingletonMeta._instances.clear()
    yield
    SingletonMeta._instances.clear()


def test_misma_instancia():
    assert DBAccess() is DBAccess()


def test_cache_registrada():
    SingletonMeta._instances.clear()
    a = DBAccess()
    assert SingletonMeta._instances == {DBAccess: a}


def test_misma_direccion():
    a = DBAccess()
    b = DBAccess()
    assert a.DireccionMemoria() == b.DireccionMemoria()


def test_clases_distintas_no_comparten():
    class Otra(metaclass=SingletonMeta):
        pass

    assert Otra() is not DBAccess()
    assert Otra() is Otra()
