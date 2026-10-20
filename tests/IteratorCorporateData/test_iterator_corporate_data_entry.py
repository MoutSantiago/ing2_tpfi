"""Tests del punto de entrada de IteratorCorporateData.

Se verifican los argumentos, la configuración del logging, la construcción
de la aplicación, la orquestación del main y la traducción de cada error a
su código de salida.
"""

import json
import logging
import os

import pytest
from botocore.exceptions import ClientError

from IteratorCorporateData import iteratorcorporatedata as entrypoint
from IteratorCorporateData.app.corporate_data_collection import (
    CorporateDataCollection,
)
from IteratorCorporateData.app.exceptions import DataAccessError
from IteratorCorporateData.app.iterator_corporate_data import (
    IteratorCorporateData,
)

RECORDS = [
    {"id": "registro-1", "nombre": "Ana"},
    {"id": "registro-2", "nombre": "Luis"},
    {"id": "registro-3", "nombre": "Carla"},
]


class FakeTable:
    """Tabla falsa sobre una lista de registros en memoria."""

    def __init__(self, records=None, error=None) -> None:
        self._records = list(records or [])
        self._error = error
        self.get_item_calls = []
        self.scan_calls = []

    def scan(self, **kwargs):
        """Devuelve todos los registros en una única página."""
        if self._error is not None:
            raise self._error

        self.scan_calls.append(kwargs)
        return {"Items": list(self._records)}

    def get_item(self, Key):
        """Busca un registro por id o devuelve un resultado vacío."""
        if self._error is not None:
            raise self._error

        self.get_item_calls.append(Key)

        for record in self._records:
            if record.get("id") == Key.get("id"):
                return {"Item": record}

        return {}


def patch_table(monkeypatch, table):
    """Hace que main construya la aplicación con una tabla falsa."""
    original_build_app = entrypoint.build_app

    def fake_build_app(record_id):
        return original_build_app(record_id, table)

    monkeypatch.setattr(entrypoint, "build_app", fake_build_app)


def test_parse_args_defaults():
    """Sin argumentos, no hay id y verbose vale False."""
    args = entrypoint.parse_args([])

    assert args.id is None
    assert args.verbose is False


def test_parse_args_accepts_id_with_space():
    """Acepta --id con el valor separado por un espacio."""
    args = entrypoint.parse_args(["--id", "registro-1"])

    assert args.id == "registro-1"
    assert args.verbose is False


def test_parse_args_accepts_id_with_equals():
    """Acepta --id=valor."""
    args = entrypoint.parse_args(["--id=registro-1"])

    assert args.id == "registro-1"


@pytest.mark.parametrize("flag", ["--v", "-v"])
def test_parse_args_accepts_verbose_flags(flag):
    """Tanto --v como -v activan el modo verbose."""
    args = entrypoint.parse_args([flag])

    assert args.verbose is True


@pytest.mark.parametrize(
    "argv",
    [
        ["--id"],
        ["--id="],
        ["--id", ""],
        ["--id", "   "],
        ["--desconocida"],
        ["--i", "registro-1"],
        ["--ver"],
    ],
)
def test_parse_args_malformed_exits_with_code_2(argv):
    """Los argumentos malformados terminan con el código 2 de argparse."""
    with pytest.raises(SystemExit) as exc_info:
        entrypoint.parse_args(argv)

    assert exc_info.value.code == 2


def test_configure_logging_verbose_sets_levels():
    """Verbose activa DEBUG solo en el paquete propio."""
    entrypoint.configure_logging(True)

    assert logging.getLogger("IteratorCorporateData").level == logging.DEBUG
    assert logging.getLogger().level == logging.WARNING
    assert logging.getLogger("boto3").level == logging.WARNING
    assert logging.getLogger("botocore").level == logging.WARNING
    assert logging.getLogger("urllib3").level == logging.WARNING


def test_configure_logging_without_verbose_uses_warning():
    """Sin verbose, el paquete propio queda en WARNING."""
    entrypoint.configure_logging(False)

    assert logging.getLogger("IteratorCorporateData").level == logging.WARNING
    assert logging.getLogger().level == logging.WARNING


