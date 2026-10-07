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

import json
import logging
import socket

from SingletonProxyObserverTPFI.app.observer.observer import (
    Observer,
    ObserverUnavailableError,
)

logger = logging.getLogger(__name__)


class ClientObserver(Observer):
    """Observer concreto asociado a un cliente TCP suscripto."""

    _sock: socket.socket
    """Socket del cliente suscripto."""

    _uuid: str
    """UUID del cliente suscripto."""

    def __init__(self, sock: socket.socket, uuid: str) -> None:
        """
        Inicializa el observer.

        Args:
            sock: Socket del cliente suscripto.
            uuid: Identificador del cliente.
        """
        self._sock = sock
        self._uuid = uuid

    @property
    def uuid(self) -> str:
        """Devuelve el UUID del cliente suscripto."""
        return self._uuid

    def update(self, message: dict) -> None:
        """
        Envía una notificación JSON al cliente.

        Args:
            message: Mensaje generado por el Publisher.

        Raises:
            ObserverUnavailableError: si no se puede enviar
                la notificación.
        """
        logger.debug("Enviando notificación a observer %s", self._uuid)
        try:
            # Serializamos el mensaje a JSON.
            data = json.dumps(message)

            # Cada mensaje termina en salto de línea para respetar
            # el protocolo de comunicación definido por el TPFI.
            data += "\n"

            # Enviamos el mensaje completo por el socket.
            self._sock.sendall(data.encode("utf-8"))

        except (OSError, TypeError, ValueError) as exc:
            # El Publisher utilizará esta excepción para detectar
            # que el cliente ya no está disponible.
            logger.warning(
                "No se pudo notificar al observer %s: %s", self._uuid, exc
            )
            raise ObserverUnavailableError(
                f"No se pudo notificar al observer {self._uuid}"
            ) from exc

    def close(self) -> None:
        """Cierra el socket del cliente suscripto."""
        logger.debug("Cerrando conexión del observer %s", self._uuid)
        try:
            self._sock.close()
        except OSError:
            # Si el socket ya estaba cerrado, no hacemos nada.
            pass
