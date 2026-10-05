"""
Módulo de pruebas unitarias para el Patrón Observer utilizando pytest.
"""

import pytest

from SingletonProxyObserverTPFI.app.observer.observer import (
    Observer,
    ObserverUnavailableError,
    SubscriptionManager,
)


class MockObserver(Observer):
    """Observador mock para verificar el éxito de las notificaciones."""

    def __init__(self, uuid_cliente: str):
        self.uuid_cliente = uuid_cliente
        self.mensajes_recibidos = []

    def update(self, message: dict) -> None:
        self.mensajes_recibidos.append(message)


class FaultyObserver(Observer):
    """Observador mock que simula un fallo y lanza ObserverUnavailableError."""

    def __init__(self, uuid_cliente: str):
        self.uuid_cliente = uuid_cliente

    def update(self, message: dict) -> None:
        raise ObserverUnavailableError(
            f"Cliente {self.uuid_cliente} no disponible."
        )


@pytest.fixture
def subscription_manager():
    """Fixture que retorna una instancia fresca del SubscriptionManager."""
    return SubscriptionManager()


@pytest.fixture
def observador_normal():
    """Fixture que retorna un observador normal operativo."""
    return MockObserver(uuid_cliente="CLIENTE-001")


def test_subscribe(subscription_manager, observador_normal):
    subscription_manager.subscribe(observador_normal)
    assert observador_normal in subscription_manager._observers


def test_unsubscribe(subscription_manager, observador_normal):
    subscription_manager.subscribe(observador_normal)
    subscription_manager.unsubscribe(observador_normal)
    assert observador_normal not in subscription_manager._observers


@pytest.mark.parametrize(
    "mensaje_prueba",
    [
        {
            "UUID": "12345",
            "ID": "REG-01",
            "action": "change",
            "data": {"sede": "Paraná"},
        },
        {
            "UUID": "67890",
            "ID": "REG-02",
            "action": "change",
            "data": {"sede": "FCyT"},
        },
    ],
)
def test_notify_subscribers_exitoso(
    subscription_manager, observador_normal, mensaje_prueba
):
    subscription_manager.subscribe(observador_normal)
    subscription_manager.notify_subscribers(mensaje_prueba)

    assert len(observador_normal.mensajes_recibidos) == 1
    assert observador_normal.mensajes_recibidos[0] == mensaje_prueba


def test_notify_subscribers_maneja_excepcion_y_desuscribe(
    subscription_manager,
):
    """Verifica que si un observador lanza ObserverUnavailableError, es removido automáticamente y los demás siguen recibiendo notificaciones."""
    obs_bueno = MockObserver(uuid_cliente="CLIENTE-OK")
    obs_malo = FaultyObserver(uuid_cliente="CLIENTE-FAIL")

    subscription_manager.subscribe(obs_bueno)
    subscription_manager.subscribe(obs_malo)

    mensaje = {"UUID": "SYS", "ID": "REG-99", "action": "change", "data": {}}

    subscription_manager.notify_subscribers(mensaje)

    assert len(obs_bueno.mensajes_recibidos) == 1
    assert obs_malo not in subscription_manager._observers
    assert obs_bueno in subscription_manager._observers
