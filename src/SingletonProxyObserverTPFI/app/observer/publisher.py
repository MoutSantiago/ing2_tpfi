"""Módulo con la interfaz base para el desarrollo de publishers.

Define el contrato que debe cumplir cualquier publisher para gestionar a sus
suscriptores y notificarlos.

Patrón: Observer

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

from abc import ABC, abstractmethod


class Publisher(ABC):
    """Clase abstracta / interfaz publisher.

    Esta clase define los metodos que deben heredar los publishers concretos
    del patrón observer.

    Args:
        ABC (ABC): Define esta calse como clase abstracta.
    """

    @abstractmethod
    def subscribe(observer) -> None:
        """Método subscribe.

        Utilizado para que un observador se suscriba al publisher.
        Agrega el observer a la lista de suscriptores, de modo que reciba las
        notificaciones posteriores.

        Args:
            observer (Observer): Observer que se quiere subscribir a este
            publisher
        """
        pass

    def unsubscribe(observer) -> None:
        """Método unsubscribe.

        Método utilizado para que un observador se desuscriba del publisher.
        Quita el observer de la lista de suscriptores. Si el observador no
        estaba suscripto, no hace nada.

        Args:
            observer (Observer): Observer subscripto que se quiere desubscribir
        """
        pass

    def notify_subscribers() -> None:
        """Método notify_subscribers.

        Método que envía una notificación a todos los suscriptores del
        publisher, invocando el método update de cada uno con el último cambio
        publicado.
        Si la notificación a un suscriptor falla, no debe interrumpir el envío
        a los demás.
        """
        pass
