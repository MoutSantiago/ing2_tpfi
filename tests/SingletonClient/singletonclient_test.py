"""Tests para el punto de entrada de SingletonClient."""

import logging

import pytest

from SingletonClient import singletonclient as entrypoint


def test_parse_args_defaults():
    """Usa los valores predeterminados cuando solo se indica -i."""
    args = entrypoint.parse_args(["-i", "input.json"])

    assert args.input_path == "input.json"
    assert args.host == "localhost"
    assert args.port == 8080
    assert args.output_path is None
    assert args.verbose is False


def test_parse_args_accepts_equals_syntax():
    """Acepta argumentos con signo igual."""
    args = entrypoint.parse_args(
        ["-i=in.json", "-o=out.json", "-s=host", "-p=9000", "-v"]
    )

    assert args.input_path == "in.json"
    assert args.output_path == "out.json"
    assert args.host == "host"
    assert args.port == 9000
    assert args.verbose is True


def test_parse_args_accepts_space_syntax():
    """Acepta argumentos separados por espacios."""
    args = entrypoint.parse_args(
        ["-i", "in.json", "-o", "out.json", "-s", "host", "-p", "9000", "-v"]
    )

    assert args.input_path == "in.json"
    assert args.output_path == "out.json"
    assert args.host == "host"
    assert args.port == 9000
    assert args.verbose is True


@pytest.mark.parametrize(
    "argv",
    [
        ["-p", "abc"],
        ["-p", "0"],
        ["-p", "65536"],
        ["-x"],
        ["-s"],
        ["-p"],
        ["-o"],
        [],
    ],
)
def test_parse_args_invalid_arguments_exit_with_code_2(argv):
    """Los argumentos inválidos producen el código de argparse 2."""
    with pytest.raises(SystemExit) as exc_info:
        entrypoint.parse_args(argv)

    assert exc_info.value.code == 2


def test_configure_logging_verbose_sets_levels():
    """Verbose activa DEBUG en el paquete propio, no en las librerías."""
    entrypoint.configure_logging(True)

    assert logging.getLogger("SingletonClient").level == logging.DEBUG
    assert logging.getLogger("botocore").level == logging.WARNING
    assert logging.getLogger("boto3").level == logging.WARNING
    assert logging.getLogger("urllib3").level == logging.WARNING
    assert logging.getLogger().level == logging.WARNING


def test_configure_logging_without_verbose_uses_warning():
    """Sin verbose, el paquete propio queda en WARNING."""
    entrypoint.configure_logging(False)

    assert logging.getLogger("SingletonClient").level == logging.WARNING
    assert logging.getLogger().level == logging.WARNING

def test_main_success_returns_0(monkeypatch):
    """main retorna 0 cuando el cliente responde correctamente."""
    class FakeClient:
        def execute(self, input_path):
            assert input_path == "input.json"
            return {"STATUS": "OK"}

    def fake_build_client(host, port, output, read_timeout=None):
        assert host == "localhost"
        assert port == 8080
        assert output is None
        return FakeClient()

    monkeypatch.setattr(entrypoint, "build_client", fake_build_client)

    result = entrypoint.main(["-i", "input.json"])
    assert result == 0


def test_main_server_error_response_returns_1(monkeypatch, capsys):
    """Si la respuesta es "Error", main retorna 1."""
    class FakeClient:
        def execute(self, input_path):
            return "Error"

    monkeypatch.setattr(
        entrypoint, "build_client", lambda *args, **kwargs: FakeClient()
    )

    result = entrypoint.main(["-i", "input.json"])
    assert result == 1


def test_main_server_error_dict_returns_1(monkeypatch):
    """Si la respuesta es dict con STATUS Error, main retorna 1."""
    class FakeClient:
        def execute(self, input_path):
            return {"STATUS": "Error"}

    monkeypatch.setattr(
        entrypoint, "build_client", lambda *args, **kwargs: FakeClient()
    )

    result = entrypoint.main(["-i", "input.json"])
    assert result == 1