def test_build_app_injects_the_table():
    """Con una tabla ya creada no se consulta AWS y se arma el cliente."""
    table = FakeTable(RECORDS)

    app = entrypoint.build_app("registro-1", table)

    assert isinstance(app, IteratorCorporateData)
    assert isinstance(app._collection, CorporateDataCollection)
    assert app._collection._table is table
    assert app._single_record is True


def test_build_app_without_id_uses_multi_record_mode():
    """Sin id, el cliente arma el resultado como lista."""
    table = FakeTable(RECORDS)

    app = entrypoint.build_app(None, table)

    assert app._single_record is False


def test_build_app_without_region_raises_data_access_error(monkeypatch):
    """Si falta la región de AWS se lanza DataAccessError."""

    class NoRegionSession:
        region_name = None

        def get_credentials(self):
            return object()

    monkeypatch.setattr(entrypoint.boto3.session, "Session", NoRegionSession)

    with pytest.raises(DataAccessError, match="región"):
        entrypoint.build_app(None)


def test_build_app_without_credentials_raises_data_access_error(
    monkeypatch,
):
    """Si faltan las credenciales de AWS se lanza DataAccessError."""

    class NoCredentialsSession:
        region_name = "us-east-1"

        def get_credentials(self):
            return None

    monkeypatch.setattr(
        entrypoint.boto3.session, "Session", NoCredentialsSession
    )

    with pytest.raises(DataAccessError, match="credenciales"):
        entrypoint.build_app(None)


def test_build_app_wraps_resource_creation_error(monkeypatch):
    """Un error de boto3 al crear el recurso pasa a DataAccessError."""

    class FakeSession:
        region_name = "us-east-1"

        def get_credentials(self):
            return object()

    def failing_resource(service):
        raise ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "sin permiso"}},
            "CreateTable",
        )

    monkeypatch.setattr(entrypoint.boto3.session, "Session", FakeSession)
    monkeypatch.setattr(entrypoint.boto3, "resource", failing_resource)

    with pytest.raises(DataAccessError, match="sin permiso") as exc_info:
        entrypoint.build_app(None)

    assert isinstance(exc_info.value.__cause__, ClientError)


def test_build_app_creates_the_real_resource(monkeypatch):
    """Sin tabla inyectada, build_app crea el recurso y la tabla."""
    table = FakeTable(RECORDS)
    created = {}

    class FakeSession:
        region_name = "us-east-1"

        def get_credentials(self):
            return object()

    class FakeResource:
        def Table(self, name):
            created["table_name"] = name
            return table

    monkeypatch.setattr(entrypoint.boto3.session, "Session", FakeSession)
    monkeypatch.setattr(
        entrypoint.boto3, "resource", lambda service: FakeResource()
    )

    app = entrypoint.build_app(None)

    assert isinstance(app, IteratorCorporateData)
    assert isinstance(app._collection, CorporateDataCollection)
    assert app._collection._table is table
    assert created["table_name"] == "CorporateData"


def test_main_full_table_returns_0_and_writes_json_list(monkeypatch, capsys):
    """Sin --id se emite la lista completa y se retorna 0."""
    patch_table(monkeypatch, FakeTable(RECORDS))

    result = entrypoint.main([])

    captured = capsys.readouterr()
    assert result == 0
    assert json.loads(captured.out) == RECORDS
    assert captured.err == ""


def test_main_existing_id_returns_0_and_writes_object(monkeypatch, capsys):
    """Con un --id existente se emite el registro como objeto."""
    patch_table(monkeypatch, FakeTable(RECORDS))

    result = entrypoint.main(["--id", "registro-2"])

    captured = capsys.readouterr()
    assert result == 0
    assert json.loads(captured.out) == RECORDS[1]
    assert not isinstance(json.loads(captured.out), list)


def test_main_empty_table_returns_0_and_writes_id_none(monkeypatch, capsys):
    """Con la tabla vacía se emite {"id": null} y se retorna 0."""
    patch_table(monkeypatch, FakeTable([]))

    result = entrypoint.main([])

    captured = capsys.readouterr()
    assert result == 0
    assert json.loads(captured.out) == {"id": None}


