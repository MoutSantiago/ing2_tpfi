"""Tests para las excepciones de IteratorCorporateData."""

import pytest

from IteratorCorporateData.app.exceptions import (
    DataAccessError,
    RecordNotFoundError,
)


def test_record_not_found_inherits_from_data_access_error():
    """RecordNotFoundError debe heredar de DataAccessError."""
    assert issubclass(RecordNotFoundError, DataAccessError)


def test_data_access_error_catches_record_not_found():
    """DataAccessError debe capturar RecordNotFoundError."""
    with pytest.raises(DataAccessError, match="Registro inexistente"):
        raise RecordNotFoundError("Registro inexistente")


def test_data_access_error_preserves_message():
    """DataAccessError debe conservar el mensaje recibido."""
    message = "No se pudo acceder a DynamoDB."

    with pytest.raises(DataAccessError, match=message) as exc_info:
        raise DataAccessError(message)

    assert str(exc_info.value) == message


def test_record_not_found_preserves_message():
    """RecordNotFoundError debe conservar el mensaje recibido."""
    message = "No existe un registro con el ID solicitado."

    with pytest.raises(RecordNotFoundError, match=message) as exc_info:
        raise RecordNotFoundError(message)

    assert str(exc_info.value) == message


def test_data_access_error_preserves_original_exception():
    """La excepción original debe conservarse mediante __cause__."""
    original_error = RuntimeError("Error original de prueba")

    with pytest.raises(DataAccessError) as exc_info:
        try:
            raise original_error
        except RuntimeError as error:
            raise DataAccessError(
                "Falló el acceso a la base de datos."
            ) from error

    assert exc_info.value.__cause__ is original_error
