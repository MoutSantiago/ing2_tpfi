"""Módulo que define cómo se obtiene un iterador sobre CorporateData.

Define la interfaz que implementan las colecciones concretas para obtener
un iterador sobre los registros de la tabla CorporateData.

Patrón: Iterator

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

from abc import ABC, abstractmethod

from IteratorCorporateData.app.record_iterator import Iterator


class Collection(ABC):
    """Define cómo se obtiene un iterador sobre CorporateData."""

    @abstractmethod
    def create_iterator(self) -> Iterator:
        """Crea y devuelve un iterador nuevo.

        Cada llamada devuelve un iterador independiente de los anteriores.
        Crear el iterador no consulta la base de datos.

        Returns:
            Iterator: Iterador nuevo sobre los registros de CorporateData.
        """
        pass
