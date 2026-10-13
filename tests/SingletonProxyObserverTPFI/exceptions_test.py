import pytest

from SingletonProxyObserverTPFI.app.exceptions import (
    DataAccessError,
    ObserverUnavailableError,
    RecordNotFoundError,
)

# =============================================================================
# Tests de la jerarquía de excepciones
# =============================================================================


def test_record_not_found_hereda_de_data_access_error():
    """Verifica que RecordNotFoundError sea una DataAccessError, para que un
    except DataAccessError la capture."""
    assert issubclass(RecordNotFoundError, DataAccessError)


def test_observer_unavailable_no_hereda_de_data_access_error():
    """Verifica que ObserverUnavailableError NO herede de DataAccessError,
    porque no es un error de base de datos."""
    assert not issubclass(ObserverUnavailableError, DataAccessError)


def test_observer_unavailable_hereda_de_exception():
    """Verifica que ObserverUnavailableError sea una Exception normal."""
    assert issubclass(ObserverUnavailableError, Exception)


def test_data_access_error_hereda_de_exception():
    """Verifica que DataAccessError sea una Exception normal."""
    assert issubclass(DataAccessError, Exception)


def test_data_access_error_es_la_base_comun():
    """Verifica que las dos excepciones de datos compartan la misma clase
    base y que ObserverUnavailableError quede por fuera de esa jerarquía."""
    assert RecordNotFoundError.__bases__ == (DataAccessError,)
    assert DataAccessError.__bases__ == (Exception,)
    assert ObserverUnavailableError.__bases__ == (Exception,)


# =============================================================================
# Tests de captura
# =============================================================================


def test_except_data_access_error_captura_record_not_found():
    """Verifica que un except DataAccessError capture a
    RecordNotFoundError."""
    capturado = None
    try:
        raise RecordNotFoundError("no existe el registro X")
    except DataAccessError as e:
        capturado = e

    assert isinstance(capturado, RecordNotFoundError)
    assert capturado is not None
    assert "no existe el registro X" in str(capturado)


def test_except_data_access_error_no_captura_observer_unavailable():
    """Verifica que un except DataAccessError NO capture a
    ObserverUnavailableError."""
    with pytest.raises(ObserverUnavailableError):
        try:
            raise ObserverUnavailableError("socket cerrado")
        except DataAccessError:  # pragma: no cover
            pytest.fail("ObserverUnavailableError no debe ser DataAccessError")


def test_observer_unavailable_se_captura_con_exception():
    """Verifica que ObserverUnavailableError se capture con un except
    Exception genérico."""
    with pytest.raises(Exception) as exc_info:
        raise ObserverUnavailableError("socket cerrado")

    assert "socket cerrado" in str(exc_info.value)


# =============================================================================
# Tests del mensaje y del encadenamiento de causas
# =============================================================================


@pytest.mark.parametrize(
    "excepcion",
    [DataAccessError, RecordNotFoundError, ObserverUnavailableError],
)
def test_excepciones_aceptan_mensaje(excepcion):
    """Verifica que cada excepción acepte y conserve un mensaje
    descriptivo, que el Server puede incluir en la respuesta de error."""
    error = excepcion("mensaje descriptivo")

    assert str(error) == "mensaje descriptivo"


@pytest.mark.parametrize(
    "excepcion",
    [DataAccessError, RecordNotFoundError, ObserverUnavailableError],
)
def test_excepciones_pueden_instantanciarse_sin_mensaje(excepcion):
    """Verifica que las excepciones puedan crearse sin argumentos."""
    assert isinstance(excepcion(), excepcion)


def test_encadenamiento_conserva_error_original():
    """Verifica que al relanzar con `raise ... from error` la causa original
    quede en __cause__ y no se pierda el detalle del error de boto3."""
    original = ValueError("fallo original de boto3")

    try:
        try:
            raise original
        except ValueError as error:
            raise DataAccessError("Error en la base") from error
    except DataAccessError as error:
        assert error.__cause__ is original
        assert str(error.__cause__) == "fallo original de boto3"


def test_record_not_found_conserva_causa():
    """Verifica que RecordNotFoundError también encadene su causa."""
    original = KeyError("UADER-FCyT-IS2")

    with pytest.raises(RecordNotFoundError) as exc_info:
        try:
            raise original
        except KeyError as error:
            raise RecordNotFoundError("registro inexistente") from error

    assert exc_info.value.__cause__ is original
    assert isinstance(exc_info.value, DataAccessError)


def test_causa_inexistente_sin_from():
    """Verifica que si no se usa `from`, __cause__ queda en None."""
    with pytest.raises(DataAccessError) as exc_info:
        raise DataAccessError("sin causa")

    assert exc_info.value.__cause__ is None
