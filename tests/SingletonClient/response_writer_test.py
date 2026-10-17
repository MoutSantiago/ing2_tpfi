"""Pruebas de ResponseWriter del SingletonClient."""

import json

import pytest

from SingletonClient.app.response_writer import INDENT, ResponseWriter


def pretty(message):
    """JSON multilínea esperado para una respuesta."""
    return json.dumps(message, ensure_ascii=False, indent=INDENT)


class TestResponseWriterWithoutPath:
    """Pruebas cuando no se especifica ruta de salida."""

    def test_write_without_output_path_prints_json_to_stdout(
        self, tmp_path, monkeypatch, capsys
    ):
        """Sin ruta, write imprime la respuesta por salida estándar y no crea
        archivos."""
        monkeypatch.chdir(tmp_path)

        writer = ResponseWriter(None)
        response = {"resultado": "éxito", "valor": 42}

        writer.write(response)

        captured = capsys.readouterr()

        assert captured.out == pretty(response) + "\n"
        assert captured.err == ""
        assert list(tmp_path.iterdir()) == []

    def test_write_serializes_dict_correctly(self, capsys):
        """Un diccionario se serializa correctamente."""
        writer = ResponseWriter(None)
        response = {"clave": "valor", "número": 123}

        writer.write(response)

        captured = capsys.readouterr()
        result = captured.out

        assert result == pretty(response) + "\n"
        assert json.loads(result) == response

    def test_write_serializes_list_correctly(self, capsys):
        """Una lista se serializa correctamente."""
        writer = ResponseWriter(None)
        response = [1, 2, 3, "texto"]

        writer.write(response)

        captured = capsys.readouterr()
        result = captured.out

        assert result == pretty(response) + "\n"
        assert json.loads(result) == response

    def test_write_serializes_text_correctly(self, capsys):
        """Un texto se serializa correctamente."""
        writer = ResponseWriter(None)
        response = "respuesta del servidor"

        writer.write(response)

        captured = capsys.readouterr()
        result = captured.out

        assert result == pretty(response) + "\n"
        assert json.loads(result) == response


class TestResponseWriterWithPath:
    """Pruebas cuando se especifica ruta de salida."""

    def test_write_with_output_path_writes_file_and_prints_nothing(
        self, tmp_path, capsys
    ):
        """Con ruta, escribe el archivo y no imprime nada."""
        output_file = tmp_path / "response.json"
        writer = ResponseWriter(str(output_file))
        response = {"mensaje": "respuesta"}

        writer.write(response)

        captured = capsys.readouterr()
        content = output_file.read_text(encoding="utf-8")

        assert captured.out == ""
        assert captured.err == ""
        assert json.loads(content) == response

    def test_second_write_replaces_content(self, tmp_path, capsys):
        """Una segunda llamada a write reemplaza el contenido anterior."""
        output_file = tmp_path / "response.json"
        writer = ResponseWriter(str(output_file))

        writer.write({"primero": "contenido"})
        capsys.readouterr()

        writer.write({"segundo": "nuevo contenido"})
        capsys.readouterr()

        content = output_file.read_text(encoding="utf-8")
        assert json.loads(content) == {"segundo": "nuevo contenido"}

    def test_write_serializes_dict_and_can_reload(self, tmp_path, capsys):
        """Un diccionario se guarda y se puede leer con json.load."""
        output_file = tmp_path / "response.json"
        writer = ResponseWriter(str(output_file))
        response = {"id": 1, "datos": "test"}

        writer.write(response)
        capsys.readouterr()

        content = output_file.read_text(encoding="utf-8")
        loaded = json.loads(content)
        assert loaded == response
        assert isinstance(loaded, dict)

    def test_write_serializes_list_and_can_reload(self, tmp_path, capsys):
        """Una lista se guarda y se puede leer con json.load."""
        output_file = tmp_path / "response.json"
        writer = ResponseWriter(str(output_file))
        response = [{"id": 1}, {"id": 2}]

        writer.write(response)
        capsys.readouterr()

        content = output_file.read_text(encoding="utf-8")
        loaded = json.loads(content)
        assert loaded == response
        assert isinstance(loaded, list)

    def test_write_serializes_text_and_can_reload(self, tmp_path, capsys):
        """Un texto se guarda y se puede leer con json.load."""
        output_file = tmp_path / "response.json"
        writer = ResponseWriter(str(output_file))
        response = "texto plano"

        writer.write(response)
        capsys.readouterr()

        content = output_file.read_text(encoding="utf-8")
        loaded = json.loads(content)
        assert loaded == response

    def test_accents_preserved_without_u_escape(self, tmp_path, capsys):
        """Los caracteres con tilde se escriben tal cual, sin \u00f3."""
        output_file = tmp_path / "response.json"
        writer = ResponseWriter(str(output_file))
        response = {
            "ciudad": "Concepción del Uruguay",
            "mensaje": "Notificación recibida",
            "producto": "Botines de fútbol",
        }

        writer.write(response)
        capsys.readouterr()

        content = output_file.read_text(encoding="utf-8")
        assert "Concepción del Uruguay" in content
        assert "Notificación recibida" in content
        assert "fútbol" in content
        assert "\\u00f3" not in content
        assert "\\u00fa" not in content
        assert json.loads(content) == response


class TestResponseWriterInit:
    """Pruebas de inicialización."""

    def test_init_with_nonexistent_directory_raises_oserror(self, tmp_path):
        """Un directorio inexistente en la ruta lanza OSError en el
        constructor, sin dejar archivos creados."""
        invalid_path = tmp_path / "directorio_inexistente" / "response.json"

        with pytest.raises(OSError):
            ResponseWriter(str(invalid_path))

        assert not invalid_path.exists()
        assert not (tmp_path / "directorio_inexistente").exists()

    def test_init_with_valid_directory_does_not_create_file(self, tmp_path):
        """La inicialización con ruta válida no crea ni vacía el archivo."""
        output_file = tmp_path / "response.json"
        writer = ResponseWriter(str(output_file))

        assert writer is not None
        assert not output_file.exists()
