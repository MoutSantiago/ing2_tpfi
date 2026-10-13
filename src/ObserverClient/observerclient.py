"""
Punto de entrada del cliente suscriptor.

Interpreta los argumentos, configura el logging, construye las
dependencias e inicia ObserverClient. No implementa lógica de red
ni de escritura de notificaciones.

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
from typing import Optional, Sequence

from ObserverClient.app.notification_writer import NotificationWriter
from ObserverClient.app.observer_client import (
    DEFAULT_RETRY_INTERVAL,
    ObserverClient,
)
from ObserverClient.app.server_connection import ServerConnection
from SingletonProxyObserverTPFI.singletonproxyobserver import ColorFormatter


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Procesa los argumentos y valida el puerto TCP."""
    parser = argparse.ArgumentParser(
        description="Cliente suscriptor de notificaciones."
    )

    parser.add_argument(
        "-s",
        default="localhost",
        metavar="hostname",
        help="Nombre o dirección del servidor (por defecto: localhost).",
    )
    parser.add_argument(
        "-p",
        type=int,
        default=8080,
        metavar="port",
        help="Puerto TCP entre 1 y 65535 (por defecto: 8080).",
    )
    parser.add_argument(
        "-o",
        default=None,
        metavar="output.json",
        help="Archivo donde agregar las notificaciones recibidas.",
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
    args.host = args.s
    args.port = args.p
    args.output = args.o

    return args


def configure_logging(verbose: bool) -> None:
    """Configura logging en stdout con encabezado coloreado."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColorFormatter(use_color=True))

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.WARNING)

    # El paquete propio puede emitir DEBUG en modo verbose.
    package_logger = logging.getLogger("ObserverClient")
    package_logger.setLevel(logging.DEBUG if verbose else logging.WARNING)

    # Las librerías externas deben conservar el nivel WARNING.
    for logger_name in (
        "botocore",
        "boto3",
        "urllib3",
    ):
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def build_client(
    host: str,
    port: int,
    output: Optional[str],
    retry_interval: int = DEFAULT_RETRY_INTERVAL,
) -> ObserverClient:
    """Construye las dependencias e instancia el cliente."""
    connection = ServerConnection(host, port)
    writer = NotificationWriter(output)

    return ObserverClient(
        host,
        port,
        connection,
        writer,
        retry_interval,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Arranca el cliente y traduce los errores a códigos de salida."""
    client = None

    try:
        args = parse_args(argv)
        configure_logging(args.verbose)

        client = build_client(
            host=args.host,
            port=args.port,
            output=args.output,
        )

        client.run()
        return 0

    except KeyboardInterrupt:
        if client is not None:
            try:
                client.stop()
            except Exception as error:
                logging.error("Error al detener el cliente: %s", error)

        return 0

    except OSError as error:
        logging.error("Error de entrada/salida: %s", error)
        return 1

    except Exception as error:
        logging.error("Error fatal durante la ejecución: %s", error)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
