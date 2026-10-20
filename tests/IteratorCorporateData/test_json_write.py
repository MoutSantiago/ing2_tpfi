"""Tests para JsonWrite de IteratorCorporateData."""

import json
from decimal import Decimal

import pytest

from IteratorCorporateData.app.json_write import JsonWrite


def test_write_dict_produces_valid_json(capsys):
    """Un diccionario se serializa como JSON válido legible con json.loads."""
    data = {"ciudad": "Concepción del Uruguay", "cp": 3260}
    JsonWrite.write(data)
    captured = capsys.readouterr()
    assert json.loads(captured.out) == data


def test_write_list_produces_valid_json(capsys):
    """Una lista se serializa como JSON válido legible con json.loads."""
    data = [1, "dos", None, True]
    JsonWrite.write(data)
    captured = capsys.readouterr()
    assert json.loads(captured.out) == data


def test_write_no_ascii_escape(capsys):
    """Los caracteres con tilde se escriben tal cual sin secuencias \\u00f3."""
    data = {"ciudad": "Concepción del Uruguay"}
    JsonWrite.write(data)
    captured = capsys.readouterr()
    assert "Concepción del Uruguay" in captured.out
    assert "\\u00f3" not in captured.out


def test_write_decimal_integer_as_int(capsys):
    """Un Decimal entero se imprime como entero."""
    data = {"valor": Decimal("10")}
    JsonWrite.write(data)
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed == {"valor": 10}
    assert isinstance(parsed["valor"], int)


def test_write_decimal_with_fraction_as_float(capsys):
    """Un Decimal con decimales se imprime como número decimal."""
    data = {"valor": Decimal("10.5")}
    JsonWrite.write(data)
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed == {"valor": 10.5}
    assert isinstance(parsed["valor"], float)


def test_write_decimal_two_dot_zero_as_int(capsys):
    """Un Decimal como 2.0 se imprime como entero al no tener parte decimal."""
    data = {"valor": Decimal("2.0")}
    JsonWrite.write(data)
    captured = capsys.readouterr()
    assert '"valor": 2' in captured.out


def test_write_non_serializable_raises_type_error(capsys):
    """Un tipo no serializable lanza TypeError."""
    with pytest.raises(TypeError):
        JsonWrite.write({"valor": {1, 2, 3}})


def test_write_output_ends_with_newline(capsys):
    """La salida termina con un salto de línea."""
    JsonWrite.write({"a": 1})
    captured = capsys.readouterr()
    assert captured.out.endswith("\n")


def test_write_output_is_single_json_document(capsys):
    """La salida contiene un único documento JSON."""
    data = {"a": 1, "b": [1, 2]}
    JsonWrite.write(data)
    captured = capsys.readouterr()
    texto = captured.out.strip()
    parsed, end = json.JSONDecoder().raw_decode(texto)
    assert end == len(texto)
    assert parsed == data


def test_write_indentation_is_two_spaces(capsys):
    """El JSON se escribe con indentación de 2 espacios."""
    data = {"a": {"b": 1}}
    JsonWrite.write(data)
    captured = capsys.readouterr()
    assert captured.out == '{\n  "a": {\n    "b": 1\n  }\n}\n'
