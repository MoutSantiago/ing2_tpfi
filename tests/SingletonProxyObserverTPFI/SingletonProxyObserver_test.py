"""Tests del punto de entrada del servidor (argparse)."""

from unittest.mock import MagicMock, patch

import pytest

from SingletonProxyObserverTPFI.singletonproxyobserver import (
    DEFAULT_PORT,
    build_server,
    main,
    parse_args,
)

PATCHES = (
    "SingletonProxyObserverTPFI.singletonproxyobserver.Server",
    "SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataProxy",
    "SingletonProxyObserverTPFI.singletonproxyobserver.CorporateLogDAO",
    "SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataDAO",
    "SingletonProxyObserverTPFI.singletonproxyobserver.SubscriptionManager",
)


def apply_dependency_patches(func):
    """Aplica los parches de las dependencias de build_server."""
    for target in reversed(PATCHES):
        func = patch(target)(func)
    return func


# --- parse_args ---


def test_parse_args_defaults():
    """Usa los valores predeterminados cuando no hay argumentos."""
    args = parse_args([])

    assert args.port == DEFAULT_PORT
    assert DEFAULT_PORT == 8080
    assert args.verbose is False


def test_parse_args_accepts_equals_syntax():
    """Acepta argumentos con signo igual."""
    args = parse_args(["-p=9000", "-v"])

    assert args.port == 9000
    assert args.verbose is True


def test_parse_args_accepts_space_syntax():
    """Acepta argumentos separados por espacios."""
    args = parse_args(["--port", "5000"])

    assert args.port == 5000


def test_parse_args_long_and_short_port_are_equivalent():
    """--port y -p producen el mismo resultado."""
    assert (
        parse_args(["--port", "5000"]).port == parse_args(["-p", "5000"]).port
    )


@pytest.mark.parametrize("argv", [["-p", "abc"], ["-x"], ["-p"], ["--port"]])
def test_parse_args_invalid_arguments_exit_with_code_2(argv):
    """Los argumentos inválidos producen el código de argparse 2."""
    with pytest.raises(SystemExit) as exc_info:
        parse_args(argv)

    assert exc_info.value.code == 2


def test_parse_args_help_exits_with_code_0(capsys):
    """--help muestra las flags y termina con código 0."""
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--help"])

    assert exc_info.value.code == 0

    captured = capsys.readouterr()

    assert "--port" in captured.out
    assert "-p" in captured.out
    assert "-v" in captured.out


# --- main ---


@apply_dependency_patches
def test_main_llama_serve_forever_y_usa_puerto_por_defecto(*mocks):
    """main arranca el servidor con el puerto por defecto."""
    server_mock = mocks[-1]
    server_mock.return_value = MagicMock()

    result = main([])

    assert result == 0
    assert server_mock.return_value._port == DEFAULT_PORT
    server_mock.return_value.serve_forever.assert_called_once()


@apply_dependency_patches
def test_main_usa_el_puerto_indicado(*mocks):
    """main pasa el puerto indicado al servidor."""
    server_mock = mocks[-1]
    server_mock.return_value = MagicMock()

    result = main(["-p", "5000"])

    assert result == 0
    assert server_mock.return_value._port == 5000


@apply_dependency_patches
def test_main_con_keyboard_interrupt_detiene_servidor(*mocks):
    """Ante KeyboardInterrupt, main detiene el servidor y retorna 0."""
    server_mock = mocks[-1]
    server_mock.return_value = MagicMock()
    server_mock.return_value.serve_forever.side_effect = KeyboardInterrupt

    result = main([])

    assert result == 0
    server_mock.return_value.stop.assert_called_once()


@apply_dependency_patches
def test_main_con_data_access_error_retorna_codigo_1(*mocks):
    """Ante DataAccessError, main retorna 1 sin propagar la excepción."""
    from SingletonProxyObserverTPFI.app.exceptions import DataAccessError

    data_dao_mock = mocks[1]
    data_dao_mock.get_instance.side_effect = DataAccessError("Error de prueba")

    result = main([])

    assert result == 1


@apply_dependency_patches
def test_main_con_os_error_retorna_codigo_1(*mocks):
    """Ante OSError, main retorna 1 sin propagar la excepción."""
    data_dao_mock = mocks[1]
    data_dao_mock.get_instance.side_effect = OSError("Error de socket")

    result = main([])

    assert result == 1


# --- build_server ---


@apply_dependency_patches
def test_build_server_crea_dependencias_en_orden(*mocks):
    """build_server crea todas las dependencias y retorna un Server."""
    (
        subs_manager_mock,
        data_dao_mock,
        log_dao_mock,
        proxy_mock,
        server_mock,
    ) = mocks

    data_dao_mock.get_instance.return_value = MagicMock()
    log_dao_mock.get_instance.return_value = MagicMock()
    server_mock.return_value = MagicMock()

    result = build_server()

    subs_manager_mock.assert_called_once()
    data_dao_mock.get_instance.assert_called_once()
    log_dao_mock.get_instance.assert_called_once()
    proxy_mock.assert_called_once()
    server_mock.assert_called_once()
    assert result == server_mock.return_value


@apply_dependency_patches
def test_build_server_conecta_proxy_y_publisher(*mocks):
    """build_server conecta el proxy y el publisher al Server."""
    (
        subs_manager_mock,
        data_dao_mock,
        log_dao_mock,
        proxy_mock,
        server_mock,
    ) = mocks

    data_dao_mock.get_instance.return_value = MagicMock()
    log_dao_mock.get_instance.return_value = MagicMock()
    server_mock.return_value = MagicMock()

    build_server()

    call_kwargs = server_mock.call_args[1]
    assert call_kwargs["data"] == proxy_mock.return_value
    assert call_kwargs["publisher"] == subs_manager_mock.return_value
    assert call_kwargs["host"] == "0.0.0.0"
    assert call_kwargs["port"] == 8080
