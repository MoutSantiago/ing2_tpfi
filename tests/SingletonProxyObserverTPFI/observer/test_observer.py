"""
Tests unitarios para observer.py.
"""

from SingletonProxyObserverTPFI.app.observer.observer import (
    Observer,
    ObserverUnavailableError,
)


def test_observer_define_update():
    """
    Verifica que Observer defina el método update().
    """

    assert hasattr(Observer, "update")


def test_observer_unavailable_error_es_exception():
    """
    Verifica que ObserverUnavailableError herede de Exception.
    """

    assert issubclass(
        ObserverUnavailableError,
        Exception,
    )


def test_clase_concreta_puede_implementar_observer():
    """
    Verifica que una clase concreta pueda implementar el método
    update() definido por Observer.
    """

    class TestObserver(Observer):
        def update(self, message: dict) -> None:
            self.message = message

    observer = TestObserver()

    message = {
        "UUID": "uuid-123",
        "ID": "registro-1",
        "ACTION": "change",
    }

    observer.update(message)

    assert observer.message == message
