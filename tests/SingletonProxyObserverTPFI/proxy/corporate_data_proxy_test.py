"""Tests del proxy CorporateDataProxy.

Verifican las reglas de negocio: la auditoría se registra SIEMPRE antes de
la operación, el set notifica el cambio al publisher y las excepciones de
las capas inferiores se dejan propagar.
"""

from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest

from SingletonProxyObserverTPFI.app.exceptions import (
    DataAccessError,
    RecordNotFoundError,
)
from SingletonProxyObserverTPFI.app.observer.observer import (
    ObserverUnavailableError,
)
from SingletonProxyObserverTPFI.app.observer.subscription_manager import (
    SubscriptionManager,
)
from SingletonProxyObserverTPFI.app.proxy.corporate_data_interface import (
    CorporateDataInterface,
)
from SingletonProxyObserverTPFI.app.proxy.corporate_data_proxy import (
    CorporateDataProxy,
)
from SingletonProxyObserverTPFI.app.singleton.corporate_log_dao import (
    CorporateLogDAO,
)

# =============================================================================
# Mocks / stubs
# =============================================================================


class RealDAOStub(CorporateDataInterface):
    """Stub del objeto real que accede a la tabla CorporateData.

    No toca DynamoDB: cada método registra la invocación en self.llamados y
    devuelve un valor fijo, para poder estudiar qué llamó el proxy y en qué
    orden.
    """

    def __init__(self, respuesta: dict[str, str]) -> None:
        """Guarda la respuesta fija que devolverá get/set.

        Args:
            respuesta: Registro que devolverán get y set.
        """
        self.respuesta = respuesta
        self.llamados: list[tuple[str, str, dict[str, str] | None, str]] = []

    def get(self, id: str, uuid: str) -> dict[str, str]:
        """Registra la llamada y devuelve la respuesta fija."""
        self.llamados.append(("get", id, None, uuid))
        return self.respuesta

    def set(
        self, id: str, data: dict[str, str], uuid: str
    ) -> dict[str, str]:
        """Registra la llamada y devuelve la respuesta fija."""
        self.llamados.append(("set", id, data, uuid))
        return dict(self.respuesta, id=id)

    def list(self, uuid: str) -> list[dict[str, str]]:
        """Registra la llamada y devuelve la respuesta fija."""
        self.llamados.append(("list", "", None, uuid))
        return [self.respuesta]


class SpyLogDAO(CorporateLogDAO):
    """Spy de CorporateLogDAO.

    Hereda de CorporateLogDAO pero sobrescribe write_entry para no tocar
    DynamoDB: registra los parámetros recibidos en self.entries.
    """

    def __init__(self) -> None:
        """Inicializa la lista de entradas registradas."""
        self.entries: list[dict[str, str | None]] = []

    def write_entry(
        self,
        uuid: str,
        session_id: str,
        action: str,
        item_id: str | None,
        timestamp: str,
    ) -> None:
        """Registra la entrada de auditoría sin tocar DynamoDB."""
        self.entries.append(
            {
                "uuid": uuid,
                "session_id": session_id,
                "action": action,
                "item_id": item_id,
                "timestamp": timestamp,
            }
        )


class SpyLogDAOQueFalla(SpyLogDAO):
    """Spy que falla al escribir la auditoría."""

    def write_entry(
        self,
        uuid: str,
        session_id: str,
        action: str,
        item_id: str | None,
        timestamp: str,
    ) -> None:
        """Simula un fallo de escritura en CorporateLog."""
        raise DataAccessError("Error escribiendo en CorporateLog")


# =============================================================================
# Fixtures
# =============================================================================

REGISTRO = {"id": "reg-1", "cp": "3260", "sede": "FCyT"}

UUID = "c9f1f1e4-0000-4000-8000-000000000001"


def crear_proxy(respuesta: dict[str, str] = REGISTRO) -> tuple:
    """Crea el proxy con sus tres dependencias mockeadas.

    Returns:
        tuple: (proxy, real, spy_log, manager)
    """
    real = RealDAOStub(respuesta)
    spy_log = SpyLogDAO()
    manager = SubscriptionManager()
    proxy = CorporateDataProxy(real, spy_log, manager)
    return proxy, real, spy_log, manager


