import json

import pytest

from ObserverClient.app.notification_writer import NotificationWriter


def test_write_without_output_path_prints_json_to_stdout(
    tmp_path, monkeypatch, capsys
):
    """Imprime la notificación por stdout sin crear archivos."""
    monkeypatch.chdir(tmp_path)

    writer = NotificationWriter(None)
    message = {"evento": "actualización", "mensaje": "Producto actualizado"}

    writer.write(message)

    captured = capsys.readouterr()

    assert captured.out == json.dumps(message, ensure_ascii=False) + "\n"
    assert captured.err == ""
    assert list(tmp_path.iterdir()) == []


def test_write_with_output_path_prints_and_saves_notification(
    tmp_path, capsys
):
    """Imprime la notificación y la guarda en el archivo configurado."""
    output_file = tmp_path / "notifications.jsonl"
    writer = NotificationWriter(str(output_file))
    message = {"evento": "actualización", "producto": "Zapatillas"}

    writer.write(message)

    captured = capsys.readouterr()
    expected_line = json.dumps(message, ensure_ascii=False)

    assert captured.out == expected_line + "\n"
    assert captured.err == ""
    assert output_file.read_text(encoding="utf-8") == expected_line + "\n"


def test_write_appends_multiple_notifications(tmp_path, capsys):
    """Agrega notificaciones al archivo sin sobrescribir las anteriores."""
    output_file = tmp_path / "notifications.jsonl"
    writer = NotificationWriter(str(output_file))

    first_message = {"evento": "creado", "id": 1}
    second_message = {"evento": "actualizado", "id": 2}

    writer.write(first_message)
    writer.write(second_message)

    captured = capsys.readouterr()
    lines = output_file.read_text(encoding="utf-8").splitlines()

    assert captured.out == (
        json.dumps(first_message, ensure_ascii=False)
        + "\n"
        + json.dumps(second_message, ensure_ascii=False)
        + "\n"
    )
    assert len(lines) == 2
    assert json.loads(lines[0]) == first_message
    assert json.loads(lines[1]) == second_message


def test_write_preserves_accents_in_utf8_file(tmp_path, capsys):
    """Guarda caracteres acentuados sin convertirlos en secuencias Unicode."""
    output_file = tmp_path / "notifications.jsonl"
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
    assert json.loads(content) == message


def test_init_with_invalid_output_path_raises_oserror(tmp_path):
    """Propaga OSError cuando no se puede abrir la ruta de salida."""
    invalid_path = tmp_path / "directorio_inexistente" / "notifications.jsonl"

    with pytest.raises(OSError):
        NotificationWriter(str(invalid_path))


def test_each_output_line_is_valid_json(tmp_path, capsys):
    """Cada notificación guardada ocupa una línea JSON válida."""
    output_file = tmp_path / "notifications.jsonl"
    writer = NotificationWriter(str(output_file))

    messages = [
        {"evento": "creado", "id": 1},
        {"evento": "eliminado", "id": 2},
        {"evento": "actualizado", "id": 3},
    ]

    for message in messages:
        writer.write(message)

    capsys.readouterr()
    lines = output_file.read_text(encoding="utf-8").splitlines()

    assert len(lines) == len(messages)

    for line, expected_message in zip(lines, messages):
        assert json.loads(line) == expected_message
