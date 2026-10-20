"""Módulo iterador concreto que devuelve un único registro de CorporateData.

Implementa la interfaz Iterator del patrón Iterator. Recupera el registro
que se pide con el argumento --id mediante get_item sobre la tabla de
DynamoDB.

Patrón: Iterator

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

import logging
from typing import Any

# pyrefly: ignore[missing-source-for-stubs]
from botocore.exceptions import BotoCoreError, ClientError

from IteratorCorporateData.app.exceptions import (
    DataAccessError,
    RecordNotFoundError,
)
from IteratorCorporateData.app.record_iterator import Iterator

logger = logging.getLogger(__name__)


class SingleRecordIterator(Iterator):
    """Iterador concreto que devuelve un único registro de CorporateData.

    Implementa la interfaz Iterator. Recupera el registro que se pide con el
    argumento --id mediante get_item sobre la tabla de DynamoDB. Si el
    registro no existe, next lanza RecordNotFoundError.
    """

    _table: Any
    """Recurso Table de boto3 asociado a CorporateData."""

    _record_id: str
    """id del registro que se quiere recuperar."""

    _consumed: bool
    """Indica que ya se intentó obtener el registro. Arranca en False."""

    def __init__(self, table: Any, record_id: str) -> None:
        """Guarda la tabla y el id sin consultar la base de datos.

        Args:
            table: Recurso Table de boto3 asociado a CorporateData.
            record_id: id del registro que se quiere recuperar.
        """
        self._table = table
        self._record_id = record_id
        self._consumed = False
        logger.debug("SingleRecordIterator inicializado; id=%s", record_id)

    def has_more(self) -> bool:
        """Indica si todavía no se intentó obtener el registro.

        Retorna True mientras _consumed sea False. No consulta la base de
        datos.

        Returns:
            bool: True si el registro todavía no fue consumido.
        """
        return not self._consumed

    def next(self) -> dict:
        """Devuelve el registro solicitado y marca el iterador como consumido.

        Si el registro ya se entregó, lanza StopIteration. En caso contrario,
        marca _consumed como True antes de consultar, para que un intento
        fallido no se reintente en silencio, y pide el registro con
        get_item usando {"id": _record_id} como clave.

        Returns:
            dict: El registro recuperado de CorporateData.

        Raises:
            StopIteration: si el registro ya se entregó.
            RecordNotFoundError: si no existe un registro con el id
                solicitado.
            DataAccessError: si falla la consulta a DynamoDB.
        """
        if self._consumed:
            raise StopIteration

        self._consumed = True

        logger.debug(
            "Consultando registro de CorporateData; id=%s", self._record_id
        )

        try:
            response = self._table.get_item(Key={"id": self._record_id})
        except (ClientError, BotoCoreError) as error:
            raise DataAccessError(
                f"No se pudo obtener el registro con id={self._record_id}."
            ) from error

        record = response.get("Item")

        if record is None:
            logger.debug("Registro no encontrado; id=%s", self._record_id)
            raise RecordNotFoundError(
                f"No existe un registro con el id={self._record_id}."
            )

        logger.debug("Registro encontrado; id=%s", self._record_id)
        return record
