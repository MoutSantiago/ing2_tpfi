"""Interfaz abstracta para recorrer registros de CorporateData."""

from abc import ABC, abstractmethod


class Iterator(ABC):
    """Define el contrato para recorrer registros."""

    @abstractmethod
    def has_more(self) -> bool:
        """Indica si quedan registros sin avanzar el recorrido."""
        raise NotImplementedError

    @abstractmethod
    def next(self) -> dict:
        """Devuelve el siguiente registro y avanza el recorrido."""
        raise NotImplementedError
