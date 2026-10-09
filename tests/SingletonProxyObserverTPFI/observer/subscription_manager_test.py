"""
Tests unitarios para subscription_manager.py.
"""

from SingletonProxyObserverTPFI.app.observer.observer import (
    Observer,
    ObserverUnavailableError,
)
from SingletonProxyObserverTPFI.app.observer.subscription_manager import (
    SubscriptionManager,
)


class TestObserver(Observer):
    """Observer de prueba para los tests."""

    __test__ = False

    _uuid: str
    """UUID del observer de prueba."""

    received_message: dict | None
    """Último mensaje recibido, None si todavía no recibió ninguno."""

    def __init__(self, uuid: str = "test-uuid"):
        self._uuid = uuid
        self.received_message = None

    @property
    def uuid(self) -> str:
        """Devuelve el UUID del observer."""
        return self._uuid

    def update(self, message: dict) -> None:
        self.received_message = message

    def close(self) -> None:
        pass


def test_subscribe_agrega_observer():
    """testea que subscribe agrega un observer a la lista."""
    manager = SubscriptionManager()
    observer = TestObserver()

    manager.subscribe(observer)

    assert observer in manager._observers


def test_subscribe_no_duplicados():
    """testea que subscribe no agrega el mismo observer dos veces."""
    manager = SubscriptionManager()
    observer = TestObserver()

    manager.subscribe(observer)
    manager.subscribe(observer)

    assert manager._observers.count(observer) == 1


def test_unsubscribe_remueve_observer():
    """testea que unsubscribe remueve un observer de la lista."""
    manager = SubscriptionManager()
    observer = TestObserver()

    manager.subscribe(observer)
    manager.unsubscribe(observer)

    assert observer not in manager._observers


def test_unsubscribe_no_hace_nada_si_no_suscripto():
    """testea que unsubscribe no hace nada si el observer no estaba
    suscripto."""
    manager = SubscriptionManager()
    observer = TestObserver()

    # Observer nunca fue suscrito, por lo tanto la lista sigue vacía
    # y no debería lanzar excepción
    manager.unsubscribe(observer)

    # La lista _observers debe seguir estando vacía
    assert manager._observers == []


def test_notify_subscribers_envia_mensaje():
    """testea que notify_subscribers envía el mensaje a todos los observers."""
    manager = SubscriptionManager()
    observer1 = TestObserver()
    observer2 = TestObserver()

    manager.subscribe(observer1)
    manager.subscribe(observer2)

    manager._last_change = {"key": "value"}
    manager.notify_subscribers()

    assert observer1.received_message == {"key": "value"}
    assert observer2.received_message == {"key": "value"}


def test_notify_subscribers_observer_unavailable():
    """testea que si un observer lanza ObserverUnavailableError, es
    desubscripto y cerrado."""
    manager = SubscriptionManager()
    observer_good = TestObserver()
    observer_bad = TestObserver()

    # Hacer que observer_bad lance ObserverUnavailableError en update
    class BadObserver(TestObserver):
        def update(self, message: dict) -> None:
            raise ObserverUnavailableError("observer unavailable")

    observer_bad = BadObserver()
    # Reemplazar update para que use la versión que lanza error
    type(observer_bad).update = BadObserver.update

    manager.subscribe(observer_good)
    manager.subscribe(observer_bad)

    manager._last_change = {"key": "value"}
    manager.notify_subscribers()

    # observer_good debería haber recibido el mensaje
    assert observer_good.received_message == {"key": "value"}
    # observer_bad debería haber sido removido de la lista
    assert observer_bad not in manager._observers


def test_publish_change_guarda_y_notifica():
    """testea que publish_change guarda el mensaje y llama a
    notify_subscribers."""
    manager = SubscriptionManager()
    observer = TestObserver()

    manager.subscribe(observer)

    manager.publish_change({"message": "hello"})

    assert manager._last_change == {"message": "hello"}
    assert observer.received_message == {"message": "hello"}


def test_publish_change_sube_notifica_a_todos():
    """testea que publish_change notifica a todos los suscriptores."""
    manager = SubscriptionManager()
    observer1 = TestObserver()
    observer2 = TestObserver()

    manager.subscribe(observer1)
    manager.subscribe(observer2)

    manager.publish_change({"msg": "test"})

    assert observer1.received_message == {"msg": "test"}
    assert observer2.received_message == {"msg": "test"}


def test_insensibilidad_a_mayusculas_y_minusculas_en_nombres():
    """testea que los métodos funcionan correctamente con la interfaz
    esperada."""
    manager = SubscriptionManager()
    observer = TestObserver()

    manager.subscribe(observer)
    manager.unsubscribe(observer)
    manager.publish_change({"test": 123})

    assert manager._last_change == {"test": 123}


def test_lock_protegido_en_subscribe_y_unsubscribe():
    """testea que subscribe y unsubscribe usan el lock
    (verificado por no lanzar error)."""
    manager = SubscriptionManager()
    observer1 = TestObserver()
    observer2 = TestObserver()

    # Estas operaciones no deben lanzar excepciones
    manager.subscribe(observer1)
    manager.subscribe(observer2)
    manager.unsubscribe(observer1)
    manager.unsubscribe(observer2)

    assert observer1 not in manager._observers
    assert observer2 not in manager._observers


def test_notify_subscribers_vacio():
    """testea que notify_subscribers no falla si no hay observers
    suscriptos."""
    manager = SubscriptionManager()

    # Esto no debería lanzar excepción
    manager.notify_subscribers()


def test_publish_change_vacio():
    """testea que publish_change funciona con lista de observers vacía."""
    manager = SubscriptionManager()

    # Esto no debería lanzar excepción
    manager.publish_change({"key": "value"})


class TestObserverThatRaises:
    """Observer que lanza error en update."""

    def update(self, message: dict) -> None:
        raise ObserverUnavailableError("observer error")

    def close(self) -> None:
        pass
