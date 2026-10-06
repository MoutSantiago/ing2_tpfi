"""Módulo que recibe las múltiples acciones del servidor.

Su función es recibir y aplicar las reglas de negocio definidas para cada
acción, derivando las funciones a las demás clases.

Patrón: Proxy

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from SingletonProxyObserverTPFI.app.observer.subscription_manager import (
    SubscriptionManager,
)
from SingletonProxyObserverTPFI.app.proxy.corporate_data_interface import (
    CorporateDataInterface,
)
from SingletonProxyObserverTPFI.app.singleton.corporate_log_dao import (
    CorporateLogDAO,
)


class CorporateDataProxy(CorporateDataInterface):
    """Clase que implementa el patrón proxy para la tabla CorporateData.

    Recibe las acciones del servidor y aplica las reglas de negocio de cada
    caso, delegando la lectura/escritura de datos al objeto real (en
    producción, CorporateDataDAO).

    Para cada acción, el proxy PRIMERO registra la auditoría en CorporateLog
    y RECIÉN DESPUÉS opera sobre los datos. Si el registro de auditoría
    falla, la operación no se ejecuta: así ningún dato cambia sin quedar
    auditado.

    En set, además de auditar y modificar, notifica el cambio a los
    suscriptores a través del publisher, que ya se encarga de aislar a los
    observers que no estén disponibles.
    """

    _real: CorporateDataInterface
    """Atributo privado de instancia con el objeto que realiza las consultas
    a la tabla CorporateData (en producción, CorporateDataDAO).
    Se tipa con la interfaz para poder reemplazar al DAO por un mock en los
    tests.
    """

    _log: CorporateLogDAO
    """Atributo privado de instancia con el objeto que escribe en la tabla
    CorporateLog.
    """

    _publisher: SubscriptionManager
    """Atributo privado de instancia con el publisher que notifica a los
    suscriptores sobre los cambios.
    """

    def __init__(
        self,
        real: CorporateDataInterface,
        log: CorporateLogDAO,
        publisher: SubscriptionManager,
    ) -> None:
        """Método constructor de la clase.

        Recibe las tres dependencias y las guarda en _real, _log y _publisher.

        Args:
            real (CorporateDataInterface): Objeto real que accede a la tabla
                CorporateData (CorporateDataDAO en producción).
            log (CorporateLogDAO): Objeto que escribe la pista de auditoría.
            publisher (SubscriptionManager): Publisher que notifica los
                cambios a los suscriptores.
        """
        self._real = real
        self._log = log
        self._publisher = publisher

    def _audit(
        self, uuid: str, action: str, item_id: Optional[str] = None
    ) -> None:
        """Escribe el registro de auditoría en CorporateLog.

        Genera un session_id nuevo con uuid4() y un timestamp en formato
        ISO 8601 (UTC), y delega la escritura a CorporateLogDAO.write_entry.

        Lanza DataAccessError si no se puede escribir la auditoría. Como la
        auditoría se realiza antes que la operación, este fallo impide que la
        acción se ejecute.

        Args:
            uuid (str): UUID del cliente que realiza la petición.
            action (str): Acción ejecutada (get, set, list o subscribe).
            item_id (Optional[str]): ID del registro afectado; None para
                list/subscribe, que no afectan a un registro en particular.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        self._log.write_entry(
            uuid=uuid,
            session_id=str(uuid4()),
            action=action,
            item_id=item_id,
            timestamp=timestamp,
        )

    def get(self, id: str, uuid: str) -> dict[str, str]:
        """Maneja una acción get.

        Audita la acción y recién entonces delega la lectura al objeto real.

        Args:
            id (str): Identificador del registro solicitado.
            uuid (str): UUID del cliente que realiza la petición.

        Returns:
            dict[str, str]: Registro solicitado.

        Raises:
            DataAccessError: Si falla la auditoría.
            RecordNotFoundError: Si el registro no existe, propagada desde
                el objeto real.
        """
        self._audit(uuid, "get", id)
        return self._real.get(id, uuid)

    def set(self, id: str, data: dict[str, str], uuid: str) -> dict[str, str]:
        """Maneja una acción set.

        Audita la acción, delega la escritura al objeto real y, si salió
        bien, notifica el cambio a los suscriptores con un mensaje que lleva
        el uuid, el id, la acción "change" y el registro resultante.

        Un fallo al notificar a un suscriptor no afecta el resultado del set:
        el publisher se ocupa de aislar y desuscribir a los observers que ya
        no están disponibles.

        Args:
            id (str): Identificador del registro a crear o modificar.
            data (dict[str, str]): Campos a escribir sobre el registro.
            uuid (str): UUID del cliente que realiza la petición.

        Returns:
            dict[str, str]: Registro resultante tras aplicar el cambio.

        Raises:
            DataAccessError: Si falla la auditoría o el acceso a los datos.
        """
        self._audit(uuid, "set", id)
        registro = self._real.set(id, data, uuid)

        # El mensaje combina los identificadores con el registro resultante,
        # de modo que el observer reciba el cambio completo en una misma
        # respuesta JSON.
        mensaje = {
            "UUID": uuid,
            "ID": id,
            "ACTION": "change",
            **registro,
        }
        self._publisher.publish_change(mensaje)

        return registro

    def list(self, uuid: str) -> list[dict[str, str]]:
        """Maneja una acción list.

        Audita la acción (sin id, porque no afecta a un registro en
        particular) y recién entonces delega la lectura al objeto real.

        Args:
            uuid (str): UUID del cliente que realiza la petición.

        Returns:
            list[dict[str, str]]: Todos los registros de la tabla.

        Raises:
            DataAccessError: Si falla la auditoría.
        """
        self._audit(uuid, "list")
        return self._real.list(uuid)

    def audit_subscription(self, uuid: str) -> None:
        """Registra en CorporateLog la acción subscribe del cliente uuid.

        No pertenece a la interfaz CorporateDataInterface: lo invoca el
        Server antes de registrar al observer, para que el servidor no
        dependa de los DAOs.

        Lanza DataAccessError si falla; en ese caso la suscripción no debe
        realizarse.

        Args:
            uuid (str): UUID del cliente que se va a suscribir.
        """
        self._audit(uuid, "subscribe")
