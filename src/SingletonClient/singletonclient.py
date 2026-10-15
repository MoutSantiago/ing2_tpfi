"""
Punto de entrada del cliente SingletonClient.

Interpreta los argumentos, configura el logging, crea las dependencias,
ejecuta un intercambio con el servidor y traduce el resultado (o el error)
a un código de salida. No contiene lógica de red, de archivos ni de salida,
que viven en las demás clases.

Ingeniería de Software II - UADER FCyT (2026)
Autores:
    - Laiño Valentino
    - Mout Santiago
    - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

import argparse
import logging
import sys
import uuid
from pathlib import Path
from typing import Optional, Sequence

# Agrega el directorio padre (src/) al path ANTES de los imports absolutos,
# para que funcionen tanto al ejecutar el archivo directamente
# como como módulo (-m).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.logger import configure_logging as _configure_logging  # noqa: E402
from SingletonClient.app.exceptions import (  # noqa: E402
    ConnectionLostError,
    InvalidRequestError,
)
from SingletonClient.app.request_loader import RequestLoader  # noqa: E402
from SingletonClient.app.response_writer import ResponseWriter  # noqa: E402
from SingletonClient.app.server_connection import (  # noqa: E402
    DEFAULT_READ_TIMEOUT,
    ServerConnection,
)
from SingletonClient.app.singleton_client import SingletonClient  # noqa: E402

LOGGER_NAME = "SingletonClient"
"""Nombre del logger del paquete propio, configurado por shared.logger."""

logger = logging.getLogger(LOGGER_NAME)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Procesa los argumentos y valida el puerto TCP."""
    parser = argparse.ArgumentParser(description="Cliente SingletonClient.")

    parser.add_argument(
        "-i",
        dest="input",
        required=True,
        metavar="input.json",
        help="Archivo JSON de entrada con la petición (obligatorio).",
    )
    parser.add_argument(
        "-o",
        dest="output",
        default=None,
        metavar="output.json",
        help="Archivo donde se graba la respuesta (opcional).",
    )
    parser.add_argument(
        "-s",
        dest="s",
        default="localhost",
        metavar="hostname",
        help="Nombre o dirección del servidor (por defecto: localhost).",
    )
    parser.add_argument(
        "-p",
        dest="p",
        type=int,
        default=8080,
        metavar="port",
        help="Puerto TCP entre 1 y 65535 (por defecto: 8080).",
    )
    parser.add_argument(
        "-v",
        action="store_true",
        dest="verbose",
        help="Activa los mensajes DEBUG del paquete propio.",
    )

    args = parser.parse_args(argv)

    if not 1 <= args.p <= 65535:
        parser.error("el puerto debe ser un entero entre 1 y 65535")

    # Nombres descriptivos para facilitar el uso de los argumentos.
    args.input_path = args.input
    args.host = args.s
    args.port = args.p
    args.output_path = args.output

    return args


def configure_logging(verbose: bool) -> None:
    """Configura el logging del cliente en stdout.

    Con verbose en True usa el nivel DEBUG para el código propio;
    en caso contrario, WARNING. Las librerías externas siempre en WARNING.

    Args:
        verbose: Si se debe activar el nivel DEBUG del paquete propio.
    """
    _configure_logging(verbose, LOGGER_NAME)


def build_client(
    host: str,
    port: int,
    output: Optional[str],
    read_timeout: float = DEFAULT_READ_TIMEOUT,
) -> SingletonClient:
    """Construye las dependencias e instancia el cliente."""
    logger.debug("Creando RequestLoader...")
    loader = RequestLoader(str(uuid.getnode()))

    logger.debug("Creando ServerConnection...")
    connection = ServerConnection(host, port, read_timeout)

    logger.debug("Creando ResponseWriter...")
    writer = ResponseWriter(output)

    logger.debug("Creando SingletonClient...")
    return SingletonClient(loader, connection, writer)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Orquesta la ejecución y traduce errores a códigos de salida."""
    try:
        args = parse_args(argv)
        configure_logging(args.verbose)

        logger.debug("Construyendo cliente...")
        client = build_client(
            host=args.host,
            port=args.port,
            output=args.output_path,
        )

        logger.debug("Ejecutando intercambio...")
        response = client.execute(args.input_path)

        # Si la respuesta del servidor es de error (el texto "Error"
        # o un objeto con STATUS igual a "Error"), retorna 1.
        is_error_response = False
        if isinstance(response, str):
            if response.strip() == "Error":
                is_error_response = True
        elif isinstance(response, dict):
            resp = response
            if resp.get("STATUS") == "Error" or resp.get("status") == "Error":
                is_error_response = True

        if is_error_response:
            return 1

        return 0

    except InvalidRequestError as error:
        logger.error("Error en la petición: %s", error)
        return 1

    except ConnectionLostError as error:
        logger.error("Error de conexión: %s", error)
        return 1

    except ValueError as error:
        logger.error("Error en la respuesta: %s", error)
        return 1

    except OSError as error:
        logger.error("Error de entrada/salida: %s", error)
        return 1

    except KeyboardInterrupt:
        logger.info("Cancelado por el usuario")
        return 1

    except Exception as error:
        logger.error("Error durante la ejecución: %s", error)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
