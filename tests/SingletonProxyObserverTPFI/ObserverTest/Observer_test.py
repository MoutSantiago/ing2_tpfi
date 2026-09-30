"""
Módulo de pruebas unitarias para el Patrón Observer utilizando pytest.
"""

import pytest

from ObserverClient.Observer import (
    ClienteSocketObservador,
    SubjectCorporateData,
)


class MockSocketCliente(ObservadorConcretoMock := ClienteSocketObservador):
    """Clase mock para simular el comportamiento del socket durante los tests."""

    def __init__(self, uuid_cliente: str):
        super().__init__(uuid_cliente, socket_conexion=None)
        self.ultima_notificacion = None

    def actualizar(self, datos_actualizados: dict) -> None:
        self.ultima_notificacion = datos_actualizados


@pytest.fixture
def subject_data():
    """Fixture que retorna una instancia del sujeto observado."""
    return SubjectCorporateData()


@pytest.fixture
def cliente_mock():
    """Fixture que retorna un cliente observador mock."""
    return MockSocketCliente(uuid_cliente="CPU-OBSERVER-999")


def test_agregar_observador(subject_data, cliente_mock):
    subject_data.agregar_observador(cliente_mock)
    assert cliente_mock in subject_data._observadores


def test_remover_observador(subject_data, cliente_mock):
    subject_data.agregar_observador(cliente_mock)
    subject_data.remover_observador(cliente_mock)
    assert cliente_mock not in subject_data._observadores


@pytest.mark.parametrize(
    "datos_cambio",
    [
        {"id": "REG-10", "sede": "Paraná", "cp": "3100"},
        {"id": "REG-20", "sede": "Concepción", "cp": "3260"},
    ],
)
def test_notificar_observadores(subject_data, cliente_mock, datos_cambio):
    subject_data.agregar_observador(cliente_mock)
    subject_data.notificar_observadores(datos_cambio)

    assert cliente_mock.ultima_notificacion == datos_cambio
