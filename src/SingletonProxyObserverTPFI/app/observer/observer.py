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
Define la interfaz base para los observers del patrón Observer.

El módulo contiene:

- Observer: interfaz que deben implementar todos los observers.
- ObserverUnavailableError: excepción utilizada cuando un observer
  no puede recibir una notificación.
"""

from abc import ABC, abstractmethod


class ObserverUnavailableError(Exception):
    """
    Excepción lanzada cuando un observer no puede recibir una notificación.

    Esta excepción permite que el Publisher detecte que un observer
    dejó de estar disponible y pueda eliminarlo de la lista de
    suscriptores sin interrumpir la notificación al resto.
    """

    pass


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
        raise NotImplementedError
