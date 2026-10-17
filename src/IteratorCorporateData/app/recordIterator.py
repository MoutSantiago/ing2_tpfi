"""Interfaz abstracta para recorrer registros de CorporateData."""

from abc import ABC, abstractmethod


class Iterator(ABC):
    """Define el contrato para recorrer registros de a uno."""

    @abstractmethod
    def has_more(self) -> bool:
        """Indica si quedan registros sin avanzar el recorrido.

        Raises:
            DataAccessError: si falla el acceso a la base de datos.
        """
        pass

    @abstractmethod
    def next(self) -> dict:
        """Devuelve el siguiente registro y avanza el recorrido.

        Raises:
            StopIteration: si no quedan registros.
            DataAccessError: si falla el acceso a la base de datos.
        """
        pass
