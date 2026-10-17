"""Módulo encargado de mostrar cada notificación recibida del servidor.

Está separada de ObserverClient para que este no conozca los detalles de la
salida, y para poder reemplazarla por un mock en los tests.

Cada notificación se muestra por pantalla como un JSON multilínea y, si se
configuró un archivo de salida, se guarda dentro de un array JSON en ese
archivo.

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

INDENT = 2
"""Cantidad de espacios usados para indentar el JSON de salida."""


class NotificationWriter:
    """Escribe notificaciones por pantalla y, opcionalmente, en un archivo."""

    _output_path: Optional[str]
    """Atributo privado de instancia con la ruta del archivo donde se
    guardan las notificaciones. Vale None si no se especificó un archivo
    de salida."""

    def __init__(self, output_path: Optional[str]) -> None:
        """
        Inicializa el escritor de notificaciones.

        Si se proporciona una ruta, comprueba que el archivo
        pueda abrirse en modo agregar. Si no existe, se crea.

        Args:
            output_path: Ruta del archivo de salida o None.

        Raises:
            OSError: si no se puede abrir el archivo indicado.
        """
        # Guardamos la ruta recibida. Si es None, las notificaciones
        # solamente se mostrarán por salida estándar.
        self._output_path = output_path

        # Validamos la ruta durante la inicialización para detectar
        # problemas antes de recibir la primera notificación.
        if self._output_path is not None:
            # El modo "a" permite crear el archivo sin borrar lo que ya
            # tenía. La sentencia with lo cierra automáticamente. Si
            # ocurre un error, el OSError se propaga al invocador.
            with open(self._output_path, "a", encoding="utf-8"):
                pass
            logger.info(
                "Las notificaciones se guardarán en %s", self._output_path
            )

    def show(self, message: dict) -> None:
        """
        Muestra una notificación por pantalla, sin tocarla en el archivo.

        Se utiliza para los mensajes que solo deben verse en la terminal
        del observer, como la confirmación de suscripción del servidor.

        Args:
            message: Diccionario con los datos a mostrar.
        """
        # Convertimos el diccionario en un JSON multilínea.
        # ensure_ascii=False conserva los caracteres Unicode,
        # como las tildes y la letra ñ, sin convertirlos en
        # secuencias como '\\u00f3'.
        pretty_json = json.dumps(
            message,
            ensure_ascii=False,
            indent=INDENT,
        )

        # Mostramos el mensaje por salida estándar.
        # flush=True fuerza el vaciado del buffer para que el
        # mensaje sea visible inmediatamente.
        print(pretty_json, flush=True)
        logger.debug("Mensaje mostrado: %s", message)

    def write(self, message: dict) -> None:
        """
        Muestra una notificación y, si corresponde, la guarda en el archivo.

        La notificación se muestra por pantalla como un JSON multilínea y,
        si hay un archivo configurado, se agrega al final del array JSON que
        guarda ese archivo.

        Args:
            message: Diccionario con los datos de la notificación.

        Raises:
            OSError: si falla la lectura o la escritura del archivo.

        Nota:
            La salida estándar se escribe primero. De esta manera,
            la notificación se muestra aunque falle su guardado.
        """
        # Mostramos la notificación por salida estándar.
        self.show(message)

        # Si no se configuró un archivo, no hacemos nada más.
        output_path = self._output_path

        if output_path is None:
            return

        # Leemos el array existente, le agregamos la notificación y
        # reescribimos el archivo completo. Si la escritura falla, el
        # OSError se propaga.
        messages = self._read_notifications(output_path)
        messages.append(message)
        self._write_notifications(output_path, messages)

    def _read_notifications(self, output_path: str) -> list[dict]:
        """Lee el array de notificaciones guardado en el archivo.

        Si el archivo está vacío, devuelve un array vacío. Si el archivo
        contiene el formato antiguo (una notificación JSON por línea), lo
        migra a un array.

        Args:
            output_path: Ruta del archivo de salida.

        Returns:
            La lista de notificaciones guardadas.

        Raises:
            OSError: si no se puede leer el archivo.
            ValueError: si el contenido no es interpretable como JSON.
        """
        with open(output_path, encoding="utf-8") as file:
            content = file.read().strip()

        if not content:
            return []

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Formato antiguo: una notificación JSON por línea.
            return self._read_json_lines(content)

        if isinstance(data, list):
            return data

        # El contenido era un único objeto JSON: se interpreta como el
        # formato antiguo de una notificación por línea.
        return self._read_json_lines(content)

    @staticmethod
    def _read_json_lines(content: str) -> list[dict]:
        """Interpreta el contenido como el formato de una JSON por línea.

        Args:
            content: Texto con una notificación JSON por línea.

        Returns:
            La lista de notificaciones.

        Raises:
            ValueError: si alguna línea no es un objeto JSON válido.
        """
        messages: list[dict] = []

        for line in content.splitlines():
            line = line.strip()

            if line:
                messages.append(json.loads(line))

        return messages

    @staticmethod
    def _write_notifications(
        output_path: str,
        messages: list[dict],
    ) -> None:
        """Reescribe el archivo con el array de notificaciones.

        Args:
            output_path: Ruta del archivo de salida.
            messages: Notificaciones a guardar.

        Raises:
            OSError: si no se puede escribir el archivo.
        """
        # Abrimos el archivo en modo escritura y con codificación UTF-8.
        # Cada notificación queda dentro de un único array JSON.
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(messages, file, ensure_ascii=False, indent=INDENT)
            file.write("\n")
