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

from abc import ABC, abstractmethod

# La excepción vive en .exceptions (allí la define el servidor y la captura
# Server._handle_client). Se re-exporta desde acá para mantener compatibles
# los imports históricos: from .observer import ObserverUnavailableError
from ..exceptions import ObserverUnavailableError

__all__ = ["Observer", "ObserverUnavailableError"]


class Observer(ABC):
    """
    Interfaz abstracta para los observadores del patrón Observer.

    Cualquier clase que quiera ser registrada en un Publisher debe
    implementar el método ``update``.
    """

    @abstractmethod
    def update(self, message: dict) -> None:
        """
        Recibe una notificación publicada por el Publisher.

        Args:
            message: Diccionario que contiene la información de la
                modificación realizada sobre CorporateData.

        Raises:
            ObserverUnavailableError: si el observer no puede recibir
                la notificación.
        """
        pass
