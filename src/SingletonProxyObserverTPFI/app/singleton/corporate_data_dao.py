"""Módulo encargado del manejo de peticiones a la tabla CorporateData.

Su función es la de manejar las acciones que tienen impacto o hacen uso de la
tabla CorporateData.

Patrón: Singleton

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

from __future__ import annotations

import logging
from threading import Lock
from typing import TYPE_CHECKING, Any, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Las excepciones salen de exceptions.py para que las capas superiores (proxy,
# Server) capturen un único tipo de error de datos sin importar boto3.
from SingletonProxyObserverTPFI.app.exceptions import (
    DataAccessError,
    RecordNotFoundError,
)
from SingletonProxyObserverTPFI.app.proxy.corporate_data_interface import (
    CorporateDataInterface,
)

logger = logging.getLogger(__name__)

# Es false en runtime, donde se ignora la importación
if TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import Table

NOMBRE_TABLA = "CorporateData"
"""Nombre de la tabla de DynamoDB sobre la que opera este DAO."""

CLAVE = "id"
"""Atributo que actúa como clave de partición de la tabla CorporateData."""

CAMPOS = (
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
"""Campos que componen un tuple de CorporateData (Tabla 1 del enunciado).

Se usan para dejar en blanco los campos que no se informan al crear un
registro nuevo con set().
"""


class CorporateDataDAO(CorporateDataInterface):
    """Clase Singleton CorporateDataDAO.

    Clase encargada del manejo de peticiones a la tabla CorporateData de la
    base de datos (DynamoDB): buscar un registro, modificarlo o listarlos
    todos.

    Está pensada para instanciarse una única vez mediante get_instance(),
    porque el servidor atiende varios clientes en simultáneo y todos comparten
    la misma conexión con la base.

    Nota: este DAO no genera la pista de auditoría en CorporateLog. Esa
    responsabilidad es del CorporateDataProxy, por lo que recibe el uuid por
    contrato de la interfaz pero no lo utiliza.
    """

    _instance: Optional[CorporateDataDAO] = None
    """Atributo privado y de clase (estático) que almacena la única instancia
    del singleton. Vale None hasta que se invoca por primera vez a
    get_instance().
    """

    _lock: Lock = Lock()
    """Atributo privado y de clase que contiene un threading.Lock.
    Se usa dentro de get_instance() para evitar que dos hilos creen dos
    instancias a la vez, ya que el servidor atiende varios clientes en
    simultáneo.
    """

    _table: Table
    """Atributo privado de instancia que contiene el recurso Table de boto3
    asociado a la tabla CorporateData. Se crea en el constructor y es el objeto
    con el que se ejecutan las operaciones contra DynamoDB.
    """

    def __init__(self) -> None:
        """Método constructor de la clase.

        Abre la conexión con DynamoDB y guarda en _table la referencia a la
        tabla CorporateData.
        No debe invocarse directamente, sino a través de get_instance().
        Lanza DataAccessError si no puede conectarse.
        Lanza RuntimeError si se intenta instanciar directamente.
        """
        if type(self)._instance is not None:
            raise RuntimeError("""No instanciar directamente.
                Use CorporateDataDAO.get_instance()""")
        try:
            logger.debug("Conectando a DynamoDB tabla %s...", NOMBRE_TABLA)
            dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
            self._table = dynamodb.Table(NOMBRE_TABLA)
            # Verificar que la tabla existe y es accesible. Cualquier error
            # acá (tabla inexistente, sin permisos) se traduce en
            # DataAccessError para que las capas superiores no vean boto3.
            _ = self._table.table_status
            logger.info("Conectado a tabla %s", NOMBRE_TABLA)
        except (ClientError, BotoCoreError) as e:
            logger.error("Error conectando a %s: %s", NOMBRE_TABLA, e)
            raise DataAccessError(
                f"No se pudo conectar a la tabla {NOMBRE_TABLA}: {e}"
            ) from e
        except Exception as e:
            logger.exception(
                "Error inesperado al inicializar CorporateDataDAO"
            )
            raise DataAccessError(
                f"Error inesperado al inicializar CorporateDataDAO: {e}"
            ) from e

    @classmethod
    def get_instance(cls) -> CorporateDataDAO:
        """Método estático que expone la instancia única.

        Si _instance es None, adquiere _lock, crea la instancia y la guarda;
        en cualquier caso, retorna la instancia existente.

        Lanza DataAccessError si falla la creación de la instancia.

        Returns:
            CorporateDataDAO: Instancia única de la clase.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    try:
                        cls._instance = cls()
                    except DataAccessError:
                        raise
                    except Exception as e:
                        raise DataAccessError(
                            f"Error creando instancia de CorporateDataDAO: {e}"
                        ) from e
        return cls._instance

    @staticmethod
    def _a_texto(item: dict[str, Any]) -> dict[str, str]:
        """Convierte un item de DynamoDB en un diccionario de strings.

        DynamoDB no tiene un tipo texto propio: los campos numéricos
        (idreq, seqID, etc.) se devuelven como Decimal. Como el contrato de la
        interfaz declara dict[str, str], se pasan a str para que el proxy y
        el cliente reciban siempre valores textuales.

        Args:
            item (dict[str, Any]): Item devuelto por boto3.

        Returns:
            dict[str, str]: El mismo item con todos los valores como texto.
        """
        return {
            clave: valor if isinstance(valor, str) else str(valor)
            for clave, valor in item.items()
        }

    def get(self, id: str, uuid: str) -> dict[str, str]:
        """Busca en la tabla el registro cuya clave sea id.

        El uuid se recibe por contrato de la interfaz pero no se utiliza,
        porque la auditoría de las acciones la realiza el proxy.

        Args:
            id (str): Clave del registro a recuperar.
            uuid (str): UUID del cliente (sin uso en este DAO).

        Returns:
            dict[str, str]: Registro solicitado con sus campos como texto.

        Raises:
            RecordNotFoundError: Si no existe un registro con esa clave.
            DataAccessError: Si falla el acceso a la base de datos.
        """
        logger.debug("Obteniendo registro con %s='%s'", CLAVE, id)
        try:
            respuesta = self._table.get_item(Key={CLAVE: id})
        except (ClientError, BotoCoreError) as e:
            logger.error("Error leyendo de %s: %s", NOMBRE_TABLA, e)
            raise DataAccessError(
                f"Error leyendo de {NOMBRE_TABLA}: {e}"
            ) from e

        item = respuesta.get("Item")
        if item is None:
            # Caso excepcional por definición del enunciado: el Server lo
            # convierte en la respuesta "Error" para el cliente.
            logger.warning("Registro no encontrado con %s='%s'", CLAVE, id)
            raise RecordNotFoundError(
                f"No existe un registro con {CLAVE}='{id}' en {NOMBRE_TABLA}"
            )
        return self._a_texto(item)

    def set(self, id: str, data: dict[str, str], uuid: str) -> dict[str, str]:
        """Modifica el registro con clave id usando los campos de data.

        Los campos no informados en data no se modifican. Si el id no existe,
        se crea un registro nuevo con los campos no informados en blanco.
        El uuid se recibe por contrato de la interfaz pero no se utiliza,
        porque la auditoría de las acciones la realiza el proxy.

        Args:
            id (str): Clave del registro a crear o modificar.
            data (dict[str, str]): Campos a escribir sobre el registro.
            uuid (str): UUID del cliente (sin uso en este DAO).

        Returns:
            dict[str, str]: Registro resultante tras aplicar el cambio.

        Raises:
            DataAccessError: Si falla el acceso a la base de datos.
        """
        logger.debug("Escribiendo registro con %s='%s'", CLAVE, id)
        try:
            # Se lee el registro previo para poder modificar solo los campos
            # informados. Si no existe, previo queda en None.
            previo = self._table.get_item(Key={CLAVE: id}).get("Item")

            if previo is None:
                # Registro nuevo: los campos no informados quedan en blanco.
                logger.debug("Creando registro nuevo con %s='%s'", CLAVE, id)
                registro: dict[str, Any] = {campo: "" for campo in CAMPOS}
            else:
                # Registro existente: solo se sobreescriben los campos de data.
                registro = dict(previo)

            registro.update(data)
            registro[CLAVE] = id
            self._table.put_item(Item=registro)
            logger.info(
                "Registro con %s='%s' escrito correctamente", CLAVE, id
            )
        except (ClientError, BotoCoreError) as e:
            logger.error("Error escribiendo en %s: %s", NOMBRE_TABLA, e)
            raise DataAccessError(
                f"Error escribiendo en {NOMBRE_TABLA}: {e}"
            ) from e

        return self._a_texto(registro)

    def list(self, uuid: str) -> list[dict[str, str]]:
        """Recorre toda la tabla y retorna todos los registros.

        El scan de DynamoDB devuelve como máximo 1 MB por llamada, así que
        se repite la petición usando la clave devuelta en LastEvaluatedKey
        hasta agotar la tabla.
        El uuid se recibe por contrato de la interfaz pero no se utiliza,
        porque la auditoría de las acciones la realiza el proxy.

        Args:
            uuid (str): UUID del cliente (sin uso en este DAO).

        Returns:
            list[dict[str, str]]: Todos los registros de la tabla, vacía
                si la tabla no contiene datos.

        Raises:
            DataAccessError: Si falla el acceso a la base de datos.
        """
        logger.debug("Listando todos los registros de %s", NOMBRE_TABLA)
        registros: list[dict[str, str]] = []
        # None inicia el recorrido desde el principio de la tabla.
        clave_inicio: Optional[dict[str, Any]] = None

        try:
            while True:
                if clave_inicio is None:
                    respuesta = self._table.scan()
                else:
                    # Marca de paginación: continúa desde donde terminó la
                    # llamada anterior, porque un scan trae 1 MB máximo.
                    respuesta = self._table.scan(
                        ExclusiveStartKey=clave_inicio
                    )

                registros.extend(
                    self._a_texto(item) for item in respuesta.get("Items", [])
                )

                clave_inicio = respuesta.get("LastEvaluatedKey")
                if not clave_inicio:
                    break
        except (ClientError, BotoCoreError) as e:
            logger.error("Error listando %s: %s", NOMBRE_TABLA, e)
            raise DataAccessError(f"Error listando {NOMBRE_TABLA}: {e}") from e

        logger.info(
            "Listados %d registros de %s", len(registros), NOMBRE_TABLA
        )
        return registros
