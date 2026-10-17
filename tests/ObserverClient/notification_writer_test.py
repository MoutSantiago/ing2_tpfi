import json

import pytest

from ObserverClient.app.notification_writer import INDENT, NotificationWriter


def pretty(message):
    """JSON multilínea esperado para una notificación."""
    return json.dumps(message, ensure_ascii=False, indent=INDENT)


def test_write_without_output_path_prints_json_to_stdout(
    tmp_path, monkeypatch, capsys
):
    """Imprime la notificación multilínea por stdout sin crear archivos."""
    monkeypatch.chdir(tmp_path)

    writer = NotificationWriter(None)
    message = {"evento": "actualización", "mensaje": "Producto actualizado"}

    writer.write(message)

    captured = capsys.readouterr()

    assert captured.out == pretty(message) + "\n"
    assert "\n" in pretty(message)
    assert captured.err == ""
    assert list(tmp_path.iterdir()) == []


def test_write_prints_multiline_json(tmp_path, capsys):
    """La notificación mostrada ocupa más de una línea."""
    writer = NotificationWriter(None)
    message = {"evento": "creado", "id": 1, "detalle": "un registro"}

    writer.write(message)

    captured = capsys.readouterr()
    lines = captured.out.splitlines()

    assert len(lines) > 1
    assert lines[0] == "{"


def test_show_prints_without_touching_output_file(tmp_path, capsys):
    """show imprime el JSON pero no guarda nada en el archivo."""
    output_file = tmp_path / "notifications.json"
    writer = NotificationWriter(str(output_file))
    message = {"UUID": "u", "ACTION": "ok"}

    writer.show(message)

    captured = capsys.readouterr()

    assert captured.out == pretty(message) + "\n"
    assert captured.err == ""
    assert output_file.read_text(encoding="utf-8") == ""


def test_show_without_output_path_prints_only(tmp_path, monkeypatch, capsys):
    """show sin archivo de salida solo imprime por stdout."""
    monkeypatch.chdir(tmp_path)

    writer = NotificationWriter(None)
    message = {"UUID": "u", "ACTION": "ok"}

    writer.show(message)

    captured = capsys.readouterr()

    assert captured.out == pretty(message) + "\n"
    assert list(tmp_path.iterdir()) == []


def test_write_with_output_path_prints_and_saves_notification(
    tmp_path, capsys
):
    """Imprime la notificación y la guarda en el archivo configurado."""
    output_file = tmp_path / "notifications.json"
    writer = NotificationWriter(str(output_file))
    message = {"evento": "actualización", "producto": "Zapatillas"}

    writer.write(message)

    captured = capsys.readouterr()
    content = output_file.read_text(encoding="utf-8")

    assert captured.out == pretty(message) + "\n"
    assert captured.err == ""
    assert json.loads(content) == [message]


def test_output_file_is_a_json_array(tmp_path, capsys):
    """El archivo guarda las notificaciones dentro de un array JSON."""
    output_file = tmp_path / "notifications.json"
    writer = NotificationWriter(str(output_file))

    writer.write({"evento": "creado", "id": 1})
    capsys.readouterr()

    content = output_file.read_text(encoding="utf-8")

    assert content.lstrip().startswith("[")
    assert content.rstrip().endswith("]")
    assert isinstance(json.loads(content), list)


def test_write_appends_multiple_notifications(tmp_path, capsys):
    """Agrega notificaciones al array sin sobrescribir las anteriores."""
    output_file = tmp_path / "notifications.json"
    writer = NotificationWriter(str(output_file))

    first_message = {"evento": "creado", "id": 1}
    second_message = {"evento": "actualizado", "id": 2}

    writer.write(first_message)
    writer.write(second_message)

    capsys.readouterr()
    content = output_file.read_text(encoding="utf-8")

    assert json.loads(content) == [first_message, second_message]


def test_write_preserves_accents_in_utf8_file(tmp_path, capsys):
    """Guarda caracteres acentuados sin convertirlos en secuencias Unicode."""
    output_file = tmp_path / "notifications.json"
    writer = NotificationWriter(str(output_file))
    message = {
        "mensaje": "Notificación recibida",
        "producto": "Botines de fútbol",
    }

    writer.write(message)
    capsys.readouterr()

    content = output_file.read_text(encoding="utf-8")

    assert "Notificación recibida" in content
    assert "fútbol" in content
    assert "\\u00f3" not in content
    assert json.loads(content) == [message]


def test_init_with_invalid_output_path_raises_oserror(tmp_path):
    """Propaga OSError cuando no se puede abrir la ruta de salida."""
    invalid_path = tmp_path / "directorio_inexistente" / "notifications.json"

    with pytest.raises(OSError):
        NotificationWriter(str(invalid_path))


def test_write_on_empty_file_creates_array(tmp_path, capsys):
    """Un archivo vacío se interpreta como un array vacío."""
    output_file = tmp_path / "notifications.json"
    output_file.touch()
    writer = NotificationWriter(str(output_file))

    writer.write({"evento": "creado", "id": 1})
    capsys.readouterr()

    assert json.loads(output_file.read_text(encoding="utf-8")) == [
        {"evento": "creado", "id": 1}
    ]


def test_write_migrates_old_json_lines_format(tmp_path, capsys):
    """Migra un archivo viejo (una JSON por línea) a un array."""
    output_file = tmp_path / "notifications.json"
    first = {"evento": "creado", "id": 1}
    output_file.write_text(
        json.dumps(first, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    writer = NotificationWriter(str(output_file))

    second = {"evento": "actualizado", "id": 2}
    writer.write(second)
    capsys.readouterr()

    content = output_file.read_text(encoding="utf-8")

    assert json.loads(content) == [first, second]


def test_read_json_lines_rejects_invalid_content(tmp_path):
    """Un contenido no interpretable como JSON propaga ValueError."""
    output_file = tmp_path / "notifications.json"
    output_file.write_text("esto no es json\n", encoding="utf-8")
    writer = NotificationWriter(str(output_file))

    with pytest.raises(ValueError):
        writer.write({"evento": "creado", "id": 1})