def test_main_nonexistent_id_returns_1_without_traceback(monkeypatch, capsys):
    """Un --id inexistente retorna 1 con un mensaje claro."""
    patch_table(monkeypatch, FakeTable(RECORDS))

    result = entrypoint.main(["--id", "no-existe"])

    captured = capsys.readouterr()
    assert result == 1
    assert "no-existe" in captured.err
    assert "Traceback" not in captured.err


def test_main_data_access_failure_returns_1(monkeypatch, capsys):
    """Un fallo de acceso a DynamoDB retorna 1 con la causa."""
    error = ClientError(
        {"Error": {"Code": "InternalError", "Message": "fallo simulado"}},
        "Scan",
    )
    patch_table(monkeypatch, FakeTable(RECORDS, error=error))

    result = entrypoint.main([])

    captured = capsys.readouterr()
    assert result == 1
    assert "Error de acceso a datos" in captured.err
    assert "fallo simulado" in captured.err
    assert "Traceback" not in captured.err


def test_main_os_error_returns_1(monkeypatch, capsys):
    """Un error al escribir el resultado retorna 1."""

    class FailingWriter:
        @staticmethod
        def write(result):
            raise OSError("no se pudo escribir")

    patch_table(monkeypatch, FakeTable(RECORDS))
    monkeypatch.setattr(entrypoint, "JsonWrite", FailingWriter)

    result = entrypoint.main([])

    captured = capsys.readouterr()
    assert result == 1
    assert "No se pudo escribir el resultado" in captured.err
    assert "no se pudo escribir" in captured.err


def test_main_keyboard_interrupt_returns_1(monkeypatch, capsys):
    """La cancelación manual retorna 1."""

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(entrypoint, "build_app", interrupt)

    result = entrypoint.main([])

    captured = capsys.readouterr()
    assert result == 1
    assert "Cancelado" in captured.err


def test_main_unexpected_exception_returns_1(monkeypatch, capsys):
    """Cualquier otra excepción se informa con su detalle y retorna 1."""

    def fail(*args, **kwargs):
        raise RuntimeError("fallo inesperado")

    monkeypatch.setattr(entrypoint, "build_app", fail)

    result = entrypoint.main([])

    captured = capsys.readouterr()
    assert result == 1
    assert "fallo inesperado" in captured.err
    assert "Traceback" not in captured.err


def test_main_verbose_emits_debug_on_stdout(monkeypatch, capsys):
    """Con --v los mensajes DEBUG salen por salida estándar."""
    patch_table(monkeypatch, FakeTable(RECORDS))

    result = entrypoint.main(["--v"])

    captured = capsys.readouterr()
    assert result == 0
    assert "Construyendo la aplicación" in captured.out

    json_start = captured.out.index("[\n")
    assert json.loads(captured.out[json_start:]) == RECORDS


def test_main_without_verbose_output_is_only_json(monkeypatch, capsys):
    """Sin --v la salida estándar contiene únicamente el JSON."""
    patch_table(monkeypatch, FakeTable(RECORDS))

    result = entrypoint.main([])

    captured = capsys.readouterr()
    assert result == 0
    assert "DEBUG" not in captured.out
    assert json.loads(captured.out) == RECORDS


@pytest.mark.skipif(
    os.environ.get("IS2_AWS_ACCEPTANCE") != "1",
    reason="Requiere credenciales y la tabla real CorporateData de AWS.",
)
def test_acceptance_against_real_table(capsys):
    """Prueba de aceptación completa, por id y con id inexistente."""
    assert entrypoint.main([]) == 0
    full_output = json.loads(capsys.readouterr().out)
    assert isinstance(full_output, list)

    if full_output:
        record_id = full_output[0]["id"]
        assert entrypoint.main(["--id", record_id]) == 0
        single_output = json.loads(capsys.readouterr().out)
        assert single_output["id"] == record_id

    assert entrypoint.main(["--id", "id-inexistente-de-aceptacion"]) == 1
    assert "id-inexistente-de-aceptacion" in capsys.readouterr().err
