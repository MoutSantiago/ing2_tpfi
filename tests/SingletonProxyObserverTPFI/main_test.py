import pytest
from typer.testing import CliRunner

from SingletonProxyObserverTPFI.main import app, main

runner = CliRunner()

LOG_MSG = "[LOG] Modo detallado (showLog) activado."


# --- valores por defecto (sin pasar flags) ---


def test_default_port_is_8080():
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "El servidor se iniciará en el puerto: 8080" in result.output
    assert LOG_MSG not in result.output


def test_default_showlog_is_false():
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert LOG_MSG not in result.output


# --- flag --port / -p ---


@pytest.mark.parametrize("port", [8080, 5000, 3000, 80, 443, 65535, 1, 0])
def test_port_flag_variants(port):
    result = runner.invoke(app, ["--port", str(port)])

    assert result.exit_code == 0
    assert f"El servidor se iniciará en el puerto: {port}" in result.output


def test_port_short_flag():
    result = runner.invoke(app, ["-p", "5000"])

    assert result.exit_code == 0
    assert "El servidor se iniciará en el puerto: 5000" in result.output


def test_port_long_and_short_flag_are_equivalent():
    largo = runner.invoke(app, ["--port", "5000"])
    corto = runner.invoke(app, ["-p", "5000"])

    assert largo.exit_code == corto.exit_code == 0
    assert largo.output == corto.output


def test_port_override_ultimo_gana():
    result = runner.invoke(app, ["--port", "5000", "-p", "3000"])

    assert result.exit_code == 0
    assert "El servidor se iniciará en el puerto: 3000" in result.output


def test_port_por_defecto_cuando_solo_se_pasa_showlog():
    result = runner.invoke(app, ["--showLog"])

    assert result.exit_code == 0
    assert "El servidor se iniciará en el puerto: 8080" in result.output


# --- flag --showLog / -v ---


def test_showlog_flag_largo_activa_logs():
    result = runner.invoke(app, ["--showLog"])

    assert result.exit_code == 0
    assert LOG_MSG in result.output


def test_showlog_flag_corto_activa_logs():
    result = runner.invoke(app, ["-v"])

    assert result.exit_code == 0
    assert LOG_MSG in result.output


def test_showlog_largo_y_corto_equivalentes():
    largo = runner.invoke(app, ["--showLog"])
    corto = runner.invoke(app, ["-v"])

    assert largo.exit_code == corto.exit_code == 0
    assert largo.output == corto.output


def test_showlog_ausente_no_imprime_logs():
    result = runner.invoke(app, ["--port", "5000"])

    assert result.exit_code == 0
    assert LOG_MSG not in result.output


# --- combinación de ambas flags ---


@pytest.mark.parametrize("flag_showlog", ["--showLog", "-v"])
@pytest.mark.parametrize("flag_port", ["--port", "-p"])
def test_port_y_showlog_combinadas(flag_port, flag_showlog):
    result = runner.invoke(app, [flag_port, "5000", flag_showlog])

    assert result.exit_code == 0
    assert "El servidor se iniciará en el puerto: 5000" in result.output
    assert LOG_MSG in result.output


def test_orden_de_impresion_log_primero():
    result = runner.invoke(app, ["-p", "3000", "-v"])

    assert result.output == (
        f"{LOG_MSG}\nEl servidor se iniciará en el puerto: 3000\n"
    )


# --- valores inválidos ---


@pytest.mark.parametrize("valor", ["abc", "80.5", "", "8o80", " ", "0x1f"])
def test_port_invalido_falla_con_codigo_2(valor):
    result = runner.invoke(app, ["--port", valor])

    assert result.exit_code == 2
    assert "El servidor se iniciará en el puerto" not in result.output


def test_port_sin_valor_falla():
    result = runner.invoke(app, ["--port"])

    assert result.exit_code == 2


def test_flag_desconocida_falla():
    result = runner.invoke(app, ["--verbose"])

    assert result.exit_code == 2


# --- ayuda ---


def test_help_muestra_las_flags():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "--port" in result.output
    assert "-p" in result.output
    assert "--showLog" in result.output
    assert "-v" in result.output
    assert "Puerto del servidor" in result.output
    assert "Activar modo de logs detallados" in result.output


# --- llamadas directas a la función ---


def test_main_directo_valores_por_defecto(capsys):
    main(port=8080, showLog=False)

    captured = capsys.readouterr()
    assert captured.out == "El servidor se iniciará en el puerto: 8080\n"


@pytest.mark.parametrize(
    ("port", "showlog"),
    [(8080, False), (5000, True), (3000, False), (8080, True)],
)
def test_main_directo_combinaciones(capsys, port, showlog):
    main(port=port, showLog=showlog)

    captured = capsys.readouterr()
    assert f"El servidor se iniciará en el puerto: {port}" in captured.out
    assert (LOG_MSG in captured.out) is showlog


def test_main_directo_no_lanza_excepcion():
    assert main(port=65535, showLog=True) is None
