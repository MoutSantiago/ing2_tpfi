"""Módulo que define las excepciones propias del cliente.

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""


class InvalidRequestError(Exception):
    """La petición de entrada no tiene un formato o contenido válido."""


class ConnectionLostError(Exception):
    """No se pudo establecer o mantener la comunicación con el servidor."""
