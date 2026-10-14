"""Pruebas de RequestLoader del SingletonClient."""

import json

import pytest

from SingletonClient.app.exceptions import InvalidRequestError
from SingletonClient.app.request_loader import RequestLoader

CPU_UUID = "cpu-test-uuid"


@pytest.fixture
def loader():
    """Loader con un UUID fijo para poder verificarlo."""
    return RequestLoader(CPU_UUID)


@pytest.fixture
def write_file(tmp_path):
    """Escribe contenido (dict o texto crudo) a un archivo temporal."""

    def _write(content):
        file_path = tmp_path / "input.json"
        if isinstance(content, dict):
            file_path.write_text(
                json.dumps(content, ensure_ascii=False), encoding="utf-8"
            )
        else:
            file_path.write_text(content, encoding="utf-8")
        return str(file_path)

    return _write


class TestValidRequests:
    """Un archivo válido de cada acción devuelve la petición esperada."""

    def test_get_request(self, loader, write_file):
        path = write_file({"ACTION": "get", "ID": "req-1"})

        request = loader.load(path)

        assert request == {
            "UUID": CPU_UUID,
            "ACTION": "get",
            "ID": "req-1",
        }

    def test_set_request_includes_tuple_fields(self, loader, write_file):
        path = write_file(
            {
                "ACTION": "set",
                "ID": "req-1",
                "domicilio": "Calle Falsa 123",
                "web": "https://ejemplo.com",
            }
        )

        request = loader.load(path)

        assert request == {
            "UUID": CPU_UUID,
            "ACTION": "set",
            "ID": "req-1",
            "domicilio": "Calle Falsa 123",
            "web": "https://ejemplo.com",
        }

    def test_list_request(self, loader, write_file):
        path = write_file({"ACTION": "list"})

        request = loader.load(path)

        assert request == {"UUID": CPU_UUID, "ACTION": "list"}

    def test_accepts_lowercase_id_when_it_matches(self, loader, write_file):
        path = write_file(
            {"ACTION": "set", "ID": "req-1", "id": "req-1", "cp": "3100"}
        )

        request = loader.load(path)

        assert request["ID"] == "req-1"


class TestUuid:
    """El UUID de la petición es siempre el recibido por constructor."""

    def test_uuid_from_file_is_discarded(self, loader, write_file):
        path = write_file(
            {"ACTION": "get", "ID": "req-1", "UUID": "otro-uuid"}
        )

        request = loader.load(path)

        assert request["UUID"] == CPU_UUID

    def test_different_loader_uuid(self, write_file):
        other_loader = RequestLoader("otra-cpu")
        path = write_file({"ACTION": "list"})

        assert other_loader.load(path)["UUID"] == "otra-cpu"


class TestFileErrors:
    """Errores de lectura y formato del archivo."""

    def test_missing_file_raises_oserror(self, loader, tmp_path):
        with pytest.raises(OSError):
            loader.load(str(tmp_path / "no_existe.json"))

    def test_invalid_json_raises_invalid_request_error(
        self, loader, write_file
    ):
        path = write_file("esto no es json{")

        with pytest.raises(InvalidRequestError, match="JSON"):
            loader.load(path)

    @pytest.mark.parametrize("content", ["[1, 2]", '"texto"', "42", "null"])
    def test_json_non_object_raises_invalid_request_error(
        self, loader, write_file, content
    ):
        path = write_file(content)

        with pytest.raises(InvalidRequestError, match="objeto"):
            loader.load(path)


class TestValidation:
    """Datos mínimos según la acción."""

    def test_missing_action(self, loader, write_file):
        path = write_file({"ID": "req-1"})

        with pytest.raises(InvalidRequestError, match="ACTION"):
            loader.load(path)

    def test_unknown_action(self, loader, write_file):
        path = write_file({"ACTION": "delete", "ID": "req-1"})

        with pytest.raises(InvalidRequestError, match="delete"):
            loader.load(path)

    def test_subscribe_action_is_rejected(self, loader, write_file):
        path = write_file({"ACTION": "subscribe", "ID": "req-1"})

        with pytest.raises(InvalidRequestError, match="subscribe"):
            loader.load(path)

    def test_get_without_id(self, loader, write_file):
        path = write_file({"ACTION": "get"})

        with pytest.raises(InvalidRequestError, match="ID"):
            loader.load(path)

    def test_get_with_empty_id(self, loader, write_file):
        path = write_file({"ACTION": "get", "ID": ""})

        with pytest.raises(InvalidRequestError, match="ID"):
            loader.load(path)

    def test_set_without_id(self, loader, write_file):
        path = write_file({"ACTION": "set", "cp": "3100"})

        with pytest.raises(InvalidRequestError, match="ID"):
            loader.load(path)

    def test_set_without_tuple_fields(self, loader, write_file):
        path = write_file({"ACTION": "set", "ID": "req-1"})

        with pytest.raises(InvalidRequestError, match="campo"):
            loader.load(path)

    def test_set_with_unknown_field(self, loader, write_file):
        path = write_file(
            {"ACTION": "set", "ID": "req-1", "direccion": "Calle 1"}
        )

        with pytest.raises(InvalidRequestError, match="direccion"):
            loader.load(path)

    def test_set_with_mismatched_lowercase_id(self, loader, write_file):
        path = write_file(
            {"ACTION": "set", "ID": "req-1", "id": "otro", "cp": "3100"}
        )

        with pytest.raises(InvalidRequestError, match="id"):
            loader.load(path)

    def test_list_with_id(self, loader, write_file):
        path = write_file({"ACTION": "list", "ID": "req-1"})

        with pytest.raises(InvalidRequestError, match="ID"):
            loader.load(path)


class TestEncoding:
    """Los caracteres con tilde del archivo se conservan en la petición."""

    def test_accents_are_preserved(self, loader, write_file):
        path = write_file(
            {
                "ACTION": "set",
                "ID": "req-1",
                "localidad": "Corrientes",
                "domicilio": "Av. Ramírez 742, piso 3°",
            }
        )

        request = loader.load(path)

        assert request["domicilio"] == "Av. Ramírez 742, piso 3°"