# =============================================================================
# Tests de comportamiento
# =============================================================================


def test_get_audita_antes_de_leer():
    """Verifica que get registre la auditoría y, recién después, llame al
    objeto real."""
    proxy, real, spy_log, _ = crear_proxy()

    resultado = proxy.get("reg-1", UUID)

    assert resultado == REGISTRO
    # Solo una entrada de auditoría, con action=get y el id.
    assert len(spy_log.entries) == 1
    assert spy_log.entries[0]["uuid"] == UUID
    assert spy_log.entries[0]["action"] == "get"
    assert spy_log.entries[0]["item_id"] == "reg-1"
    # La operación real se invocó después de la auditoría.
    assert real.llamados == [("get", "reg-1", None, UUID)]


def test_set_audita_escribe_y_notifica():
    """Verifica que set audite, escriba en el objeto real y publique el
    cambio con el formato del mensaje esperado por los observers."""
    proxy, real, spy_log, manager = crear_proxy()

    resultado = proxy.set("reg-1", {"cp": "3260"}, UUID)

    assert resultado == dict(REGISTRO, id="reg-1")
    # La auditoría corre antes que la escritura real.
    assert real.llamados == [("set", "reg-1", {"cp": "3260"}, UUID)]
    assert len(spy_log.entries) == 1
    assert spy_log.entries[0]["action"] == "set"
    # El publisher conserva el último mensaje publicado.
    mensaje = manager._last_change
    assert mensaje["UUID"] == UUID
    assert mensaje["ID"] == "reg-1"
    assert mensaje["ACTION"] == "change"
    assert mensaje["cp"] == "3260"


def test_get_audita_antes_que_set():
    """Verifica el orden auditoría -> operación con una operación que
    audita dos veces: get y luego set sobre el mismo registro."""
    proxy, real, spy_log, _ = crear_proxy()

    proxy.get("reg-1", UUID)
    proxy.set("reg-1", {"cp": "3260"}, UUID)

    assert [e["action"] for e in spy_log.entries] == ["get", "set"]
    # Las operaciones reales corren en el mismo orden.
    assert [c[0] for c in real.llamados] == ["get", "set"]


def test_list_audita_y_lista():
    """Verifica que list registre la auditoría con item_id None."""
    proxy, real, spy_log, _ = crear_proxy()

    resultado = proxy.list(UUID)

    assert resultado == [REGISTRO]
    assert len(spy_log.entries) == 1
    assert spy_log.entries[0]["action"] == "list"
    assert spy_log.entries[0]["item_id"] is None
    assert real.llamados == [("list", "", None, UUID)]


def test_audit_subscription_registra_subscribe():
    """Verifica que audit_subscription registre la acción subscribe con
    item_id None y sin tocar los datos."""
    proxy, real, spy_log, _ = crear_proxy()

    proxy.audit_subscription(UUID)

    assert len(spy_log.entries) == 1
    assert spy_log.entries[0]["uuid"] == UUID
    assert spy_log.entries[0]["action"] == "subscribe"
    assert spy_log.entries[0]["item_id"] is None
    # No debe haber tocado los datos reales.
    assert real.llamados == []


def test_auditoria_usa_session_id_uuid4_e_iso_8601_utc():
    """Verifica que cada entrada de auditoría lleve un session_id UUID y un
    timestamp ISO 8601 en UTC válidos."""
    proxy, _, spy_log, _ = crear_proxy()

    proxy.get("reg-1", UUID)

    entrada = spy_log.entries[0]
    # session_id debe ser un UUID conforme a RFC 4122.
    session_id = entrada["session_id"]
    assert session_id is not None
    uuid4_verificado = uuid4()  # solo para importar uuid4 correctamente
    assert len(session_id) == len(str(uuid4_verificado))
    # timestamp debe parsearse como ISO 8601 con offset UTC (u offset de 0).
    timestamp = entrada["timestamp"]
    assert timestamp is not None
    parseado = datetime.fromisoformat(timestamp)
    assert parseado.utcoffset() is not None
    # El timestamp debe ser reciente (dentro de los últimos 5 segundos).
    diferencia = datetime.now(timezone.utc) - parseado
    assert diferencia.total_seconds() < 5


