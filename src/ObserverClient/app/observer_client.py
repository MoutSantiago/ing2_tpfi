"""Módulo que implementa la lógica del programa suscriptor.

Esta clase no conoce los detalles de la red ni de la salida: delega en
ServerConnection y NotificationWriter, que recibe ya construidos para poder
reemplazarlos por mocks en los tests. No implementa el patrón Observer (ese
vive en el servidor): es el suscriptor remoto.

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

import logging
import threading
import uuid

from ObserverClient.app.exceptions import ConnectionLostError
from ObserverClient.app.notification_writer import NotificationWriter
from ObserverClient.app.server_connection import ServerConnection

DEFAULT_RETRY_INTERVAL = 30

logger = logging.getLogger(__name__)


class ObserverClient:
    """Cliente suscriptor remoto del servidor.

    Se conecta al servidor, envía la acción subscribe, queda escuchando las
    notificaciones y las muestra con NotificationWriter. Si se interrumpe la
    conexión (o el servidor no está disponible al arrancar), espera un
    intervalo y vuelve a intentar, reenviando la suscripción en cada
    reconexión. Solo termina por cancelación manual (stop()) o por una
    excepción distinta del corte de la conexión.
    """

    _host: str
    """Atributo privado de instancia con el nombre o la dirección del
    servidor. Solo para los logs."""

    _port: int
    """Atributo privado de instancia con el puerto del servidor.
    Solo para los logs."""

    _uuid: str
    """Atributo privado de instancia con el identificador de la CPU
    donde se ejecuta el programa."""

    _retry_interval: int
    """Atributo privado de instancia con los segundos de espera
    entre intentos."""

    _connection: ServerConnection
    """Atributo privado de instancia con el objeto que maneja el socket TCP."""

    _writer: NotificationWriter
    """Atributo privado de instancia con el objeto que muestra cada
    notificación."""

    _stop_event: threading.Event
    """Atributo privado de instancia que indica que se pidió terminar y
    permite interrumpir la espera entre reintentos."""

    def __init__(
        self,
        host: str,
        port: int,
        connection: ServerConnection,
        writer: NotificationWriter,
        retry_interval: int = DEFAULT_RETRY_INTERVAL,
    ) -> None:
        """Método constructor de la clase.

        Recibe los datos del servidor (para los logs), la conexión, el
        escritor y el intervalo de reintento, y los guarda en los atributos
        correspondientes. No abre ninguna conexión.

        Args:
            host (str): Nombre o dirección del servidor.
            port (int): Puerto del servidor.
            connection (ServerConnection): Objeto que maneja el socket TCP.
            writer (NotificationWriter): Objeto que muestra cada notificación.
            retry_interval (int): Segundos de espera entre reintentos.

        Raises:
            ValueError: si retry_interval no es mayor que cero.
        """
        # Validamos el intervalo antes de guardarlo. Un valor no positivo
        # haría que el programa reintentara sin pausa.
        if retry_interval <= 0:
            raise ValueError("retry_interval debe ser mayor que cero")

        self._host = host
        self._port = port
        self._connection = connection
        self._writer = writer
        self._retry_interval = retry_interval

        # El UUID identifica a esta CPU en la solicitud de suscripción.
        self._uuid = str(uuid.getnode())

        # El evento permite pedir la detención desde otro hilo o desde un
        # manejador de señales e interrumpir la espera entre reintentos.
        self._stop_event = threading.Event()

    def run(self) -> None:
        """Ejecuta el programa hasta que se pida detenerlo.

        Mientras no se pida detener el programa, repite: conectar, suscribirse
        y escuchar. Si alguno de esos pasos lanza ConnectionLostError,
        registra una advertencia y, antes de volver a intentar, cierra la
        conexión y espera el intervalo configurado. La conexión se cierra
        siempre al salir de cada intento, haya o no excepción.

        Cualquier otra excepción no se captura: cierra la conexión y se
        propaga hasta el main, que termina el programa.

        Returns:
            None. Retorna solo cuando se pidió detener el programa.
        """
        # El bucle se repite mientras no se haya pedido detener el programa.
        while not self._stop_event.is_set():
            try:
                logger.info(
                    "Conectando al servidor %s:%d", self._host, self._port
                )
                self._connection.connect()
                self._subscribe()
                self._listen()
            except ConnectionLostError as error:
                # El corte de la conexión no termina el programa: se
                # registra como advertencia y se reintenta más abajo.
                logger.warning(
                    "Se perdió la conexión con %s:%d: %s",
                    self._host,
                    self._port,
                    error,
                )
            finally:
                # La conexión se cierra siempre al salir de cada intento.
                self._connection.close()

            # Si stop() se invocó durante el intento, se retorna sin
            # reintentar. El cierre del finally despertó al receive.
            if self._stop_event.is_set():
                return

            self._wait_to_retry()

            # Si stop() se invocó durante la espera, se retorna también.
            if self._stop_event.is_set():
                return

    def stop(self) -> None:
        """Pide la terminación del programa.

        Activa _stop_event y cierra la conexión, lo que despierta a receive
        si estaba bloqueado esperando una notificación. Se puede invocar desde
        otro hilo o desde un manejador de señales, y no hace nada si ya se
        había invocado.
        """
        # Si ya se pidió detener, no hace nada: la conexión ya se cerró.
        if self._stop_event.is_set():
            return

        logger.info("Deteniendo el cliente...")

        # Activar el evento despierta a _wait_to_retry sin esperar el
        # intervalo completo y hace que el bucle de run() no reintente.
        self._stop_event.set()

        # Cerrar la conexión despierta a receive si estaba bloqueado
        # esperando una notificación. ServerConnection.close es idempotente.
        self._connection.close()

    def _build_request(self) -> dict:
        """Arma la solicitud de suscripción.

        Returns:
            dict: Diccionario con el UUID del cliente y la acción
                "subscribe". No incluye ID, porque el enunciado solo pide
                UUID y acción.
        """
        return {"UUID": self._uuid, "ACTION": "subscribe"}

    def _subscribe(self) -> None:
        """Envía la solicitud de suscripción.

        Raises:
            ConnectionLostError: si falla el envío (lo lanza
                ServerConnection.send).
        """
        # send() ya traduce los errores de socket a ConnectionLostError.
        request = self._build_request()
        logger.debug("Enviando suscripción: %s", request)
        self._connection.send(request)
        logger.info("Suscripción enviada a %s:%d", self._host, self._port)

    def _listen(self) -> None:
        """Bucle de escucha de notificaciones.

        Mientras no se pida detener el programa, espera con receive() y
        entrega cada mensaje a _writer.write(). Si receive() lanza ValueError
        (el mensaje no es un JSON válido), registra una advertencia y
        continúa escuchando, porque la conexión sigue sana.

        Raises:
            ConnectionLostError: si se corta la conexión.
        """
        while not self._stop_event.is_set():
            try:
                message = self._connection.receive()
            except ValueError as error:
                # La conexión sigue sana: se descarta el mensaje inválido
                # y se sigue esperando la próxima notificación.
                logger.warning("Se recibió un mensaje inválido: %s", error)
                continue

            logger.debug("Notificación recibida: %s", message)

            # write() puede lanzar OSError (por ejemplo, al escribir el
            # archivo de salida). Esa excepción no se captura: se propaga.
            self._writer.write(message)

    def _wait_to_retry(self) -> None:
        """Espera el intervalo antes de reintentar la conexión.

        Usa el evento de parada para poder interrumpir la espera: si stop()
        se invoca mientras se espera, la espera termina de inmediato.
        """
        logger.info(
            "Reintentando conexión en %d segundos", self._retry_interval
        )
        self._stop_event.wait(self._retry_interval)
