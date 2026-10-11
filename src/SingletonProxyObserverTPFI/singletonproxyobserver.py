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

import logging
import sys
from pathlib import Path

# Agrega el directorio padre (src/) al path ANTES de los imports absolutos,
# para que funcionen tanto al ejecutar el archivo directamente
# (python3 singletonproxyobserver.py) como como módulo (-m).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import typer  # noqa: E402

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

app = typer.Typer()


RESET = "\033[0m"
COLORS = {
    logging.DEBUG: "\033[32m",  # verde
    logging.INFO: "\033[32m",  # verde
    logging.WARNING: "\033[33m",  # amarillo
    logging.ERROR: "\033[31m",  # rojo
    logging.CRITICAL: "\033[31m",  # rojo
}


class ColorFormatter(logging.Formatter):
    """Formatea cada línea pintando solo la hora y el nivel."""

    def __init__(self, use_color: bool) -> None:
        """Guarda si se deben emitir códigos de color."""
        super().__init__(datefmt="%H:%M:%S")
        self._use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        """Devuelve la línea de log con el encabezado coloreado."""
        head = f"{self.formatTime(record, self.datefmt)} "
        head += f"{record.levelname:<7}"
        if self._use_color:
            head = f"{COLORS.get(record.levelno, '')}{head}{RESET}"
        line = f"{head} {record.name}: {record.getMessage()}"
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


def configure_logging(verbose: bool) -> None:
    """Configura el logging del servidor según el modo verbose.

    Con verbose en True usa el nivel DEBUG para el código propio;
    en caso contrario, WARNING. Las librerías externas siempre en WARNING.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColorFormatter(sys.stdout.isatty()))

    # El logger raíz maneja todo el código propio
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        handlers=[handler],
        force=True,
    )

    # Las librerías externas siempre en WARNING para no ensuciar la salida
    for lib in ("boto3", "botocore", "urllib3", "asyncio"):
        logging.getLogger(lib).setLevel(logging.WARNING)


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


@app.command()
def main(
    port: int = typer.Option(8080, "--port", "-p", help="Puerto del servidor"),
    verbose: bool = typer.Option(
        False, "-v", help="Activar modo de logs detallados"
    ),
) -> None:
    """Orquesta el arranque del servidor.

    Es el único lugar donde se capturan los errores fatales de arranque,
    informándolos con un mensaje claro y un código de salida (sin traceback):

    - OSError: puerto ocupado o error de socket.
    - DataAccessError: no se pudo acceder a DynamoDB.
    - KeyboardInterrupt: cancelación manual (Ctrl+C), apagado ordenado.

    Códigos de salida:
        0: Terminación normal (cancelación manual con Ctrl+C).
        1: Error de ejecución (puerto ocupado o no se pudo acceder a DynamoDB).
        2: Argumentos malformados (lo devuelve typer por defecto).
    """
    configure_logging(verbose)

    logger = logging.getLogger(__name__)

    server: Server | None = None

    try:
        logger.debug("Construyendo servidor...")
        server = build_server()
        server._port = port

        logger.info("Iniciando servidor en el puerto %d...", port)
        server.serve_forever()

    except DataAccessError as exc:
        logger.error("No se pudo acceder a DynamoDB: %s", exc)
        raise typer.Exit(code=1) from exc

    except OSError as exc:
        logger.error("Error de socket (¿puerto %d ocupado?): %s", port, exc)
        raise typer.Exit(code=1) from exc

    except KeyboardInterrupt:
        logger.info("Deteniendo servidor...")
        if server is not None:
            server.stop()
        raise typer.Exit(code=0) from None


if __name__ == "__main__":
    app()
