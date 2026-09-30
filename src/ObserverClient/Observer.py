"""
Módulo que implementa el Patrón Observer para la gestión de notificaciones
a clientes subscriptos en el servidor de aplicaciones del TPFI.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class Observador(ABC):
    """Interfaz común para todos los clientes u observadores subscriptos."""

    @abstractmethod
    def actualizar(self, datos_actualizados: Dict[str, Any]) -> None:
        """Método invocado automáticamente cuando el sujeto cambia de estado."""
        pass


class SubjectCorporateData:
    """
    Sujeto observado (Publisher): Mantiene la lista de sockets o clientes
    subscriptos (acción 'subscribe') y los notifica ante cada actualización ('set').
    """

    def __init__(self) -> None:
        self._observadores: List[Observador] = []
        self._estado_actual: Dict[str, Any] = {}

    def agregar_observador(self, observador: Observador) -> None:
        """Registra un nuevo cliente subscripto si no se encuentra en la lista."""
        if observador not in self._observadores:
            self._observadores.append(observador)
            logging.info(
                f"[Observer] Cliente subscripto exitosamente. Total subscriptores: {len(self._observadores)}"
            )

    def remover_observador(self, observador: Observador) -> None:
        """Remueve a un cliente de la lista de subscripciones."""
        try:
            self._observadores.remove(observador)
            logging.info(
                f"[Observer] Cliente desuscripto. Total subscriptores restantes: {len(self._observadores)}"
            )
        except ValueError:
            pass

    def notificar_observadores(self, datos: Dict[str, Any]) -> None:
        """Dispara la notificación a todos los clientes subscriptos."""
        self._estado_actual = datos
        logging.info(
            f"[Observer] Notificando cambios a {len(self._observadores)} clientes subscriptos."
        )
        for observador in self._observadores:
            observador.actualizar(self._estado_actual)


class ClienteSocketObservador(Observador):
    """
    Observador Concreto: Representa al cliente conectado mediante un socket TCP
    que aguarda notificaciones en tiempo real ante cambios en CorporateData.
    """

    def __init__(self, uuid_cliente: str, socket_conexion: Any) -> None:
        self.uuid_cliente = uuid_cliente
        self.socket_conexion = socket_conexion

    def actualizar(self, datos_actualizados: Dict[str, Any]) -> None:
        """Envía el JSON de actualización a través del socket hacia el cliente."""
        logging.info(
            f"[ClienteSocketObserver] Enviando actualización al UUID: {self.uuid_cliente}"
        )
        # Lógica de envío por socket TCP hacia el ObserverClient
        # self.socket_conexion.sendall(json.dumps(datos_actualizados).encode('utf-8'))
