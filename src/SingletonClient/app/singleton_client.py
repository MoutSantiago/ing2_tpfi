"""Módulo encargado de mostrar la respuesta del servidor.

ResponseWriter escribe la respuesta del servidor como un único documento
JSON: por salida estándar si no se informó una ruta, o en el archivo
indicado en caso contrario. Está separada de SingletonClient para que este
no conozca los detalles de la salida y para poder reemplazarla por un mock
en los tests.

Patrón: Ninguno

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

import logging
from typing import Any

from SingletonClient.app.request_loader import RequestLoader
from SingletonClient.app.response_writer import ResponseWriter
from SingletonClient.app.server_connection import ServerConnection

logger = logging.getLogger(__name__)


class SingletonClient:
    """Clase que implementa la lógica del programa cliente.

    Orquesta un único intercambio con el servidor: carga la petición desde el
    archivo de entrada, se conecta, la envía, recibe la respuesta, la muestra
    con ResponseWriter y cierra la conexión.
    """

    _loader: RequestLoader
    """Objeto que lee y valida el archivo de entrada."""

    _connection: ServerConnection
    """Objeto que maneja el socket TCP."""

    _writer: ResponseWriter
    """Objeto que muestra la respuesta."""

    def __init__(
        self,
        loader: RequestLoader,
        connection: ServerConnection,
        writer: ResponseWriter,
    ) -> None:
        """Método constructor de la clase.

        Recibe las tres dependencias y las guarda en _loader, _connection y
        _writer. No realiza ninguna operación de red ni de archivos.

        Args:
            loader (RequestLoader): Objeto que maneja el archivo de entrada.
            connection (ServerConnection): Objeto que maneja el socket TCP.
            writer (ResponseWriter): Objeto que muestra la respuesta.
        """
        self._loader = loader
        self._connection = connection
        self._writer = writer
        logger.debug("SingletonClient inicializado con sus dependencias")

    def execute(self, input_path: str) -> Any:
        """Ejecuta el intercambio completo y retorna la respuesta del servidor.

        Los pasos, en este orden:
        Arma la petición con _loader.load(input_path).
            Si el archivo es inválido, falla antes de abrir la conexión.
        Conecta con _connection.connect(), envía la petición con
            _connection.send() y recibe la respuesta con _connection.receive().
        Cierra la conexión con _connection.close(), siempre, haya o
            no excepción (bloque finally).
        Muestra la respuesta con _writer.write() y la retorna.
        La respuesta se retorna aunque sea un error del servidor
            (por ejemplo, "Error"): evaluarla corresponde al main.

        Args:
            input_path (str): Path al archivo de entrada.

        Returns:
            Any: Respuesta del servidor (se retorna incluso si es un error
                del servidor, por ejemplo "Error").
        """
        logger.debug("Cargando petición desde %s", input_path)
        request = self._loader.load(input_path)

        logger.debug("Conectando con el servidor")
        self._connection.connect()
        try:
            logger.debug("Enviando petición al servidor")
            self._connection.send(request)
            logger.debug("Esperando respuesta del servidor")
            response = self._connection.receive()
        finally:
            self._connection.close()
            logger.debug("Conexión cerrada")

        logger.debug("Escribiendo respuesta")
        self._writer.write(response)
        return response
