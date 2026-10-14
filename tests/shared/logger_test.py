"""Tests del logger compartido en src/shared."""

import logging
import sys

from shared.logger import ColorFormatter, configure_logging


def make_record(
    level=logging.INFO, msg="hola %s", args=("mundo",), exc_info=None
):
    """Construye un LogRecord para los tests del formateador."""
    return logging.LogRecord(
        name="mi.logger",
        level=level,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=args,
        exc_info=exc_info,
    )


def test_color_formatter_without_color():
    """Sin color, la línea no lleva secuencias ANSI."""
    formatter = ColorFormatter(use_color=False)

    line = formatter.format(make_record())

    assert "INFO" in line
    assert "mi.logger: hola mundo" in line
    assert "\033[" not in line


def test_color_formatter_with_color():
    """Con color, la línea arranca con el código del nivel."""
    formatter = ColorFormatter(use_color=True)

    line = formatter.format(make_record(level=logging.ERROR))

    assert line.startswith("\033[31m")
    assert "\033[0m" in line
    assert "mi.logger: hola mundo" in line


def test_color_formatter_includes_exception():
    """Si el registro trae excepción, se incluye su traceback."""
    formatter = ColorFormatter(use_color=False)

    try:
        raise ValueError("boom")
    except ValueError:
        record = make_record(exc_info=sys.exc_info())

    line = formatter.format(record)

    assert "ValueError: boom" in line
    assert "Traceback" in line


def test_configure_logging_verbose_sets_debug():
    """Con verbose, el paquete propio queda en DEBUG."""
    configure_logging(True, "MiPaquete")

    assert logging.getLogger("MiPaquete").level == logging.DEBUG
    assert logging.getLogger().level == logging.WARNING
    assert logging.getLogger().handlers


def test_configure_logging_without_verbose_uses_warning():
    """Sin verbose, el paquete propio queda en WARNING."""
    configure_logging(False, "MiPaquete")

    assert logging.getLogger("MiPaquete").level == logging.WARNING
    assert logging.getLogger().level == logging.WARNING


def test_configure_logging_quiets_external_libraries():
    """Las librerías externas quedan en WARNING."""
    configure_logging(True, "MiPaquete")

    for lib in ("boto3", "botocore", "urllib3", "asyncio"):
        assert logging.getLogger(lib).level == logging.WARNING
