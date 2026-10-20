"""Módulo colección concreta que crea iteradores sobre CorporateData.

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

import logging
from typing import Any, Optional

from IteratorCorporateData.app.iterable_collection import Collection
from IteratorCorporateData.app.recordIterator import Iterator
from IteratorCorporateData.app.single_record_iterator import (
    SingleRecordIterator,
)
from IteratorCorporateData.app.tableScanIterator import TableScanIterator

logger = logging.getLogger(__name__)


class CorporateDataCollection(Collection):
    """Colección concreta que representa la tabla CorporateData.

    Implementa la interfaz Collection. Sabe qué iterador crear: si se pidió
    un id (--id) devuelve un SingleRecordIterator, en caso contrario un
    TableScanIterator. El cliente solo conoce la interfaz Collection, por lo
    que no sabe qué iterador se crea.
    """

    _table: Any
    """Recurso Table de boto3 asociado a CorporateData."""

    _record_id: Optional[str]
    """id pedido con --id. Vale None si se quiere recorrer toda la tabla."""

    def __init__(
        self,
        table: Any,
        record_id: Optional[str] = None,
    ) -> None:
        """Guarda la tabla y el id opcional sin consultar la base de datos.

        Args:
            table: Recurso Table de boto3 asociado a CorporateData.
            record_id: id pedido con --id. None para recorrer toda la tabla.
                Por defecto, None.
        """
        self._table = table
        self._record_id = record_id
        logger.debug(
            "CorporateDataCollection inicializado; record_id=%s", record_id
        )

    def create_iterator(self) -> Iterator:
        """Crea y devuelve un iterador nuevo e independiente.

        Si _record_id es None, retorna un TableScanIterator sobre _table;
        en caso contrario, retorna un SingleRecordIterator(_table,
        _record_id). Cada llamada devuelve un iterador nuevo. Crear el
        iterador no consulta la base de datos.

        Returns:
            Iterator: Iterador nuevo sobre los registros de CorporateData.
        """
        if self._record_id is None:
            logger.debug("Creando TableScanIterator (recorrido completo)")
            return TableScanIterator(self._table)

        logger.debug(
            "Creando SingleRecordIterator para id=%s", self._record_id
        )
        return SingleRecordIterator(self._table, self._record_id)
