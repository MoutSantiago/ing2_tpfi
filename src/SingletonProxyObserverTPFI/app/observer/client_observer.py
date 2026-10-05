"""Módulo que define a los observers concretos del patrón observer.

Cada instancia representa a un cliente suscripto y, cuando el publisher
lo notifica, le envía el mensaje a través del socket que quedó abierto en la
suscripción.

Patrón: Observer

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

"""
Módulo que implementa el cliente observador concreto (ClientObserver)
para la gestión de notificaciones a través de sockets en el patrón Observer.
"""

import json
import logging
import socket
from typing import Any, Dict

# Importa la excepción desde el módulo de excepciones o de observer según corresponda
from .observer import Observer, ObserverUnavailableError


class ClientObserver(Observer):
    """
    Define a los observers concretos del patrón observer. Cada instancia representa
    a un cliente suscripto y, cuando el publisher lo notifica, le envía el mensaje
    a través del socket que quedó abierto en la suscripción.
    """

    def __init__(self, sock: socket.socket, uuid: str) -> None:
        """
        Método constructor de la clase. Recibe el socket de la conexión con el cliente
        y su uuid, y los guarda en atributos privados.
        """
        self._sock: socket.socket = sock
        self._uuid: str = uuid

    @property
    def uuid(self) -> str:
        """Propiedad pública de solo lectura que expone el valor de _uuid."""
        return self._uuid

    def update(self, message: Dict[str, Any]) -> None:
        """
        Implementación del método de la interfaz Observer.
        Serializa el message a JSON y lo envía por el socket (_sock).
        Si el envío falla, lanza ObserverUnavailableError.
        """
        try:
            # Serializa el diccionario a formato JSON y lo codifica a bytes con salto de línea
            mensaje_json = json.dumps(message) + "\n"
            self._sock.sendall(mensaje_json.encode("utf-8"))
            logging.info(
                f"[ClientObserver] Notificación enviada exitosamente al cliente UUID: {self._uuid}"
            )
        except (socket.error, OSError, Exception) as e:
            logging.error(
                f"[ClientObserver] Error al enviar notificación al socket del cliente {self._uuid}: {e}"
            )
            raise ObserverUnavailableError(
                f"El cliente con UUID {self._uuid} no está disponible o cerró la conexión."
            ) from e

    def close(self) -> None:
        """
        Cierra la conexión con el cliente suscripto (_sock).
        Si el socket ya estaba cerrado, maneja la excepción para no lanzar error.
        """
        try:
            if self._sock:
                self._sock.close()
                logging.info(
                    f"[ClientObserver] Socket cerrado correctamente para el cliente UUID: {self._uuid}"
                )
        except (socket.error, OSError) as e:
            logging.debug(
                f"[ClientObserver] El socket del cliente {self._uuid} ya se encontraba cerrado: {e}"
            )
