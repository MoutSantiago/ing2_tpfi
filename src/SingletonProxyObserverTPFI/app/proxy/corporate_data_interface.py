"""Módulo de la interfaz CorporateDataInterface.

Su función es real de permitir la implementación de los métodos get, set y
list.

Patrón: Ninguno

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

# Las anotaciones se postergan como strings (sin evaluar en tiempo de
# ejecución) porque el método `list` de la interfaz se llama igual que el
# tipo builtin `list` que se usa en sus anotaciones de retorno.
from __future__ import annotations

from abc import ABC, abstractmethod


class CorporateDataInterface(ABC):
    """Clase abstracta / interfaz para las acciones sobre CorporateData.

    Define el contrato común que deben cumplir las clases queManipulan la
    tabla CorporateData, es decir, CorporateDataDAO (que accede a la base) y
    CorporateDataProxy (que aplica las reglas de negocio de la acción).

    Al heredar de ABC y usar @abstractmethod, la interfaz no puede
    instanciarse y toda subclase está obligada a implementar get, set y list.
    De este modo el proxy y el DAO pueden intercambiarse sin que el servidor
    (server.py) dependa de cuál de los dos esté usando.

    Patrón: Proxy

    Args:
        ABC (ABC): Marca la clase como abstracta.
    """

    @abstractmethod
    def get(self, id: str, uuid: str) -> dict[str, str]:
        """Método get.

        Recupera un único registro de la tabla CorporateData a partir de su id.

        Args:
            id (str): Identificador del registro a recuperar.
            uuid (str): UUID del cliente que realiza la petición.

        Returns:
            dict[str, str]: Registro solicitado con los campos de
                CorporateData.
        """
        pass

    @abstractmethod
    def set(self, id: str, data: dict[str, str], uuid: str) -> dict[str, str]:
        """Método set.

        Crea o modifica un registro de la tabla CorporateData. Los campos no
        informados en data no se modifican; si el registro no existía, se crea
        con los campos informados y el resto en blanco.

        Args:
            id (str): Identificador del registro a crear o modificar.
            data (dict[str, str]): Campos de CorporateData a escribir.
            uuid (str): UUID del cliente que realiza la petición.

        Returns:
            dict[str, str]: Registro resultante tras aplicar el cambio.
        """
        pass

    @abstractmethod
    def list(self, uuid: str) -> list[dict[str, str]]:
        """Método list.

        Recupera todos los registros de la tabla CorporateData.

        Args:
            uuid (str): UUID del cliente que realiza la petición.

        Returns:
            list[dict[str, str]]: Lista con todos los registros de
                CorporateData.
        """
        pass
