import inspect
from typing import get_type_hints

import pytest

from SingletonProxyObserverTPFI.app.proxy.corporate_data_interface import (
    CorporateDataInterface,
)

# =============================================================================
# Helpers
# =============================================================================


class CorporateDataDAOStub(CorporateDataInterface):
    """Subclase mínima que representa a CorporateDataDAO."""

    def get(self, id: str, uuid: str) -> dict[str, str]:
        return {"id": id, "CUIT": "30-70925411-8"}

    def set(self, id: str, data: dict[str, str], uuid: str) -> dict[str, str]:
        return {"id": id, **data}

    def list(self, uuid: str) -> list[dict[str, str]]:
        return [{"id": "UADER-FCyT-IS2"}]


class CorporateDataProxyStub(CorporateDataInterface):
    """Subclase mínima que representa a CorporateDataProxy."""

    def get(self, id: str, uuid: str) -> dict[str, str]:
        return {"id": id, "origen": "proxy"}

    def set(self, id: str, data: dict[str, str], uuid: str) -> dict[str, str]:
        return {"id": id, "origen": "proxy", **data}

    def list(self, uuid: str) -> list[dict[str, str]]:
        return [{"id": "UADER-FCyT-IS2", "origen": "proxy"}]


# =============================================================================
# Tests de la interfaz como contrato abstracto
# =============================================================================


def test_interfaz_no_se_puede_instanciar():
    """Verifica que CorporateDataInterface sea abstracta y no se pueda
    instanciar directamente."""
    with pytest.raises(TypeError) as exc_info:
        # La instanciación fallida es justamente lo que se verifica.
        CorporateDataInterface()  # pyright: ignore[reportAbstractUsage]

    assert "abstract" in str(exc_info.value)


def test_interfaz_declara_los_tres_metodos_abstractos():
    """Verifica que get, set y list estén declarados como abstractos."""
    assert CorporateDataInterface.__abstractmethods__ == frozenset(
        {"get", "set", "list"}
    )


def test_interfaz_hereda_de_abc():
    """Verifica que la interfaz herede de abc.ABC."""
    from abc import ABC

    assert issubclass(CorporateDataInterface, ABC)


def test_interfaz_no_expone_metodos_fuera_del_contrato():
    """Verifica que la interfaz solo declare los tres métodos del
    contrato (get, set y list) y ningún otro método público."""
    publicos = {
        nombre
        for nombre in vars(CorporateDataInterface)
        if not nombre.startswith("_")
    }
    assert publicos == {"get", "set", "list"}


# =============================================================================
# Tests de implementacion por subclases
# =============================================================================


def test_subclase_incompleta_no_se_puede_instanciar():
    """Verifica que una subclase que no implementa los tres métodos no
    pueda instanciarse."""

    class Incompleta(CorporateDataInterface):
        def get(self, id: str, uuid: str) -> dict[str, str]:
            return {}

    with pytest.raises(TypeError) as exc_info:
        # La instanciación fallida es justamente lo que se verifica.
        Incompleta()  # pyright: ignore[reportAbstractUsage]

    assert "abstract" in str(exc_info.value)


def test_subclase_solo_con_get_no_se_puede_instanciar():
    """Verifica que implementar solo get no alcanza para instanciar."""

    class SoloGet(CorporateDataInterface):
        def get(self, id: str, uuid: str) -> dict[str, str]:
            return {}

    with pytest.raises(TypeError):
        # La instanciación fallida es justamente lo que se verifica.
        SoloGet()  # pyright: ignore[reportAbstractUsage]


def test_subclase_completa_se_puede_instanciar():
    """Verifica que una subclase que implementa los tres métodos sí se
    pueda instanciar."""
    instancia = CorporateDataDAOStub()

    assert isinstance(instancia, CorporateDataInterface)


@pytest.mark.parametrize(
    "subclase",
    [CorporateDataDAOStub, CorporateDataProxyStub],
)
def test_dao_y_proxy_implementan_la_interfaz(subclase):
    """Verifica que tanto el DAO como el Proxy pueden implementar el
    contrato de CorporateDataInterface."""
    assert issubclass(subclase, CorporateDataInterface)
    assert not getattr(subclase, "__abstractmethods__", frozenset())


@pytest.mark.parametrize(
    "subclase", [CorporateDataDAOStub, CorporateDataProxyStub]
)
def test_dao_y_proxy_heredan_los_tres_metodos(subclase):
    """Verifica que el DAO y el Proxy hereden get, set y list."""
    for metodo in ("get", "set", "list"):
        assert callable(getattr(subclase, metodo))


# =============================================================================
# Tests de las firmas de los metodos
# =============================================================================


def test_firma_de_get():
    """Verifica que get reciba (self, id, uuid)."""
    parametros = list(inspect.signature(CorporateDataInterface.get).parameters)
    assert parametros == ["self", "id", "uuid"]


def test_firma_de_set():
    """Verifica que set reciba (self, id, data, uuid)."""
    parametros = list(inspect.signature(CorporateDataInterface.set).parameters)
    assert parametros == ["self", "id", "data", "uuid"]


def test_firma_de_list():
    """Verifica que list reciba (self, uuid)."""
    parametros = list(
        inspect.signature(CorporateDataInterface.list).parameters
    )
    assert parametros == ["self", "uuid"]


@pytest.mark.parametrize(
    ("metodo", "esperado"),
    [
        ("get", dict[str, str]),
        ("set", dict[str, str]),
        ("list", list[dict[str, str]]),
    ],
)
def test_anotaciones_de_retorno(metodo, esperado):
    """Verifica que los tipos de retorno declarados coincidan con la
    especificacion (dict para get/set, list de dict para list).

    get_type_hints resuelve las anotaciones, que al usar from __future__
    import annotations quedan almacenadas como strings.
    """
    anotaciones = get_type_hints(getattr(CorporateDataInterface, metodo))
    assert anotaciones["return"] == esperado


def test_metodo_list_no_rompe_con_el_builtin_list():
    """Verifica que el metodo list no colisione con el tipo builtin list
    usado en su propia anotacion de retorno."""
    resultado = CorporateDataDAOStub().list("uuid-1")

    assert resultado == [{"id": "UADER-FCyT-IS2"}]
    assert isinstance(resultado, list)
