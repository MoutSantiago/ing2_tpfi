"""
Punto de entrada del programa IteratorCorporateData.

Interpreta los argumentos, configura el logging, crea la conexión a
DynamoDB y las demás dependencias, ejecuta la consulta y traduce el
resultado (o el error) a un código de salida. No contiene lógica de acceso
a datos ni de salida, que viven en las demás clases.

A diferencia de los otros programas, no usa el servidor ni sockets: accede
a la tabla CorporateData directamente con los servicios de AWS (boto3),
con las credenciales y la región ya configuradas.

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
from typing import Any, Optional, Sequence

# Agrega el directorio padre (src/) al path ANTES de los imports absolutos,
# para que funcionen tanto al ejecutar el archivo directamente
# (python3 iteratorCorporateData.py) como como módulo (-m).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import boto3  # noqa: E402
from botocore.exceptions import (  # noqa: E402
    BotoCoreError,
    ClientError,
    NoCredentialsError,
    NoRegionError,
)

from IteratorCorporateData.app.corporate_data_collection import (  # noqa: E402
    CorporateDataCollection,
)
from IteratorCorporateData.app.exceptions import (  # noqa: E402
    DataAccessError,
    RecordNotFoundError,
)
from IteratorCorporateData.app.iterator_corporate_data import (  # noqa: E402
    IteratorCorporateData,
)
from IteratorCorporateData.app.json_write import JsonWrite  # noqa: E402
from shared.logger import configure_logging as _configure_logging  # noqa: E402

LOGGER_NAME: str = "IteratorCorporateData"
"""Nombre del logger del paquete propio, configurado por shared.logger."""

TABLE_NAME: str = "CorporateData"
"""Nombre de la tabla de DynamoDB que se consulta."""

logger: logging.Logger = logging.getLogger(LOGGER_NAME)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Define y procesa los argumentos de la línea de comandos.

    Args:
        argv: Lista de argumentos a parsear. Si es None, usa sys.argv[1:].

    Returns:
        argparse.Namespace: Argumentos ya validados, con los atributos id y
            verbose.

    Raises:
        SystemExit: con código 2 si los argumentos están malformados.
    """
    parser = argparse.ArgumentParser(
        description="Consulta los registros de la tabla CorporateData.",
        allow_abbrev=False,
    )

    parser.add_argument(
        "--id",
        dest="id",
        default=None,
        metavar="xxxxxxxxx",
        help=(
            "Identificador del registro a recuperar. Si no se informa, "
            "se recupera toda la tabla."
        ),
    )
    parser.add_argument(
        "-v",
        "--v",
        dest="verbose",
        action="store_true",
        help="Activa los mensajes DEBUG del paquete propio.",
    )

    args = parser.parse_args(argv)

    # El id no puede ser vacío ni estar compuesto solo por espacios. Se usa
    # parser.error para que argparse termine con el código 2.
    if args.id is not None and not args.id.strip():
        parser.error(
            "el id no puede ser vacío ni estar compuesto solo por espacios"
        )

    return args


def configure_logging(verbose: bool) -> None:
    """Configura el logging del programa en salida estándar.

    Con verbose en True usa el nivel DEBUG para el paquete propio;
    en caso contrario, WARNING. Las librerías externas siempre en WARNING.

    Args:
        verbose: Si se debe activar el nivel DEBUG del paquete propio.
    """
    _configure_logging(verbose, LOGGER_NAME)


def _create_table() -> Any:
    """Crea el recurso Table de boto3 asociado a CorporateData.

    Verifica la configuración de AWS antes de crear el recurso, porque
    boto3.resource no falla si hay región pero faltan las credenciales.

    Returns:
        Any: Recurso Table de boto3 sobre CorporateData.

    Raises:
        DataAccessError: si falta la región, faltan las credenciales o no se
            pudo crear el recurso de DynamoDB.
    """
    session = boto3.session.Session()

    if not session.region_name:
        raise DataAccessError(
            "No se pudo acceder a DynamoDB: no hay una región de AWS "
            "configurada."
        )

    if session.get_credentials() is None:
        raise DataAccessError(
            "No se pudo acceder a DynamoDB: no hay credenciales de AWS "
            "configuradas."
        )

    try:
        return boto3.resource("dynamodb").Table(TABLE_NAME)
    except (
        NoRegionError,
        NoCredentialsError,
        ClientError,
        BotoCoreError,
    ) as error:
        raise DataAccessError(
            f"No se pudo acceder a DynamoDB: {error}"
        ) from error


def build_app(
    record_id: Optional[str],
    table: Any = None,
) -> IteratorCorporateData:
    """Crea las dependencias y las conecta.

    La tabla se crea con boto3.resource("dynamodb").Table("CorporateData"),
    salvo que se pase una table ya creada, lo que permite inyectar una tabla
    falsa en los tests.

    Args:
        record_id: id pedido con --id. None para recorrer toda la tabla.
        table: Tabla de DynamoDB ya creada. Si es None, se crea con boto3.
            Por defecto, None.

    Returns:
        IteratorCorporateData: Cliente listo para ejecutar la consulta.

    Raises:
        DataAccessError: si falta la región o las credenciales de AWS.
    """
    if table is None:
        logger.debug("Creando la tabla CorporateData con boto3...")
        table = _create_table()

    logger.debug("Creando CorporateDataCollection...")
    collection = CorporateDataCollection(table, record_id)

    logger.debug("Creando JsonWrite...")
    writer = JsonWrite()

    logger.debug("Creando IteratorCorporateData...")
    return IteratorCorporateData(
        collection,
        writer,
        single_record=record_id is not None,
    )


def _describe_error(error: BaseException) -> str:
    """Devuelve el detalle de un error, incluida su causa si la tiene.

    Args:
        error: Excepción que se debe informar.

    Returns:
        str: Mensaje del error y, si existe, el de su causa.
    """
    message = str(error) or type(error).__name__

    if error.__cause__ is not None:
        message = f"{message} Causa: {error.__cause__}"

    return message


def _report_error(message: str) -> None:
    """Escribe un mensaje de error por error estándar.

    Args:
        message: Texto que se debe informar.
    """
    print(message, file=sys.stderr)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Orquesta la ejecución y traduce los errores a códigos de salida.

    Es el único lugar donde se capturan los errores, que se informan con un
    mensaje claro por error estándar y un código de salida, sin traceback.

    Códigos de salida:
        0: La consulta se completó (incluye la tabla vacía).
        1: Error de ejecución: registro inexistente, falla de acceso a AWS,
            error de escritura, cancelación manual o error inesperado.
        2: Argumentos malformados (lo devuelve argparse por defecto).

    Args:
        argv: Lista de argumentos a parsear. Si es None, usa sys.argv[1:].

    Returns:
        int: Código de salida del proceso.
    """
    try:
        args = parse_args(argv)
        configure_logging(args.verbose)

        logger.debug("Construyendo la aplicación...")
        app = build_app(args.id)

        logger.debug("Ejecutando la consulta...")
        app.run()

        return 0

    except RecordNotFoundError as error:
        _report_error(_describe_error(error))
        return 1

    except DataAccessError as error:
        _report_error(f"Error de acceso a datos: {_describe_error(error)}")
        return 1

    except OSError as error:
        _report_error(
            f"No se pudo escribir el resultado: {_describe_error(error)}"
        )
        return 1

    except KeyboardInterrupt:
        _report_error("Cancelado por el usuario.")
        return 1

    except Exception as error:
        _report_error(f"Error inesperado: {_describe_error(error)}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
