"""Excepciones propias de IteratorCorporateData."""


class DataAccessError(Exception):
    """Error al acceder a la base de datos."""


class RecordNotFoundError(DataAccessError):
    """El registro solicitado no existe en la tabla."""
