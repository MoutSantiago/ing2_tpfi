import logging

import pytest

from ObserverClient import observerclient as entrypoint


def test_parse_args_defaults():
    """Usa los valores predeterminados cuando no hay argumentos."""
    args = entrypoint.parse_args([])

    assert args.host == "localhost"
    assert args.port == 8080
    assert args.output is None
    assert args.verbose is False


def test_parse_args_accepts_equals_syntax():
    """Acepta argumentos con signo igual."""
    args = entrypoint.parse_args(
        ["-s=servidor", "-p=9000", "-o=salida.json", "-v"]
    )

    assert args.host == "servidor"
    assert args.port == 9000
    assert args.output == "salida.json"
    assert args.verbose is True


def test_parse_args_accepts_space_syntax():
    """Acepta argumentos separados por espacios."""
    args = entrypoint.parse_args(["-s", "servidor", "-p", "9000"])

    assert args.host == "servidor"
    assert args.port == 9000


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

    assert logging.getLogger("ObserverClient").level == logging.DEBUG
    assert logging.getLogger("botocore").level == logging.WARNING
    assert logging.getLogger("boto3").level == logging.WARNING
    assert logging.getLogger("urllib3").level == logging.WARNING
    assert logging.getLogger().level == logging.WARNING


def test_configure_logging_without_verbose_uses_warning():
    """Sin verbose, el paquete propio queda en WARNING."""
    entrypoint.configure_logging(False)

    assert logging.getLogger("ObserverClient").level == logging.WARNING
    assert logging.getLogger().level == logging.WARNING


def test_main_keyboard_interrupt_stops_client(monkeypatch):
    """Ctrl+C detiene el cliente y retorna código 0."""

    class FakeClient:
        def __init__(self):
            self.stop_called = False

        def run(self):
            raise KeyboardInterrupt

        def stop(self):
            self.stop_called = True

    fake_client = FakeClient()

    monkeypatch.setattr(
        entrypoint,
        "build_client",
        lambda **kwargs: fake_client,
    )

    result = entrypoint.main([])

    assert result == 0
    assert fake_client.stop_called is True


def test_main_invalid_output_returns_1_without_traceback(tmp_path, capsys):
    """Un archivo de salida inválido devuelve 1 sin traceback."""
    invalid_output = tmp_path / "no_existe" / "salida.json"

    result = entrypoint.main(["-o", str(invalid_output)])

    captured = capsys.readouterr()

    assert result == 1
    assert "Error de entrada/salida" in captured.out
    assert "Traceback" not in captured.out
    assert "Traceback" not in captured.err


def test_main_unexpected_exception_returns_1_without_traceback(
    monkeypatch, capsys
):
    """Una excepción inesperada devuelve 1 sin traceback."""

    def failing_build_client(**kwargs):
        raise RuntimeError("fallo de prueba")

    monkeypatch.setattr(
        entrypoint,
        "build_client",
        failing_build_client,
    )

    result = entrypoint.main([])

    captured = capsys.readouterr()

    assert result == 1
    assert "fallo de prueba" in captured.out
    assert "Traceback" not in captured.out
    assert "Traceback" not in captured.err


def test_build_client_creates_dependencies(monkeypatch):
    """Construye la conexión, el escritor y el cliente con sus parámetros."""
    created = {}

    class FakeConnection:
        def __init__(self, host, port):
            created["connection"] = (host, port)

    class FakeWriter:
        def __init__(self, output):
            created["writer"] = output

    class FakeClient:
        def __init__(
            self,
            host,
            port,
            connection,
            writer,
            retry_interval,
        ):
            created["client"] = (
                host,
                port,
                connection,
                writer,
                retry_interval,
            )

    monkeypatch.setattr(entrypoint, "ServerConnection", FakeConnection)
    monkeypatch.setattr(entrypoint, "NotificationWriter", FakeWriter)
    monkeypatch.setattr(entrypoint, "ObserverClient", FakeClient)

    client = entrypoint.build_client(
        "servidor",
        9000,
        "salida.json",
        retry_interval=1,
    )

    assert isinstance(client, FakeClient)
    assert created["connection"] == ("servidor", 9000)
    assert created["writer"] == "salida.json"
    assert created["client"][0:2] == ("servidor", 9000)
    assert created["client"][4] == 1
