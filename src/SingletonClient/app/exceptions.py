"""
Excepciones propias del cliente SingletonClient.

Ingeniería de Software II - UADER FCyT (2026)
"""


class InvalidRequestError(Exception):
    """La petición de entrada no tiene un formato o contenido válido."""


class ConnectionLostError(Exception):
    """No se pudo establecer o mantener la comunicación con el servidor."""
