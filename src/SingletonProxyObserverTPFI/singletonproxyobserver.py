"""Módulo principal del servidor.

Es el modulo que contiene el punto de entrada del servidor.
Gestiona las flags y argumentos y llama a los demas modulos.

Patrón: Ninguno

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
# (python3 singletonproxyobserver.py) como como módulo (-m).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.logger import configure_logging  # noqa: E402
from SingletonProxyObserverTPFI.app.exceptions import (  # noqa: E402
    DataAccessError,
)
from SingletonProxyObserverTPFI.app.observer.subscription_manager import (  # noqa: E402
    SubscriptionManager,
)
from SingletonProxyObserverTPFI.app.proxy.corporate_data_proxy import (  # noqa: E402
    CorporateDataProxy,
)
from SingletonProxyObserverTPFI.app.server import Server  # noqa: E402
from SingletonProxyObserverTPFI.app.singleton.corporate_data_dao import (  # noqa: E402
    CorporateDataDAO,
)
from SingletonProxyObserverTPFI.app.singleton.corporate_log_dao import (  # noqa: E402
    CorporateLogDAO,
)

LOGGER_NAME = "SingletonProxyObserverTPFI"
"""Nombre del logger del paquete propio, configurado por shared.logger."""

DEFAULT_PORT = 8080
"""Puerto por defecto donde escucha el servidor."""


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Procesa los argumentos de la línea de comandos.

    Args:
        argv: Lista de argumentos a parsear. Si es None, usa sys.argv[1:].

    Returns:
        Los argumentos ya validados por argparse.
    """
    parser = argparse.ArgumentParser(
        description="Servidor de aplicaciones del TPFI.",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=DEFAULT_PORT,
        metavar="port",
        help="Puerto del servidor (por defecto: %(default)s).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Activar modo de logs detallados.",
    )

    return parser.parse_args(argv)


def build_server() -> Server:
    """Crea las dependencias en este orden y las conecta.

    SubscriptionManager, CorporateDataDAO.get_instance(),
    CorporateLogDAO.get_instance(), CorporateDataProxy(real, log, publisher) y
    Server(host, port, proxy, publisher). Obtener los DAOs acá, y no de forma
    diferida, hace que un problema de conexión con DynamoDB falle al arrancar
    y no con el primer cliente. Lanza DataAccessError si falla.
    """
    logger = logging.getLogger(__name__)

    logger.debug("Creando SubscriptionManager...")
    publisher = SubscriptionManager()

    logger.debug("Obteniendo CorporateDataDAO...")
    data_dao = CorporateDataDAO.get_instance()

    logger.debug("Obteniendo CorporateLogDAO...")
    log_dao = CorporateLogDAO.get_instance()

    logger.debug("Creando CorporateDataProxy...")
    proxy = CorporateDataProxy(
        real=data_dao,
        log=log_dao,
        publisher=publisher,
    )

    logger.debug("Creando Server...")
    server = Server(
        host="0.0.0.0",  # nosec B104
        port=8080,
        data=proxy,
        publisher=publisher,
    )

    return server


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Orquesta el arranque del servidor.

    Es el único lugar donde se capturan los errores fatales de arranque,
    informándolos con un mensaje claro y un código de salida (sin traceback):

    - OSError: puerto ocupado o error de socket.
    - DataAccessError: no se pudo acceder a DynamoDB.
    - KeyboardInterrupt: cancelación manual (Ctrl+C), apagado ordenado.

    Códigos de salida:
        0: Terminación normal (cancelación manual con Ctrl+C).
        1: Error de ejecución (puerto ocupado o no se pudo acceder a DynamoDB).
        2: Argumentos malformados (lo devuelve argparse por defecto).

    Args:
        argv: Lista de argumentos a parsear. Si es None, usa sys.argv[1:].

    Returns:
        El código de salida del proceso.
    """
    args = parse_args(argv)

    configure_logging(args.verbose, LOGGER_NAME)

    logger = logging.getLogger(__name__)

    server: Server | None = None

    try:
        logger.debug("Construyendo servidor...")
        server = build_server()
        server._port = args.port

        logger.info("Iniciando servidor en el puerto %d...", args.port)
        server.serve_forever()

    except DataAccessError as exc:
        logger.error("No se pudo acceder a DynamoDB: %s", exc)
        return 1

    except OSError as exc:
        logger.error(
            "Error de socket (¿puerto %d ocupado?): %s", args.port, exc
        )
        return 1

    except KeyboardInterrupt:
        logger.info("Deteniendo servidor...")
        if server is not None:
            server.stop()
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
