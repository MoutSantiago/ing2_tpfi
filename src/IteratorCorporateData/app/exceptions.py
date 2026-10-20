"""Excepciones propias de IteratorCorporateData.

Reemplazan a los valores de retorno de error en las capas inferiores y
permiten que main() traduzca cada fallo a un código de salida sin
mostrar traceback.

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""


class DataAccessError(Exception):
    """Error al acceder a la base de datos."""


class RecordNotFoundError(DataAccessError):
    """El registro solicitado no existe en la tabla."""