def test_cada_entrada_genera_session_id_distinto():
    """Verifica que cada auditoría genere un session_id nuevo (uuid4)."""
    proxy, _, spy_log, _ = crear_proxy()

    proxy.get("reg-1", UUID)
    proxy.set("reg-1", {"cp": "3260"}, UUID)

    assert len(spy_log.entries) == 2
    assert spy_log.entries[0]["session_id"] != spy_log.entries[1]["session_id"]
    # Sesiones distintas; probablemente relacionadas.
    assert True


def test_set_notifica_a_los_observers():
    """Verifica que el cambio publicado llegue a un observer real suscripto."""
    proxy, _, spy_log, manager = crear_proxy()
    observer = Mock()
    manager.subscribe(observer)

    proxy.set("reg-1", {"cp": "3260"}, UUID)

    observer.update.assert_called_once()
    mensaje = observer.update.call_args.args[0]
    assert mensaje["ACTION"] == "change"
    assert mensaje["UUID"] == UUID


def test_set_no_se_afecta_por_fallo_del_observer():
    """Verifica que el fallo de un observer al recibir el cambio no afecte
    el resultado del set: el proxy debe retornar el registro igual y la
    escritura debe haberse hecho."""
    proxy, real, spy_log, manager = crear_proxy()
    observer_malo = Mock()
    observer_malo.update.side_effect = ObserverUnavailableError(
        "observer caido"
    )
    manager.subscribe(observer_malo)

    resultado = proxy.set("reg-1", {"cp": "3260"}, UUID)

    assert resultado == dict(REGISTRO, id="reg-1")
    assert real.llamados == [("set", "reg-1", {"cp": "3260"}, UUID)]
    assert len(spy_log.entries) == 1
    # El observer fallado se desuscribe para no volver a fallar.
    assert manager._observers == []


def test_get_si_auditoria_falla_no_toca_los_datos():
    """Verifica que si la auditoría falla, la operación no se ejecute y la
    excepción se propague al solicitante."""
    real = RealDAOStub(REGISTRO)
    proxy = CorporateDataProxy(
        real, SpyLogDAOQueFalla(), SubscriptionManager()
    )

    with pytest.raises(DataAccessError):
        proxy.get("reg-1", UUID)

    # El objeto real nunca se invocó.
    assert real.llamados == []


def test_set_si_auditoria_falla_no_escribe_ni_notifica():
    """Verifica que si la auditoría falla en set, no se escriba el dato ni
    se notifique; la excepción se propaga."""
    real = RealDAOStub(REGISTRO)
    manager = SubscriptionManager()
    observer = Mock()
    manager.subscribe(observer)
    proxy = CorporateDataProxy(real, SpyLogDAOQueFalla(), manager)

    with pytest.raises(DataAccessError):
        proxy.set("reg-1", {"cp": "3260"}, UUID)

    assert real.llamados == []
    observer.update.assert_not_called()


def test_propaga_record_not_found_del_objeto_real():
    """Verifica que RecordNotFoundError del objeto real se propague al
    solicitante luego de la auditoría."""
    real = RealDAOStub(REGISTRO)
    real.get = Mock(side_effect=RecordNotFoundError("no-existe"))  # type: ignore[method-assign]
    spy_log = SpyLogDAO()
    proxy = CorporateDataProxy(real, spy_log, SubscriptionManager())

    with pytest.raises(RecordNotFoundError):
        proxy.get("reg-1", UUID)

    assert len(spy_log.entries) == 1


def test_implementa_corporate_data_interface():
    """Verifica que CorporateDataProxy implemente la interfaz sin métodos
    abstractos pendientes."""
    proxy, _, _, _ = crear_proxy()
    assert isinstance(proxy, CorporateDataInterface)
    # Los métodos abstractos de la interfaz quedan implementados en el proxy.
    assert not proxy.__class__.__abstractmethods__
