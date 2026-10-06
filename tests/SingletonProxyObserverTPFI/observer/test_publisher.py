"""Tests unitarios para publisher.py (interfaz del patrón Observer)."""

import pytest

from SingletonProxyObserverTPFI.app.observer.publisher import Publisher


class _PublisherDePrueba(Publisher):
    """Implementación concreta mínima del Publisher para los tests."""

    def __init__(self) -> None:
        """Inicializa la lista vacía de suscriptores."""
        self.suscriptores = []

    def subscribe(self, observer) -> None:
        """Agrega un observer a la lista de suscriptores."""
        self.suscriptores.append(observer)


def test_publisher_es_abstracto():
    """Verifica que la interfaz Publisher no se pueda instanciar."""

    with pytest.raises(TypeError):
        # El error de instantiación es intencional: el test verifica
        # que la interfaz sea abstracta.
        Publisher()  # pyright: ignore[reportAbstractUsage]


def test_publisher_concreto_puede_suscribir():
    """Verifica que una subclase concreta pueda suscribir observers."""

    publisher = _PublisherDePrueba()
    observer = object()

    publisher.subscribe(observer)

    assert publisher.suscriptores == [observer]


def test_unsubscribe_de_la_clase_base_no_falla():
    """Verifica que unsubscribe de la interfaz tolera un observer
    desconocido sin lanzar excepciones."""

    publisher = _PublisherDePrueba()

    # La implementación base no hace nada si el observer no estaba.
    resultado = publisher.unsubscribe(object())

    assert resultado is None


def test_notify_subscribers_sin_suscriptores_no_falla():
    """Verifica que notify_subscribers no interrumpa el proceso
    cuando no hay observers ni mensajes pendientes."""

    publisher = _PublisherDePrueba()

    resultado = publisher.notify_subscribers()

    assert resultado is None
