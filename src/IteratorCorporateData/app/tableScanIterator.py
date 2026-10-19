"""Iterador perezoso para recorrer toda la tabla CorporateData."""

import logging
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from IteratorCorporateData.app.exceptions import DataAccessError
from IteratorCorporateData.app.recordIterator import Iterator

logger = logging.getLogger(__name__)


class TableScanIterator(Iterator):
    """Recorre una tabla de DynamoDB página por página."""

    def __init__(self, table: Any) -> None:
        """Guarda la tabla sin consultar DynamoDB."""
        self._table = table
        self._buffer: list[dict] = []
        self._last_key: dict | None = None
        self._exhausted = False

    def has_more(self) -> bool:
        """Indica si quedan registros sin consumir.

        Solicita nuevas páginas solamente cuando el buffer está vacío
        y todavía no se llegó al final de la tabla.

        Raises:
            DataAccessError: si falla el acceso a DynamoDB.
        """
        while not self._buffer and not self._exhausted:
            self._fetch_page()

        return bool(self._buffer)

    def next(self) -> dict:
        """Devuelve el siguiente registro y lo quita del buffer.

        Raises:
            StopIteration: si no quedan registros.
            DataAccessError: si falla el acceso a DynamoDB.
        """
        if not self.has_more():
            raise StopIteration

        record = self._buffer.pop(0)
        logger.debug("Registro entregado: id=%s", record.get("id"))

        return record

    def _fetch_page(self) -> None:
        """Solicita una página y actualiza el estado del recorrido."""
        scan_kwargs = {}

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

        self._buffer.extend(response.get("Items", []))

        self._last_key = response.get("LastEvaluatedKey")

        if self._last_key is None:
            self._exhausted = True
