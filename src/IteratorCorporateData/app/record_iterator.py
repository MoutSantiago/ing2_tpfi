"""Interfaz abstracta para recorrer registros de CorporateData.

Define el contrato que deben cumplir los iteradores concretos
(SingleRecordIterator y TableScanIterator) del patrón Iterator.

Patrón: Iterator

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

from abc import ABC, abstractmethod


class Iterator(ABC):
    """Define el contrato para recorrer registros."""

    @abstractmethod
    def has_more(self) -> bool:
        """Indica si quedan registros sin avanzar el recorrido.

        Returns:
            bool: True si hay al menos un registro más por entregar.
        """
        pass

    @abstractmethod
    def next(self) -> dict:
        """Devuelve el siguiente registro y avanza el recorrido.

        Returns:
            dict: El siguiente registro de CorporateData.

        Raises:
            StopIteration: si no quedan registros por entregar.
        """
        pass
