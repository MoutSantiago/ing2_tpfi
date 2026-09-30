"""
Módulo de pruebas unitarias para el Patrón Proxy utilizando pytest.
"""

import pytest

from Socket.Proxy import ProxyCorporateData


@pytest.fixture
def proxy_cliente():
    uuid_test = "CPU-TEST-123456789"
    sesion_test = "uuid-session-abc-xyz"
    return ProxyCorporateData(uuid_cliente=uuid_test, session_id=sesion_test)


def test_proxy_get(proxy_cliente):
    resultado = proxy_cliente.get_data("UADER-FCYT-IS2")
    assert isinstance(resultado, dict)
    assert resultado["id"] == "UADER-FCYT-IS2"
    assert resultado["status"] == "encontrado"


def test_proxy_list(proxy_cliente):
    resultado = proxy_cliente.list_data()
    assert isinstance(resultado, list)
    assert len(resultado) > 0
    assert resultado[0]["id"] == "UADER-FCYT-IS2"


@pytest.mark.parametrize(
    "datos_entrada, esperado",
    [
        (
            {"id": "REG-01", "sede": "FCyT", "cp": "3260"},
            {"id": "REG-01", "sede": "FCyT", "cp": "3260"},
        ),
        (
            {"id": "REG-02", "sede": "Paraná", "cp": "3100"},
            {"id": "REG-02", "sede": "Paraná", "cp": "3100"},
        ),
    ],
)
def test_proxy_set_varios(proxy_cliente, datos_entrada, esperado):
    resultado = proxy_cliente.set_data(datos_entrada)
    assert resultado == esperado
