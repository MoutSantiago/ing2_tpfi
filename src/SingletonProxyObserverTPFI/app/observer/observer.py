"""Módulo con la interfaz para los observadores del patrón observer.

Define el contrato que debe cumplir cualquier objeto que quiera ser notificado
por un publisher.

Patrón: Observer

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

"""
Módulo que implementa el Patrón Observer con gestión de subscripciones,
manejo de excepciones por desconexión y envío a través de sockets.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ObserverUnavailableError(Exception):
    """
    Excepción que se lanza cuando el observador no puede recibir la notificación
    (por ejemplo, cuando el socket del cliente se encuentra cerrado o interrumpido).
    """

    pass


class Observer(ABC):
    """
    Interfaz base para los observadores del patrón observer.
    Define el contrato que debe cumplir cualquier objeto que quiera ser notificado por un publisher.
    Permite que el publisher dependa de esta abstracción y no directamente del socket.
    """

    @abstractmethod
    def update(self, message: Dict[str, Any]) -> None:
        """
        Método que permite al observer reaccionar a un cambio.
        Recibe un message con el formato de notificación (UUID, ID, acción 'change', datos).
        Lanza ObserverUnavailableError si no puede entregar la notificación.
        """
        pass


class ClientObserver(Observer):
    """
    Implementación concreta de la interfaz Observer.
    Representa a un cliente suscripto y gestiona el envío de notificaciones mediante su socket TCP.
    """

    def __init__(self, uuid_cliente: str, socket_conexion: Any) -> None:
        self.uuid_cliente = uuid_cliente
        self.socket_conexion = socket_conexion

    def update(self, message: Dict[str, Any]) -> None:
        """
        Envía el mensaje de actualización por el socket del cliente.
        Si la conexión falla, lanza ObserverUnavailableError.
        """
        try:
            # Ejemplo de envío por socket:
            # datos_json = json.dumps(message).encode('utf-8')
            # self.socket_conexion.sendall(datos_json)
            logging.info(
                f"[ClientObserver] Notificación enviada exitosamente al cliente UUID: {self.uuid_cliente}"
            )
        except Exception as e:
            logging.error(
                f"[ClientObserver] Error al enviar notificación al socket del cliente {self.uuid_cliente}: {e}"
            )
            raise ObserverUnavailableError(
                f"El observador con UUID {self.uuid_cliente} no está disponible (conexión caída)."
            ) from e


class SubscriptionManager:
    """
    Clase Publisher del patrón Observer. Administra la lista de observadores
    y se encarga de disparar las notificaciones ante cambios en los datos.
    """

    def __init__(self) -> None:
        self._observers: List[Observer] = []

    def subscribe(self, observer: Observer) -> None:
        """Registra un nuevo observador si no se encuentra subscripto previamente."""
        if observer not in self._observers:
            self._observers.append(observer)
            logging.info(
                f"[SubscriptionManager] Nuevo observador subscripto. Total activos: {len(self._observers)}"
            )

    def unsubscribe(self, observer: Observer) -> None:
        """Elimina a un observador de la lista de subscripciones."""
        if observer in self._observers:
            self._observers.remove(observer)
            logging.info(
                f"[SubscriptionManager] Observador desuscripto. Total activos: {len(self._observers)}"
            )

    def notify_subscribers(self, message: Dict[str, Any]) -> None:
        """
        Invoca el método update de cada observador registrado.
        Captura ObserverUnavailableError para desuscribir al cliente inactivo
        sin interrumpir el flujo de notificación hacia el resto de los subscriptores.
        """
        logging.info(
            f"[SubscriptionManager] Iniciando notificación a {len(self._observers)} suscriptores."
        )

        # Se utiliza una copia de la lista ([:]) para evitar modificar la estructura
        # mientras se está iterando sobre ella.
        for observer in self._observers[:]:
            try:
                observer.update(message)
            except ObserverUnavailableError as e:
                logging.warning(
                    f"[SubscriptionManager] {e} -> Desuscribiendo automáticamente."
                )
                self.unsubscribe(observer)
