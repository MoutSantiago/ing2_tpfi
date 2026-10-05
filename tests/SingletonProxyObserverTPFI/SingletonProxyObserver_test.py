import pytest
from typer.testing import CliRunner

from SingletonProxyObserverTPFI.singletonproxyobserver import app, main

runner = CliRunner()

LOG_MSG = "[LOG] Modo detallado (showLog) activado."


# --- valores por defecto (sin pasar flags) ---


def test_default_port_is_8080():
    """Testea por defecto que el puerto sea 8080."""
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "El servidor se iniciará en el puerto: 8080" in result.output
    assert LOG_MSG not in result.output


def test_default_showlog_is_false():
    """Testea por defecto que el flag showLog sea False."""
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert LOG_MSG not in result.output


# --- flag --port / -p ---


@pytest.mark.parametrize("port", [8080, 5000, 3000, 80, 443, 65535, 1, 0])
def test_port_flag_variants(port):
    """Testea que el flag --port y -p acepten distintos puertos válidos."""
    result = runner.invoke(app, ["--port", str(port)])

    assert result.exit_code == 0
    assert f"El servidor se iniciará en el puerto: {port}" in result.output


def test_port_long_and_short_flag_are_equivalent():
    """Testea que los flags --port y -p sean equivalentes y
    produzcan la misma salida."""
    largo = runner.invoke(app, ["--port", "5000"])
    corto = runner.invoke(app, ["-p", "5000"])

    assert largo.exit_code == corto.exit_code == 0
    assert largo.output == corto.output


def test_port_override_ultimo_gana():
    """Testea que si se pasan ambos flags --port y -p, el último
    especificado prevalezca y determine el puerto final."""
    result = runner.invoke(app, ["--port", "5000", "-p", "3000"])

    assert result.exit_code == 0
    assert "El servidor se iniciará en el puerto: 3000" in result.output


def test_port_por_defecto_cuando_solo_se_pasa_showlog():
    """Testea que si se pasa solo el flag -v,
    el puerto por defecto sea 8080."""
    result = runner.invoke(app, ["-v"])

    assert result.exit_code == 0
    assert "El servidor se iniciará en el puerto: 8080" in result.output


# --- flag -v ---


def test_showlog_flag_corto_activa_logs():
    """Testea que el flag -v active la impresión de logs."""
    result = runner.invoke(app, ["-v"])

    assert result.exit_code == 0
    assert LOG_MSG in result.output


def test_showlog_ausente_no_imprime_logs():
    """Testea que si no se pasa el flag -v, no se impriman logs."""
    result = runner.invoke(app, ["--port", "5000"])

    assert result.exit_code == 0
    assert LOG_MSG not in result.output


# --- combinación de ambas flags ---


@pytest.mark.parametrize("flag_showlog", ["-v"])
@pytest.mark.parametrize("flag_port", ["--port", "-p"])
def test_port_y_showlog_combinadas(flag_port, flag_showlog):
    """Testea que se puedan combinar ambos flags y que la salida sea
    correcta."""
    result = runner.invoke(app, [flag_port, "5000", flag_showlog])

    assert result.exit_code == 0
    assert "El servidor se iniciará en el puerto: 5000" in result.output
    assert LOG_MSG in result.output


# --- valores inválidos ---


@pytest.mark.parametrize("valor", ["abc", "80.5", "", "8o80", " ", "0x1f"])
def test_port_invalido_falla_con_codigo_2(valor):
    """Testea que si se pasa un valor inválido para el flag --port,
    la aplicación falle con código de salida 2 y no imprima el mensaje
    de inicio del servidor."""
    result = runner.invoke(app, ["--port", valor])

    assert result.exit_code == 2
    assert "El servidor se iniciará en el puerto" not in result.output


def test_flag_desconocida_falla():
    """Testea que si se pasa un flag desconocido, la aplicación falle con
    código de salida 2."""
    result = runner.invoke(app, ["--verbose"])

    assert result.exit_code == 2


# --- ayuda ---


def test_help_muestra_las_flags():
    """Testea que la ayuda muestre las flags --port, -p y -v con sus
    descripciones."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "--port" in result.output
    assert "-p" in result.output
    assert "-v" in result.output
    assert "Puerto del servidor" in result.output
    assert "Activar modo de logs detallados" in result.output


# --- llamadas directas a la función ---


def test_main_directo_valores_por_defecto(capsys):
    """Testea que la función main() llamada directamente con valores por
    defecto funcione correctamente."""
    main(port=8080, showLog=False)

    captured = capsys.readouterr()
    assert captured.out == "El servidor se iniciará en el puerto: 8080\n"


@pytest.mark.parametrize(
    ("port", "showlog"),
    [(8080, False), (5000, True), (3000, False), (8080, True)],
)
def test_main_directo_combinaciones(capsys, port, showlog):
    """Testea que la función main() llamada directamente con
    distintas combinaciones de valores funcione correctamente."""
    main(port=port, showLog=showlog)

    captured = capsys.readouterr()
    assert f"El servidor se iniciará en el puerto: {port}" in captured.out
    assert (LOG_MSG in captured.out) is showlog


def test_main_directo_no_lanza_excepcion():
    """Testea que la función main() llamada directamente
    no lance ninguna excepción y retorne None."""
    assert main(port=65535, showLog=True) is None
