"""Tests para las excepciones de ObserverClient."""

import pytest

from ObserverClient.app.exceptions import ConnectionLostError


class TestConnectionLostError:
    """Tests para la excepción ConnectionLostError."""

    def test_es_subclase_de_exception(self):
        """Verifica que ConnectionLostError es subclase de Exception."""
        assert issubclass(ConnectionLostError, Exception)

    def test_captura_excepcion_con_mensaje(self):
        """Verifica que un except ConnectionLostError captura la excepción con
        mensaje."""
        mensaje = "Error de conexión al servidor"
        try:
            raise ConnectionLostError(mensaje)
        except ConnectionLostError as e:
            assert str(e) == mensaje
        else:
            pytest.fail("ConnectionLostError no fue lanzada")

    def test_encadenamiento_conserva_error_original(self):
        """Verifica que el encadenamiento (__cause__) conserva el error
        original."""
        error_original = OSError("Connection refused")
        try:
            raise ConnectionLostError("Fallo de conexión") from error_original
        except ConnectionLostError as e:
            assert e.__cause__ is error_original
            assert isinstance(e.__cause__, OSError)
            assert str(e.__cause__) == "Connection refused"

    def test_se_puede_instanciar_sin_argumentos(self):
        """Verifica que la excepción se puede instanciar sin argumentos."""
        e = ConnectionLostError()
        assert isinstance(e, ConnectionLostError)
        assert str(e) == ""

    def test_hereda_atributos_de_exception(self):
        """Verifica que hereda los atributos estándar de Exception."""
        e = ConnectionLostError("mensaje de prueba")
        assert hasattr(e, "args")
        assert e.args == ("mensaje de prueba",)
