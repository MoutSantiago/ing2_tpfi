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
from pathlib import Path
from typing import Optional, Sequence

# Agrega el directorio padre (src/) al path ANTES de los imports absolutos,
# para que funcionen tanto al ejecutar el archivo directamente
# (python3 observerclient.py) como como módulo (-m).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ObserverClient.app.notification_writer import (  # noqa: E402
    NotificationWriter,
)
from ObserverClient.app.observer_client import (  # noqa: E402
    DEFAULT_RETRY_INTERVAL,
    ObserverClient,
)
from ObserverClient.app.server_connection import (  # noqa: E402
    ServerConnection,
)
from SingletonProxyObserverTPFI.singletonproxyobserver import (  # noqa: E402
    ColorFormatter,
)

logger = logging.getLogger("ObserverClient")


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
        "-r",
        type=int,
        default=DEFAULT_RETRY_INTERVAL,
        metavar="seconds",
        dest="retry_interval",
        help=(
            "Segundos de espera entre reintentos de conexión "
            "(por defecto: %(default)s)."
        ),
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

    if args.retry_interval <= 0:
        parser.error("el intervalo de reintento debe ser mayor que cero")

    # Nombres descriptivos para facilitar el uso de los argumentos.
    args.host = args.s
    args.port = args.p
    args.output = args.o

    return args


def configure_logging(verbose: bool) -> None:
    """Configura el logging del cliente en stdout con encabezado coloreado.

    Con verbose en True usa el nivel DEBUG para el código propio;
    en caso contrario, WARNING. Las librerías externas siempre en WARNING.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColorFormatter(sys.stdout.isatty()))

    # El logger raíz queda en WARNING, para que los logs de los paquetes no
    # propios no se muestren por defecto
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.WARNING)

    # El paquete propio puede emitir DEBUG en modo verbose
    logging.getLogger("ObserverClient").setLevel(
        logging.DEBUG if verbose else logging.WARNING
    )

    # Las librerías externas siempre en WARNING para no ensuciar la salida
    for lib in ("boto3", "botocore", "urllib3"):
        logging.getLogger(lib).setLevel(logging.WARNING)


def build_client(
    host: str,
    port: int,
    output: Optional[str],
    retry_interval: int = DEFAULT_RETRY_INTERVAL,
) -> ObserverClient:
    """Construye las dependencias e instancia el cliente."""
    logger.debug("Creando ServerConnection...")
    connection = ServerConnection(host, port)

    logger.debug("Creando NotificationWriter...")
    writer = NotificationWriter(output)

    logger.debug("Creando ObserverClient...")
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

        logger.debug("Construyendo cliente...")
        client = build_client(
            host=args.host,
            port=args.port,
            output=args.output,
            retry_interval=args.retry_interval,
        )

        logger.info("Iniciando cliente hacia %s:%d...", args.host, args.port)
        client.run()
        return 0

    except KeyboardInterrupt:
        logger.info("Deteniendo cliente...")
        if client is not None:
            try:
                client.stop()
            except Exception as error:
                logger.error("Error al detener el cliente: %s", error)

        return 0

    except OSError as error:
        logger.error("Error de entrada/salida: %s", error)
        return 1

    except Exception as error:
        logger.error("Error fatal durante la ejecución: %s", error)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
