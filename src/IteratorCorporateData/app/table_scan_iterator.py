"""Iterador perezoso para recorrer toda la tabla CorporateData.

Implementa la interfaz Iterator del patrón Iterator. Recorre la tabla de
DynamoDB página por página, entregando un registro a la vez sin cargar toda
la tabla en memoria.

Patrón: Iterator

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

import logging
from typing import Any, Optional

# pyrefly: ignore[missing-source-for-stubs]
from botocore.exceptions import BotoCoreError, ClientError

from IteratorCorporateData.app.exceptions import DataAccessError
from IteratorCorporateData.app.record_iterator import Iterator

logger = logging.getLogger(__name__)


class TableScanIterator(Iterator):
    """Recorre una tabla de DynamoDB página por página."""

    _table: Any
    """Recurso Table de boto3 asociado a CorporateData."""

    _buffer: list[dict]
    """Registros de la página actual ya entregados al cliente."""

    _last_key: Optional[dict]
    """Clave de paginación de la última página leída. Vale None al inicio y
    cuando se llegó al final de la tabla."""

    _exhausted: bool
    """Indica que se recorrió la tabla completa. Arranca en False."""

    def __init__(self, table: Any) -> None:
        """Guarda la tabla sin consultar DynamoDB.

        Args:
            table: Recurso Table de boto3 asociado a CorporateData.
        """
        self._table = table
        self._buffer = []
        self._last_key = None
        self._exhausted = False
        logger.debug("TableScanIterator inicializado")

    def has_more(self) -> bool:
        """Indica si quedan registros sin consumir.

        Solicita nuevas páginas solamente cuando el buffer está vacío
        y todavía no se llegó al final de la tabla.

        Returns:
            bool: True si hay al menos un registro más por entregar.

        Raises:
            DataAccessError: si falla el acceso a DynamoDB.
        """
        while not self._buffer and not self._exhausted:
            self._fetch_page()

        if not self._buffer:
            logger.debug("Recorrido de CorporateData agotado")

        return bool(self._buffer)

    def next(self) -> dict:
        """Devuelve el siguiente registro y lo quita del buffer.

        Returns:
            dict: Siguiente registro de CorporateData.

        Raises:
            StopIteration: si no quedan registros.
            DataAccessError: si falla el acceso a DynamoDB.
        """
        if not self.has_more():
            raise StopIteration

        record = self._buffer.pop(0)
        logger.debug("Registro entregado; id=%s", record.get("id"))

        return record

    def _fetch_page(self) -> None:
        """Solicita una página y actualiza el estado del recorrido."""
        scan_kwargs: dict[str, Any] = {}

        if self._last_key is not None:
            scan_kwargs["ExclusiveStartKey"] = self._last_key

        logger.debug(
            "Solicitando página de CorporateData; ExclusiveStartKey=%s",
            self._last_key,
        )

        try:
            response = self._table.scan(**scan_kwargs)
        except (ClientError, BotoCoreError) as error:
            raise DataAccessError(
                "No se pudo recorrer la tabla CorporateData."
            ) from error

        items = response.get("Items", [])
        self._buffer.extend(items)

        self._last_key = response.get("LastEvaluatedKey")

        if self._last_key is None:
            self._exhausted = True

        logger.debug(
            "Página recibida; registros=%d total_en_buffer=%d",
            len(items),
            len(self._buffer),
        )
