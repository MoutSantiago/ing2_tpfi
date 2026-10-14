"""Módulo que lee el archivo de entrada y armar la petición.

Completa el UUID con el identificador de la CPU donde se ejecuta el programa,
y valida que la petición tenga los datos mínimos para la acción pedida, de
modo que un archivo inválido falle antes de abrir la conexión.

Patrón: Ninguno

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

import json

from SingletonClient.app.exceptions import InvalidRequestError

VALID_ACTIONS = ("get", "set", "list")
"""Acciones permitidas en este cliente."""

TUPLE_FIELDS = (
    "cp",
    "CUIT",
    "domicilio",
    "idreq",
    "idSeq",
    "localidad",
    "provincia",
    "sede",
    "seqID",
    "telefono",
    "web",
)
"""Campos modificables del tuple CorporateData."""


class RequestLoader:
    """RequestLoader es la clase encargada de leer el archivo de entrada."""

    def __init__(self, uuid: str) -> None:
        """Recibe el identificador de la CPU y lo guarda en __uuid."""
        self.__uuid: str = uuid
        """Identificador de la CPU donde se ejecuta el programa."""

    def load(self, input_path: str) -> dict:
        """Lee, valida y retorna la petición lista para enviar.

        Lanza InvalidRequestError u OSError según el caso.
        """
        data = self._read(input_path)
        self._validate(data)

        request = {"UUID": self.__uuid, "ACTION": data["ACTION"]}
        if data["ACTION"] in ("get", "set"):
            request["ID"] = data["ID"]
        if data["ACTION"] == "set":
            for field in TUPLE_FIELDS:
                if field in data:
                    request[field] = data[field]
        return request

    def _read(self, input_path: str) -> dict:
        """Abre el archivo (UTF-8) y lo interpreta como JSON."""
        with open(input_path, "r", encoding="utf-8") as file:
            content = file.read()
        try:
            data = json.loads(content)
        except json.JSONDecodeError as error:
            raise InvalidRequestError(
                f"El contenido no es un JSON válido: {error}"
            ) from error
        if not isinstance(data, dict):
            raise InvalidRequestError("El contenido JSON debe ser un objeto.")
        return data

    def _validate(self, data: dict) -> None:
        """Verifica los datos mínimos según la acción."""
        action = data.get("ACTION")
        if action is None:
            raise InvalidRequestError("Falta el campo 'ACTION'.")
        if action not in VALID_ACTIONS:
            raise InvalidRequestError(
                f"Acción desconocida o no admitida: {action!r}."
            )

        if action in ("get", "set"):
            if not data.get("ID"):
                raise InvalidRequestError(
                    f"La acción '{action}' requiere un 'ID' no vacío."
                )
            if "id" in data and data["id"] != data["ID"]:
                raise InvalidRequestError(
                    "El campo 'id' no coincide con 'ID'."
                )

        if action == "set":
            unknown = [
                key
                for key in data
                if key not in ("ACTION", "ID", "id", "UUID")
                and key not in TUPLE_FIELDS
            ]
            if unknown:
                raise InvalidRequestError(
                    f"Campos desconocidos: {', '.join(unknown)}."
                )
            if not any(field in data for field in TUPLE_FIELDS):
                raise InvalidRequestError(
                    "La acción 'set' requiere al menos un campo del tuple."
                )

        if action == "list" and "ID" in data:
            raise InvalidRequestError("La acción 'list' no debe incluir 'ID'.")
