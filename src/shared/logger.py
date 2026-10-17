"""Configuración de logging compartida por todos los programas del TPFI.

Expone el formateador con color y una única función configure_logging para
que el servidor y los clientes emitan sus logs con el mismo formato y bajo
las mismas reglas de nivel, sin duplicar código en cada punto de entrada.

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

RESET = "\033[0m"

COLORS = {
    logging.DEBUG: "\033[32m",  # verde
    logging.INFO: "\033[32m",  # verde
    logging.WARNING: "\033[33m",  # amarillo
    logging.ERROR: "\033[31m",  # rojo
    logging.CRITICAL: "\033[31m",  # rojo
}

EXTERNAL_LOGGERS = ("boto3", "botocore", "urllib3", "asyncio")


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


def configure_logging(verbose: bool, logger_name: str) -> None:
    """Configura el logging de un programa del TPFI.

    Con verbose en True usa el nivel DEBUG para el paquete propio;
    en caso contrario, WARNING. El logger raíz queda en WARNING para no
    mostrar los logs de paquetes ajenos, y las librerías externas siempre
    quedan en WARNING para no ensuciar la salida.

    Args:
        verbose: Si se debe activar el nivel DEBUG en el paquete propio.
        logger_name: Nombre del logger del programa (por ejemplo,
            "SingletonProxyObserverTPFI" u "ObserverClient").
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColorFormatter(sys.stdout.isatty()))

    # El logger raíz maneja la salida y queda en WARNING para que los logs
    # de los paquetes no propios no se muestren por defecto.
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.WARNING)

    # El paquete propio puede emitir DEBUG en modo verbose. Sus loggers
    # hijos heredan el nivel por propagación.
    logging.getLogger(logger_name).setLevel(
        logging.DEBUG if verbose else logging.WARNING
    )

    # Las librerías externas siempre en WARNING para no ensuciar la salida.
    for lib in EXTERNAL_LOGGERS:
        logging.getLogger(lib).setLevel(logging.WARNING)
