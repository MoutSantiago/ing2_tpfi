"""Pruebas de las excepciones propias de SingletonClient."""

import pytest

from SingletonClient.app.exceptions import (
    ConnectionLostError,
    InvalidRequestError,
)


def test_exceptions_inherit_from_exception():
    """Ambas excepciones heredan de Exception."""
    assert issubclass(InvalidRequestError, Exception)
    assert issubclass(ConnectionLostError, Exception)


def test_exceptions_are_independent():
    """Ninguna excepción es subclase de la otra."""
    assert not issubclass(InvalidRequestError, ConnectionLostError)
    assert not issubclass(ConnectionLostError, InvalidRequestError)


def test_invalid_request_error_preserves_message():
    """InvalidRequestError conserva su mensaje."""
    message = "El JSON de entrada no es válido."

    with pytest.raises(InvalidRequestError, match=message):
        raise InvalidRequestError(message)


def test_connection_lost_error_preserves_message():
    """ConnectionLostError conserva su mensaje."""
    message = "No se pudo conectar con el servidor."

    with pytest.raises(ConnectionLostError, match=message):
        raise ConnectionLostError(message)


def test_connection_lost_error_chains_original_exception():
    """La excepción original se conserva mediante __cause__."""
    original_error = ConnectionRefusedError("Conexión rechazada")

    with pytest.raises(ConnectionLostError) as exc_info:
        try:
            raise original_error
        except OSError as error:
            raise ConnectionLostError(
                "No se pudo comunicar con el servidor."
            ) from error

    assert exc_info.value.__cause__ is original_error
