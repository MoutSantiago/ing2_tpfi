"""Módulo encargado del manejo de peticiones a la tabla CorporateLog.

Su función es registrar la pista de auditoría de las acciones realizadas sobre
el sistema.

Patrón: Singleton

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING, Optional

import boto3
from botocore.exceptions import ClientError

from SingletonProxyObserverTPFI.app.exceptions import DataAccessError

# Es false en runtime, donde se ignora la importación
if TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import Table


class CorporateLogDAO:
    """Clase Singleton CorporateLogDAO.

    Clase encargada del manejo de peticiones a la tabla CorporateLog de la base
    de datos (DynamoDB).
    Su función es registrar la pista de auditoría de las acciones realizadas
    sobre el sistema.
    """

    _instance: Optional[CorporateLogDAO] = None
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
    asociado a la tabla CorporateLog. Se crea en el constructor y es el objeto
    con el que se ejecutan las operaciones contra DynamoDB.
    """

    def __init__(self) -> None:
        """Método constructor de la clase.

        Abre la conexión con DynamoDB y guarda en _table la referencia a la
        tabla CorporateLog.
        No debe invocarse directamente, sino a través de get_instance().
        Lanza DataAccessError si no puede conectarse.
        Lanza RuntimeError si se intenta instanciar directamente.
        """
        if type(self)._instance is not None:
            raise RuntimeError("""No instanciar directamente.
                Use CorporateLogDAO.get_instance()""")
        try:
            dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
            self._table = dynamodb.Table("CorporateLog")
            # Verificar que la tabla existe y es accesible
            _ = self._table.table_status
        except ClientError as e:
            raise DataAccessError(
                f"No se pudo conectar a la tabla CorporateLog: {e}"
            ) from e
        except Exception as e:
            raise DataAccessError(
                f"Error inesperado al inicializar CorporateLogDAO: {e}"
            ) from e

    @classmethod
    def get_instance(cls) -> CorporateLogDAO:
        """Método estático que expone la instancia única.

        Si _instance es None, adquiere _lock, crea la instancia y la guarda;
        en cualquier caso, retorna la instancia existente.

        Lanza DataAccessError si falla la creación de la instancia.

        Returns:
            CorporateLogDAO: Instancia única de la clase.
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
                            f"Error creando instancia de CorporateLogDAO: {e}"
                        ) from e
        return cls._instance

    def write_entry(
        self,
        uuid: str,
        session_id: str,
        action: str,
        item_id: Optional[str],
        timestamp: str,
    ) -> None:
        """Inserta un registro de auditoría en la tabla CorporateLog.

        No retorna valor: si el registro no se pudo escribir,
        lanza DataAccessError.

        Args:
            uuid: UUID del cliente que realizó la petición.
            session_id: El ID de la sesión (generado con uuid4).
            action: La acción realizada (get, set, list o subscribe).
            item_id: El ID del registro afectado (None para list/subscribe).
            timestamp: El timestamp de la acción en formato string.
        """
        item = {
            "id": uuid,
            "CPUid": uuid,
            "sessionid": session_id,
            "timestamp": timestamp,
            "action": action,
        }

        if item_id is not None:
            item["item_id"] = item_id

        try:
            self._table.put_item(Item=item)
        except ClientError as e:
            raise DataAccessError(
                f"Error escribiendo en CorporateLog: {e}"
            ) from e
        except Exception as e:
            raise DataAccessError(
                f"Error inesperado escribiendo registro de auditoría: {e}"
            ) from e
