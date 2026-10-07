"""Módulo que maneja los subscriptores.

Modulo que implementa al publisher concreto del patrón observer.
Mantiene la lista de clientes suscriptos y los notifica cada vez que se produce
un cambio en los datos.

Patrón: Observer

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

from threading import RLock

from .observer import Observer, ObserverUnavailableError
from .publisher import Publisher


class SubscriptionManager(Publisher):
    """Clase SubscriptionManager.

    Clase que implementa al publisher concreto del patrón observer.
    Mantiene la lista de clientes suscriptos y los notifica cada vez que se
    produce un cambio en los datos.

    Args:
        Publisher (Publisher): Interfaz Publisher.
    """

    _observers: list[Observer]
    """Lista de observers suscriptos a este publisher."""

    _lock: RLock
    """Protege el acceso a _observers y _last_change, ya que el servidor
    atiende varios clientes en simultáneo."""

    _last_change: dict
    """Almacena el último mensaje de cambio publicado, que es el estado del
    publisher."""

    def __init__(self) -> None:
        """Método constructor de la clase, inicializa los atributos vacios."""
        self._observers = []
        self._lock = RLock()
        self._last_change = {}

    def subscribe(self, observer: Observer) -> None:
        """Permite que un observer se suscriba a este publisher.

        Agrega el observer a _observers (bajo _lock). Si ese mismo objeto ya
        estaba en la lista, no lo agrega de nuevo.

        Args:
            observer (Observer): Observer que se va a subscribir
        """
        with self._lock:
            if observer not in self._observers:
                self._observers.append(observer)

    def unsubscribe(self, observer: Observer) -> None:
        """Elimina al observer de la lista de suscriptores.

        Utiliza _lock para evitar errores con los hilos.
        Si no estaba suscripto, no hace nada.

        Args:
            observer (Observer): Observer que se quiere desubscribir.
        """
        with self._lock:
            if observer in self._observers:
                self._observers.remove(observer)

    def notify_subscribers(self) -> None:
        """Envía _last_change a todos los suscriptores.

        Invoca el método update de cada observer.
        Si alguno lanza ObserverUnavailableError, lo desusbcribe y lo cierra, y
        continúa con los demás.
        """
        observers_to_remove = []
        with self._lock:
            for observer in self._observers:
                try:
                    observer.update(self._last_change)
                except ObserverUnavailableError:
                    observers_to_remove.append(observer)
            for observer in observers_to_remove:
                self._observers.remove(observer)

    def publish_change(self, message: dict) -> None:
        """Publica un cambio.

        Guarda message en _last_change y llama a notify_subscribers(),
        todo bajo _lock para que dos cambios simultáneos no se mezclen.

        Args:
            message (dict): Mensaje a publicar.
        """
        with self._lock:
            self._last_change = message
            self.notify_subscribers()
