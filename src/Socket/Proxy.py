"""Módulo exclusivo para la implementación del Patrón Proxy según los
lineamientos de Refactoring.Guru para el TPFI.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union


class ServidorCorporateData(ABC):
    """
    Interfaz de Asunto (Subject): Define la interfaz común para el ServidorReal
    y el Proxy de modo que ambos sean intercambiables para el cliente.
    """

    @abstractmethod
    def get_data(self, record_id: str) -> Union[Dict[str, Any], str]:
        """Recupera un registro específico de CorporateData."""
        pass

    @abstractmethod
    def set_data(self, data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """Crea o modifica un registro en CorporateData."""
        pass

    @abstractmethod
    def list_data(self) -> Union[List[Dict[str, Any]], str]:
        """Lista todos los registros de CorporateData."""
        pass


class ServidorRealCorporateData(ServidorCorporateData):
    """
    Asunto Real (RealSubject): Contiene la lógica principal y el acceso real
    a la base de datos (se comunica con el Singleton de CorporateData).
    """

    def get_data(self, record_id: str) -> Union[Dict[str, Any], str]:
        logging.info(
            f"[ServidorReal] Ejecutando GET físico para el ID: {record_id}"
        )
        # Aquí se invoca la lógica de persistencia real (Singleton CorporateData)
        return {"id": record_id, "status": "encontrado"}

    def set_data(self, data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        logging.info(f"[ServidorReal] Ejecutando SET físico con datos: {data}")
        # Lógica real de actualización o inserción
        return data

    def list_data(self) -> Union[List[Dict[str, Any]], str]:
        logging.info("[ServidorReal] Ejecutando LIST físico de registros.")
        # Lógica real para retornar todos los elementos
        return [{"id": "UADER-FCYT-IS2"}]


class ProxyCorporateData(ServidorCorporateData):
    """
    Proxy: Intermediario que controla el acceso al Asunto Real.
    Gestiona la auditoría (CorporateLog) y la retransmisión por Observer ante cambios.
    """

    def __init__(self, uuid_cliente: str, session_id: str) -> None:
        self._servidor_real: Union[ServidorRealCorporateData, None] = None
        self.uuid_cliente = uuid_cliente
        self.session_id = session_id

    def _obtener_servidor_real(self) -> ServidorRealCorporateData:
        """Carga diferida (Lazy initialization) del Asunto Real."""
        if self._servidor_real is None:
            logging.debug("[Proxy] Instanciando el ServidorRealCorporateData.")
            self._servidor_real = ServidorRealCorporateData()
        return self._servidor_real

    def _auditar_acceso(self, accion: str) -> bool:
        """Genera el registro de pista de auditoría en la tabla CorporateLog[cite: 5]."""
        logging.info(
            f"[Proxy] Auditando acción '{accion}' | UUID Cliente: {self.uuid_cliente} | Sesión: {self.session_id}"
        )
        return True

    def get_data(self, record_id: str) -> Union[Dict[str, Any], str]:
        if not self._auditar_acceso("get"):
            return "Error: Acceso no autorizado"

        return self._obtener_servidor_real().get_data(record_id)

    def set_data(self, data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        if not self._auditar_acceso("set"):
            return "Error: Acceso no autorizado"

        resultado = self._obtener_servidor_real().set_data(data)

        # Retransmisión al cliente solicitante y observadores (Patrón Observer)[cite: 5]
        self._notificar_observadores(resultado)

        return resultado

    def list_data(self) -> Union[List[Dict[str, Any]], str]:
        if not self._auditar_acceso("list"):
            return "Error: Acceso no autorizado"

        return self._obtener_servidor_real().list_data()

    def _notificar_observadores(
        self, datos_actualizados: Dict[str, Any]
    ) -> None:
        """Método auxiliar para disparar las notificaciones del Observer."""
        logging.info(
            f"[Proxy -> Observer] Notificando cambios a los subscriptores: {datos_actualizados}"
        )
