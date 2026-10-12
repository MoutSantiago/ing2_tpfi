"""Módulo que implementa la lógica del programa suscriptor.

Se conecta al servidor, envía la acción subscribe, queda escuchando las
notificaciones y las muestra con NotificationWriter.

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

import json
from typing import Optional


class NotificationWriter:
    """
    Escribe notificaciones JSON por pantalla y, opcionalmente,
    en un archivo de salida.

    Attributes:
        _output_path (Optional[str]): Ruta del archivo donde se
            guardan las notificaciones. Vale None si no se
            especificó un archivo de salida.
    """

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
            # El modo "a" permite agregar contenido sin borrar
            # las notificaciones que ya estaban guardadas.
            # La sentencia with cierra el archivo automáticamente.
            # Si ocurre un error, el OSError se propaga al invocador.
            with open(self._output_path, "a", encoding="utf-8"):
                pass

    def write(self, message: dict) -> None:
        """
        Muestra una notificación y, si corresponde, la guarda
        en el archivo configurado.

        Args:
            message: Diccionario con los datos de la notificación.

        Raises:
            OSError: si falla la escritura en el archivo.

        Nota:
            La salida estándar se escribe primero. De esta manera,
            la notificación se muestra aunque falle su guardado.
        """
        # Convertimos el diccionario en una única línea JSON.
        # ensure_ascii=False conserva los caracteres Unicode,
        # como las tildes y la letra ñ, sin convertirlos en
        # secuencias como '\\u00f3'.
        json_line = json.dumps(
            message,
            ensure_ascii=False,
        )

        # Mostramos la notificación por salida estándar.
        # flush=True fuerza el vaciado del buffer para que el
        # mensaje sea visible inmediatamente.
        print(json_line, flush=True)

        # Si no se configuró un archivo, no hacemos nada más.
        if self._output_path is None:
            return

        # Abrimos el archivo en modo agregar y con codificación
        # UTF-8. Cada notificación ocupa una línea independiente.
        # Si la escritura falla, el OSError se propaga.
        with open(self._output_path, "a", encoding="utf-8") as file:
            file.write(json_line + "\n")