def test_main_invalid_request_returns_1(monkeypatch, capsys):
    """InvalidRequestError retorna 1 sin traceback."""
    from SingletonClient.app.exceptions import InvalidRequestError

    def failing_build_client(*args, **kwargs):
        raise InvalidRequestError("archivo inválido")

    monkeypatch.setattr(entrypoint, "build_client", failing_build_client)

    result = entrypoint.main(["-i", "input.json"])
    captured = capsys.readouterr()

    assert result == 1
    assert "archivo inválido" in captured.out
    assert "Traceback" not in captured.out


def test_main_connection_lost_returns_1(monkeypatch, capsys):
    """ConnectionLostError retorna 1."""
    from SingletonClient.app.exceptions import ConnectionLostError

    def failing_build_client(*args, **kwargs):
        raise ConnectionLostError("servidor caído")

    monkeypatch.setattr(entrypoint, "build_client", failing_build_client)

    result = entrypoint.main(["-i", "input.json"])
    captured = capsys.readouterr()

    assert result == 1
    assert "servidor caído" in captured.out


def test_main_value_error_returns_1(monkeypatch, capsys):
    """ValueError (respuesta ilegible) retorna 1."""
    def failing_build_client(*args, **kwargs):
        raise ValueError("respuesta no es JSON válido")

    monkeypatch.setattr(entrypoint, "build_client", failing_build_client)

    result = entrypoint.main(["-i", "input.json"])
    captured = capsys.readouterr()

    assert result == 1
    assert "respuesta no es JSON válido" in captured.out


def test_main_os_error_returns_1(monkeypatch, capsys):
    """OSError retorna 1."""
    def failing_build_client(*args, **kwargs):
        raise OSError("archivo no escribible")

    monkeypatch.setattr(entrypoint, "build_client", failing_build_client)

    result = entrypoint.main(["-i", "input.json"])
    captured = capsys.readouterr()

    assert result == 1
    assert "archivo no escribible" in captured.out


def test_main_keyboard_interrupt_returns_1(monkeypatch):
    """KeyboardInterrupt retorna 1."""
    def failing_build_client(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(entrypoint, "build_client", failing_build_client)

    result = entrypoint.main(["-i", "input.json"])
    assert result == 1


def test_main_unexpected_exception_returns_1(monkeypatch, capsys):
    """Excepción inesperada retorna 1."""
    def failing_build_client(*args, **kwargs):
        raise RuntimeError("fallo inesperado")

    monkeypatch.setattr(entrypoint, "build_client", failing_build_client)

    result = entrypoint.main(["-i", "input.json"])
    captured = capsys.readouterr()

    assert result == 1
    assert "fallo inesperado" in captured.out


def test_build_client_creates_dependencies(monkeypatch):
    """build_client crea todas las dependencias."""
    created = {}

    class FakeLoader:
        def __init__(self, uuid_str):
            created["loader"] = uuid_str

    class FakeConn:
        def __init__(self, host, port, read_timeout):
            created["conn"] = (host, port, read_timeout)

    class FakeWriter:
        def __init__(self, output):
            created["writer"] = output

    class FakeClient:
        def __init__(self, loader, connection, writer):
            created["client"] = (loader, connection, writer)

    monkeypatch.setattr(entrypoint, "RequestLoader", FakeLoader)
    monkeypatch.setattr(entrypoint, "ServerConnection", FakeConn)
    monkeypatch.setattr(entrypoint, "ResponseWriter", FakeWriter)
    monkeypatch.setattr(entrypoint, "SingletonClient", FakeClient)
    monkeypatch.setattr(entrypoint.uuid, "getnode", lambda: 12345)

    client = entrypoint.build_client("h", 9000, "out.json", read_timeout=5)

    assert isinstance(client, FakeClient)
    assert created["loader"] == "12345"
    assert created["conn"] == ("h", 9000, 5)
    assert created["writer"] == "out.json"
