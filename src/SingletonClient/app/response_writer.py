"""Módulo encargado de mostrar la respuesta del servidor.

ResponseWriter escribe la respuesta del servidor como un único documento
JSON: por salida estándar si no se informó una ruta, o en el archivo
indicado en caso contrario. Está separada de SingletonClient para que este
no conozca los detalles de la salida y para poder reemplazarla por un mock
en los tests.

Patrón: Ninguno

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

import json
import os
from typing import Any, Optional

INDENT = 2
"""Cantidad de espacios usados para indentar el JSON de salida."""


class ResponseWriter:
    """Muestra la respuesta del servidor por pantalla o en un archivo."""

    _output_path: Optional[str]
    """Atributo privado de instancia con la ruta del archivo de salida.
    Vale None si no se informó, en cuyo caso se escribe por salida
    estándar."""

    def __init__(self, output_path: Optional[str]) -> None:
        """Inicializa el escritor de la respuesta.

        Recibe la ruta del archivo de salida (o None) y la guarda. Si se
        informó una ruta, verifica que el directorio destino exista y sea
        escribible, sin crear ni vaciar el archivo, de modo que un error en
        la salida se detecte al arrancar y no después de haber consultado
        al servidor.

        Args:
            output_path: Ruta del archivo de salida o None.

        Raises:
            OSError: si el directorio destino no existe o no es escribible.
        """
        self._output_path = output_path

        if output_path is not None:
            self._check_output_directory(output_path)

    @staticmethod
    def _check_output_directory(output_path: str) -> None:
        """Comprueba que el directorio destino exista y sea escribible.

        No crea ni vacía el archivo de salida: solo valida el directorio
        que lo contiene.

        Args:
            output_path: Ruta del archivo de salida.

        Raises:
            OSError: si el directorio no existe o no admite escritura.
        """
        directory = os.path.dirname(os.path.abspath(output_path))

        if not os.path.isdir(directory):
            raise OSError(f"El directorio de salida no existe: {directory}")

        if not os.access(directory, os.W_OK):
            raise OSError(
                f"El directorio de salida no es escribible: {directory}"
            )

    def write(self, response: Any) -> None:
        """Muestra la respuesta como un único documento JSON.

        La respuesta se serializa con indentación de dos espacios y sin
        escapar los caracteres no ASCII, y se termina con un salto de línea.
        Si no hay una ruta configurada, se imprime por salida estándar
        forzando el vaciado del buffer. En caso contrario, se reemplaza el
        contenido del archivo (modo "w", UTF-8) y no se imprime nada.

        Args:
            response: Respuesta del servidor, que puede ser un diccionario,
                una lista o un texto.

        Raises:
            OSError: si falla la escritura del archivo.
        """
        document = (
            json.dumps(response, ensure_ascii=False, indent=INDENT) + "\n"
        )
        output_path = self._output_path

        if output_path is None:
            print(document, end="", flush=True)
            return

        with open(output_path, "w", encoding="utf-8") as file:
            file.write(document)
