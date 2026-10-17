"""Módulo encargado de emitir el resultado por salida estándar en formato JSON.

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

import json
from decimal import Decimal
from typing import Any


class JsonWrite:
    """Clase encargada de emitir el resultado por salida estándar.

    Escribe un único documento JSON con indentación de 2 espacios,
    codificación UTF-8 y sin escapar los caracteres no ASCII (por ejemplo,
    "Concepción del Uruguay"), de modo que la salida se pueda leer con un
    único json.loads.
    """

    @staticmethod
    def write(result: Any) -> None:
        """Serializa result (un diccionario o una lista) a JSON.

        Imprime el resultado por salida estándar terminado en un salto de línea
        y fuerza el vaciado del buffer (flush=True).
        Los valores numéricos de DynamoDB (Decimal) se convierten con _default,
        ya que json no sabe serializarlos.

        Args:
            result (Any): Datos de entrada
        """
        texto = json.dumps(
            result,
            default=JsonWrite._default,
            indent=2,
            ensure_ascii=False,
        )
        print(texto, flush=True)

    @staticmethod
    def _default(value) -> Any:
        """Método privado que se pasa como default a json.dumps.

        Convierte un Decimal en int si no tiene parte decimal y en float en
        caso contrario.
        Lanza TypeError con cualquier otro tipo no serializable.

        Args:
            value: Valor que json.dumps no sabe serializar por sí mismo.

        Returns:
            Any: Representación serializable del valor (int o float).

        Raises:
            TypeError: Si el tipo de value no es serializable a JSON.
        """
        if isinstance(value, Decimal):
            if value == value.to_integral_value():
                return int(value)
            return float(value)
        raise TypeError(
            f"Object of type {type(value).__name__} is not JSON serializable"
        )
