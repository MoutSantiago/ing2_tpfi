"""Módulo encargado de recibir peticiones y retornar respuestas.

Escucha conexiones TCP, interpreta el JSON de cada petición y la deriva al
proxy (get, set, list) o al publisher (subscribe), sin conocer los DAOs.

Patrón: Ninguno

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

import json
import socket
import threading
from typing import Any

from SingletonProxyObserverTPFI.app.observer.publisher import Publisher

from .exceptions import DataAccessError, RecordNotFoundError
from .observer.client_observer import ClientObserver
from .observer.observer import ObserverUnavailableError


class Server:
    """
    Servidor TCP encargado de recibir y procesar solicitudes.

    El Server actúa como intermediario entre los clientes TCP y los
    componentes que implementan los patrones Proxy y Observer.
    """

    # Tamaño máximo permitido para una petición JSON.
    # Evita aceptar mensajes arbitrariamente grandes.
    MAX_REQUEST_SIZE = 64 * 1024

    # Tiempo máximo de espera para recibir una petición.
    CLIENT_TIMEOUT = 10.0

    # Acciones válidas según la especificación del TPFI.
    VALID_ACTIONS = {"get", "set", "list", "subscribe"}

    # Campos correspondientes al tuple CorporateData.
    #
    # ID NO se incluye porque se trata como la clave del registro.
    # Para un set, se exige al menos uno de estos campos.
    CORPORATE_DATA_FIELDS = {
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
    }

    class CorporateDataProxy: ...

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        data: CorporateDataProxy | None = None,
        publisher: Publisher | None = None,
    ) -> None:
        """
        Inicializa el servidor.

        Args:
            host: dirección IP en la que escuchará el servidor.
            port: puerto TCP en el que escuchará.
            data: instancia del CorporateDataProxy.
            publisher: instancia del Publisher.

        Raises:
            ValueError: si data o publisher no fueron proporcionados.
        """
        if data is None:
            raise ValueError("data es obligatorio")

        if publisher is None:
            raise ValueError("publisher es obligatorio")

        # Dirección donde escucha el servidor.
        self._host = host

        # Puerto TCP.
        self._port = port

        # Socket de escucha.
        # Todavía NO se crea aquí porque la especificación indica
        # que el socket debe abrirse dentro de serve_forever().
        self._sock: socket.socket | None = None

        # Dependencia del patrón Proxy.
        self._data = data

        # Dependencia del patrón Observer.
        self._publisher = publisher

        # Evento utilizado para detener el bucle principal.
        self._stop_event = threading.Event()

    def serve_forever(self) -> None:
        """
        Abre el socket y comienza a aceptar conexiones.

        Cada cliente se procesa en un thread independiente.

        Raises:
            OSError: si no es posible abrir o utilizar el puerto.
        """
        # Creamos el socket TCP IPv4.
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Permite reutilizar rápidamente el puerto luego de detener
        # el servidor.
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            # bind asocia el socket con host + port.
            #
            # Si otro proceso está utilizando el puerto, aquí puede
            # producirse OSError.
            sock.bind((self._host, self._port))

            # Ponemos el socket en modo escucha.
            sock.listen()

            # Guardamos el socket para que stop() pueda cerrarlo.
            self._sock = sock

            # Eliminamos cualquier estado previo de stop.
            self._stop_event.clear()

            while not self._stop_event.is_set():
                try:
                    # Esperamos una conexión entrante.
                    conn, addr = sock.accept()

                except OSError:
                    # Cuando stop() cierra el socket, accept() puede
                    # generar OSError. En ese caso, si efectivamente
                    # se pidió detener el servidor, terminamos
                    # normalmente.
                    if self._stop_event.is_set():
                        break

                    # Si no se pidió detener el servidor, propagamos
                    # el error porque representa un problema real.
                    raise

                # Cada conexión se procesa en su propio thread.
                thread = threading.Thread(
                    target=self._handle_client,
                    args=(conn, addr),
                    daemon=True,
                )

                thread.start()

        finally:
            # Nos aseguramos de liberar el socket incluso si ocurre
            # una excepción.
            try:
                sock.close()
            except OSError:
                pass

            if self._sock is sock:
                self._sock = None

    def stop(self) -> None:
        """
        Solicita la detención del servidor.

        No cierra los sockets pertenecientes a los clientes que ya
        realizaron subscribe.
        """
        # Indicamos al thread principal que debe abandonar el bucle.
        self._stop_event.set()

        # Cerramos únicamente el socket de escucha.
        #
        # Los sockets de los ClientObserver pertenecen a las
        # conexiones de los suscriptores y no deben cerrarse acá.
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass

            self._sock = None

    def _handle_client(
        self,
        conn: socket.socket,
        addr: Any,
    ) -> None:
        """
        Atiende una conexión TCP individual.

        Args:
            conn: socket de comunicación con el cliente.
            addr: dirección del cliente.
        """
        # Por defecto, una conexión normal debe cerrarse al terminar.
        # En caso de subscribe, _dispatch devuelve None y la conexión
        # queda bajo responsabilidad del ClientObserver.
        close_connection = True

        try:
            # Evitamos que un cliente quede bloqueado indefinidamente
            # sin enviar datos.
            conn.settimeout(self.CLIENT_TIMEOUT)

            # makefile permite trabajar cómodamente con líneas.
            #
            # Sin embargo, para respetar el tamaño máximo hacemos
            # nuestra propia lectura de bytes.
            raw_request = self._receive_request(conn)

            # Decodificamos el JSON.
            request = json.loads(raw_request)

            # Verificamos que la petición tenga la estructura mínima.
            if not self._validate(request):
                self._send_error(
                    conn,
                    "Petición inválida.",
                )
                return

            # Ejecutamos la operación correspondiente.
            response = self._dispatch(request, conn)

            # subscribe devuelve None porque no debe responder y cerrar
            # inmediatamente la conexión.
            if response is None:
                close_connection = False
                return

            # Las operaciones get/set/list sí devuelven información.
            self._send_json(conn, response)

        except json.JSONDecodeError:
            # El cliente envió algo que no es JSON válido.
            self._send_error(conn, "JSON inválido.")

        except (DataAccessError, RecordNotFoundError) as exc:
            # Errores provenientes del Proxy o de los DAOs.
            self._send_error(conn, str(exc))

        except ObserverUnavailableError as exc:
            # En principio el error del observer se maneja en el
            # Publisher. Lo capturamos para evitar que el thread
            # termine mostrando una excepción no controlada.
            self._send_error(conn, str(exc))

        except (OSError, TimeoutError) as exc:
            # Problemas de socket o timeout.
            #
            # Si el cliente cerró la conexión, simplemente terminamos
            # el procesamiento.
            try:
                self._send_error(conn, str(exc))
            except OSError:
                pass

        except Exception as exc:
            # El servidor no debe caer por una petición individual.
            #
            # Esta captura es deliberadamente amplia porque el
            # requisito establece que un error de una petición no
            # debe detener al servidor.
            try:
                self._send_error(
                    conn,
                    f"Error interno: {exc}",
                )
            except OSError:
                pass

        finally:
            # Una suscripción mantiene el socket abierto.
            #
            # Para get/set/list, o ante errores, se cierra.
            if close_connection:
                try:
                    conn.close()
                except OSError:
                    pass

    def _receive_request(self, conn: socket.socket) -> str:
        r"""
        Recibe una petición JSON terminada en '\\n'.

        Args:
            conn: socket del cliente.

        Returns:
            Texto JSON recibido.

        Raises:
            ValueError: si la petición supera el tamaño máximo.
            ConnectionError: si el cliente cierra la conexión.
        """
        data = bytearray()

        while len(data) < self.MAX_REQUEST_SIZE:
            chunk = conn.recv(4096)

            if not chunk:
                # El cliente cerró la conexión antes de terminar
                # de enviar la petición.
                if not data:
                    raise ConnectionError("El cliente cerró la conexión.")

                break

            data.extend(chunk)

            # El protocolo utiliza una línea por mensaje.
            if b"\n" in chunk:
                break

        if len(data) >= self.MAX_REQUEST_SIZE:
            raise ValueError("La petición supera el tamaño máximo permitido.")

        # Nos quedamos solamente con la primera línea.
        line = bytes(data).split(b"\n", 1)[0]

        return line.decode("utf-8")

    def _validate(self, request: Any) -> bool:
        """
        Valida los campos mínimos de una petición.

        Una petición válida debe:

        - ser un objeto/diccionario JSON;
        - contener UUID;
        - contener ACTION;
        - utilizar una acción válida;
        - incluir ID para get/set;
        - incluir al menos un campo de CorporateData para set.

        Args:
            request: objeto obtenido luego de decodificar el JSON.

        Returns:
            True si la petición cumple las condiciones mínimas.
            False en caso contrario.
        """
        # json.loads() puede devolver un string, una lista, un número,
        # etc. Solamente aceptamos objetos JSON.
        if not isinstance(request, dict):
            return False

        # UUID es obligatorio.
        uuid = request.get("UUID")

        if not isinstance(uuid, str) or not uuid.strip():
            return False

        # ACTION también es obligatorio.
        action = request.get("ACTION")

        if not isinstance(action, str):
            return False

        # Normalizamos para evitar aceptar "GET", " Get ", etc.
        action = action.strip().lower()

        if action not in self.VALID_ACTIONS:
            return False

        # get y set necesitan identificar el registro.
        if action in {"get", "set"}:
            record_id = request.get("ID")

            if not isinstance(record_id, str) or not record_id.strip():
                return False

        # set debe modificar al menos un campo del tuple.
        if action == "set":
            has_data_field = any(
                field in request for field in self.CORPORATE_DATA_FIELDS
            )

            if not has_data_field:
                return False

        return True

    def _dispatch(
        self,
        request: dict,
        conn: socket.socket,
    ) -> dict | list | None:
        """
        Deriva una petición hacia el componente correspondiente.

        Args:
            request: petición validada.
            conn: socket del cliente.

        Returns:
            Resultado de get/set/list, o None para subscribe.
        """
        action = request["ACTION"].strip().lower()

        if action == "get":
            # El Server no accede directamente a la base.
            # Todo el acceso pasa por CorporateDataProxy.
            return self._data.get(
                request["ID"],
                request["UUID"],
            )

        if action == "set":
            # Construimos únicamente los campos de CorporateData
            # presentes en la petición.
            fields = {
                field: request[field]
                for field in self.CORPORATE_DATA_FIELDS
                if field in request
            }

            return self._data.set(
                request["ID"],
                fields,
                request["UUID"],
            )

        if action == "list":
            return self._data.list(
                request["UUID"],
            )

        if action == "subscribe":
            self._handle_subscribe(
                conn,
                request["UUID"],
            )

            # None tiene un significado especial para _handle_client:
            # mantener la conexión abierta.
            return None

        # _validate debería impedir llegar hasta acá.
        raise ValueError(f"Acción desconocida: {action}")

    def _handle_subscribe(
        self,
        conn: socket.socket,
        uuid: str,
    ) -> None:
        """
        Registra un nuevo cliente como observer.

        Primero se realiza la auditoría de la suscripción mediante
        CorporateDataProxy. Solamente si la auditoría tiene éxito
        se crea y registra el ClientObserver.

        Args:
            conn: socket del cliente.
            uuid: UUID del cliente.
        """
        # La suscripción debe quedar registrada en CorporateLog.
        self._data.audit_subscription(uuid)

        # Solamente después de auditar creamos el observer.
        observer = ClientObserver(
            sock=conn,
            uuid=uuid,
        )

        # El Publisher queda encargado de mantener al observer y
        # notificarlo cuando exista una modificación.
        self._publisher.subscribe(observer)

    @staticmethod
    def _send_json(
        conn: socket.socket,
        data: dict | list,
    ) -> None:
        r"""
        Serializa y envía una respuesta JSON terminada en '\\n'.

        Args:
            conn: socket del cliente.
            data: respuesta que será enviada.
        """
        payload = json.dumps(data)
        payload += "\n"

        conn.sendall(payload.encode("utf-8"))

    @staticmethod
    def _send_error(
        conn: socket.socket,
        message: str,
    ) -> None:
        """
        Envía una respuesta de error al cliente.

        Args:
            conn: socket del cliente.
            message: descripción del error.
        """
        response = {
            "Error": message,
        }

        Server._send_json(conn, response)
