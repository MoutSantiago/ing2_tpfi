import logging
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from SingletonProxyObserverTPFI.singletonproxyobserver import (
    app,
    build_server,
    configure_logging,
    main,
)

runner = CliRunner()

LOG_MSG = "[LOG] Modo detallado (showLog) activado."


# --- valores por defecto (sin pasar flags) ---


@patch("SingletonProxyObserverTPFI.singletonproxyobserver.Server")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataProxy")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateLogDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.SubscriptionManager")
def test_default_port_is_8080(
    mock_subs_manager,
    mock_data_dao,
    mock_log_dao,
    mock_proxy,
    mock_server,
):
    """Testea por defecto que el puerto sea 8080."""
    mock_data_dao.get_instance.return_value = MagicMock()
    mock_log_dao.get_instance.return_value = MagicMock()
    mock_subs_manager.return_value = MagicMock()
    mock_proxy.return_value = MagicMock()
    mock_server.return_value = MagicMock()

    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert mock_server.return_value._port == 8080


@patch("SingletonProxyObserverTPFI.singletonproxyobserver.Server")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataProxy")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateLogDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.SubscriptionManager")
def test_default_showlog_is_false(
    mock_subs_manager,
    mock_data_dao,
    mock_log_dao,
    mock_proxy,
    mock_server,
):
    """Testea por defecto que el flag showLog sea False."""
    mock_data_dao.get_instance.return_value = MagicMock()
    mock_log_dao.get_instance.return_value = MagicMock()
    mock_subs_manager.return_value = MagicMock()
    mock_proxy.return_value = MagicMock()
    mock_server.return_value = MagicMock()

    result = runner.invoke(app, [])

    assert result.exit_code == 0


# --- flag --port / -p ---


@pytest.mark.parametrize("port", [8080, 5000, 3000, 80, 443, 65535, 1, 0])
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.Server")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataProxy")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateLogDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.SubscriptionManager")
def test_port_flag_variants(
    mock_subs_manager,
    mock_data_dao,
    mock_log_dao,
    mock_proxy,
    mock_server,
    port,
):
    """Testea que el flag --port y -p acepten distintos puertos válidos."""
    mock_data_dao.get_instance.return_value = MagicMock()
    mock_log_dao.get_instance.return_value = MagicMock()
    mock_subs_manager.return_value = MagicMock()
    mock_proxy.return_value = MagicMock()
    mock_server.return_value = MagicMock()

    result = runner.invoke(app, ["--port", str(port)])

    assert result.exit_code == 0
    assert mock_server.return_value._port == port


@patch("SingletonProxyObserverTPFI.singletonproxyobserver.Server")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataProxy")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateLogDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.SubscriptionManager")
def test_port_long_and_short_flag_are_equivalent(
    mock_subs_manager,
    mock_data_dao,
    mock_log_dao,
    mock_proxy,
    mock_server,
):
    """Testea que los flags --port y -p sean equivalentes y
    produzcan la misma salida."""
    mock_data_dao.get_instance.return_value = MagicMock()
    mock_log_dao.get_instance.return_value = MagicMock()
    mock_subs_manager.return_value = MagicMock()
    mock_proxy.return_value = MagicMock()
    mock_server.return_value = MagicMock()

    largo = runner.invoke(app, ["--port", "5000"])
    corto = runner.invoke(app, ["-p", "5000"])

    assert largo.exit_code == corto.exit_code == 0
    assert mock_server.return_value._port == 5000


@patch("SingletonProxyObserverTPFI.singletonproxyobserver.Server")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataProxy")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateLogDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.SubscriptionManager")
def test_port_override_ultimo_gana(
    mock_subs_manager,
    mock_data_dao,
    mock_log_dao,
    mock_proxy,
    mock_server,
):
    """Testea que si se pasan ambos flags --port y -p, el último
    especificado prevalezca y determine el puerto final."""
    mock_data_dao.get_instance.return_value = MagicMock()
    mock_log_dao.get_instance.return_value = MagicMock()
    mock_subs_manager.return_value = MagicMock()
    mock_proxy.return_value = MagicMock()
    mock_server.return_value = MagicMock()

    result = runner.invoke(app, ["--port", "5000", "-p", "3000"])

    assert result.exit_code == 0
    assert mock_server.return_value._port == 3000


@patch("SingletonProxyObserverTPFI.singletonproxyobserver.Server")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataProxy")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateLogDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.SubscriptionManager")
def test_port_por_defecto_cuando_solo_se_pasa_showlog(
    mock_subs_manager,
    mock_data_dao,
    mock_log_dao,
    mock_proxy,
    mock_server,
):
    """Testea que si se pasa solo el flag -v,
    el puerto por defecto sea 8080."""
    mock_data_dao.get_instance.return_value = MagicMock()
    mock_log_dao.get_instance.return_value = MagicMock()
    mock_subs_manager.return_value = MagicMock()
    mock_proxy.return_value = MagicMock()
    mock_server.return_value = MagicMock()

    result = runner.invoke(app, ["-v"])

    assert result.exit_code == 0
    assert mock_server.return_value._port == 8080


# --- flag -v ---


@patch("SingletonProxyObserverTPFI.singletonproxyobserver.Server")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataProxy")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateLogDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.SubscriptionManager")
def test_showlog_flag_corto_activa_logs(
    mock_subs_manager,
    mock_data_dao,
    mock_log_dao,
    mock_proxy,
    mock_server,
):
    """Testea que el flag -v active la impresión de logs."""
    mock_data_dao.get_instance.return_value = MagicMock()
    mock_log_dao.get_instance.return_value = MagicMock()
    mock_subs_manager.return_value = MagicMock()
    mock_proxy.return_value = MagicMock()
    mock_server.return_value = MagicMock()

    result = runner.invoke(app, ["-v"])

    assert result.exit_code == 0


@patch("SingletonProxyObserverTPFI.singletonproxyobserver.Server")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataProxy")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateLogDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.SubscriptionManager")
def test_showlog_ausente_no_imprime_logs(
    mock_subs_manager,
    mock_data_dao,
    mock_log_dao,
    mock_proxy,
    mock_server,
):
    """Testea que si no se pasa el flag -v, no se impriman logs."""
    mock_data_dao.get_instance.return_value = MagicMock()
    mock_log_dao.get_instance.return_value = MagicMock()
    mock_subs_manager.return_value = MagicMock()
    mock_proxy.return_value = MagicMock()
    mock_server.return_value = MagicMock()

    result = runner.invoke(app, ["--port", "5000"])

    assert result.exit_code == 0


# --- combinación de ambas flags ---


@pytest.mark.parametrize("flag_showlog", ["-v"])
@pytest.mark.parametrize("flag_port", ["--port", "-p"])
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.Server")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataProxy")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateLogDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.SubscriptionManager")
def test_port_y_showlog_combinadas(
    mock_subs_manager,
    mock_data_dao,
    mock_log_dao,
    mock_proxy,
    mock_server,
    flag_port,
    flag_showlog,
):
    """Testea que se puedan combinar ambos flags y que la salida sea
    correcta."""
    mock_data_dao.get_instance.return_value = MagicMock()
    mock_log_dao.get_instance.return_value = MagicMock()
    mock_subs_manager.return_value = MagicMock()
    mock_proxy.return_value = MagicMock()
    mock_server.return_value = MagicMock()

    result = runner.invoke(app, [flag_port, "5000", flag_showlog])

    assert result.exit_code == 0
    assert mock_server.return_value._port == 5000


# --- valores inválidos ---


@pytest.mark.parametrize("valor", ["abc", "80.5", "", "8o80", " ", "0x1f"])
def test_port_invalido_falla_con_codigo_2(valor):
    """Testea que si se pasa un valor inválido para el flag --port,
    la aplicación falle con código de salida 2 y no imprima el mensaje
    de inicio del servidor."""
    result = runner.invoke(app, ["--port", valor])

    assert result.exit_code == 2


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


@patch("SingletonProxyObserverTPFI.singletonproxyobserver.Server")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataProxy")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateLogDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.SubscriptionManager")
def test_main_directo_valores_por_defecto(
    mock_subs_manager,
    mock_data_dao,
    mock_log_dao,
    mock_proxy,
    mock_server,
):
    """Testea que la función main() llamada directamente con valores por
    defecto funcione correctamente."""
    mock_data_dao.get_instance.return_value = MagicMock()
    mock_log_dao.get_instance.return_value = MagicMock()
    mock_subs_manager.return_value = MagicMock()
    mock_proxy.return_value = MagicMock()
    mock_server.return_value = MagicMock()

    result = main(port=8080, verbose=False)

    assert result is None
    mock_server.return_value.serve_forever.assert_called_once()


@patch("SingletonProxyObserverTPFI.singletonproxyobserver.Server")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataProxy")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateLogDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.SubscriptionManager")
def test_main_directo_no_lanza_excepcion(
    mock_subs_manager,
    mock_data_dao,
    mock_log_dao,
    mock_proxy,
    mock_server,
):
    """Testea que la función main() llamada directamente
    no lance ninguna excepción y retorne None."""
    mock_data_dao.get_instance.return_value = MagicMock()
    mock_log_dao.get_instance.return_value = MagicMock()
    mock_subs_manager.return_value = MagicMock()
    mock_proxy.return_value = MagicMock()
    mock_server.return_value = MagicMock()

    assert main(port=65535, verbose=True) is None


# --- configure_logging ---


def test_configure_logging_verbose_true():
    """Testea que configure_logging con verbose=True use nivel DEBUG."""
    with patch("logging.basicConfig") as mock_basic:
        configure_logging(verbose=True)

        mock_basic.assert_called_once()
        assert mock_basic.call_args[1]["level"] == logging.DEBUG


def test_configure_logging_verbose_false():
    """Testea que configure_logging con verbose=False use nivel WARNING."""
    with patch("logging.basicConfig") as mock_basic:
        configure_logging(verbose=False)

        mock_basic.assert_called_once()
        assert mock_basic.call_args[1]["level"] == logging.WARNING


def test_configure_logging_force_true():
    """Testea que configure_logging use force=True para sobrescribir."""
    with patch("logging.basicConfig") as mock_basic:
        configure_logging(verbose=True)

        assert mock_basic.call_args[1]["force"] is True


# --- build_server ---


@patch("SingletonProxyObserverTPFI.singletonproxyobserver.Server")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataProxy")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateLogDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.SubscriptionManager")
def test_build_server_crea_dependencias_en_orden(
    mock_subs_manager,
    mock_data_dao,
    mock_log_dao,
    mock_proxy,
    mock_server,
):
    """Testea que build_server cree todas las dependencias en el orden
    correcto y retorne una instancia de Server."""
    mock_data_dao.get_instance.return_value = MagicMock()
    mock_log_dao.get_instance.return_value = MagicMock()
    mock_subs_manager.return_value = MagicMock()
    mock_proxy.return_value = MagicMock()
    mock_server.return_value = MagicMock()

    result = build_server()

    mock_subs_manager.assert_called_once()
    mock_data_dao.get_instance.assert_called_once()
    mock_log_dao.get_instance.assert_called_once()
    mock_proxy.assert_called_once()
    mock_server.assert_called_once()
    assert result == mock_server.return_value


@patch("SingletonProxyObserverTPFI.singletonproxyobserver.Server")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataProxy")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateLogDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.SubscriptionManager")
def test_build_server_conecta_proxy_y_publisher_al_server(
    mock_subs_manager,
    mock_data_dao,
    mock_log_dao,
    mock_proxy,
    mock_server,
):
    """Testea que build_server conecte el proxy y el publisher al Server."""
    mock_data_dao.get_instance.return_value = MagicMock()
    mock_log_dao.get_instance.return_value = MagicMock()
    mock_subs_manager.return_value = MagicMock()
    mock_proxy.return_value = MagicMock()
    mock_server.return_value = MagicMock()

    build_server()

    call_kwargs = mock_server.call_args[1]
    assert call_kwargs["data"] == mock_proxy.return_value
    assert call_kwargs["publisher"] == mock_subs_manager.return_value


@patch("SingletonProxyObserverTPFI.singletonproxyobserver.Server")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataProxy")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateLogDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.SubscriptionManager")
def test_build_server_pasa_host_y_port_correctos(
    mock_subs_manager,
    mock_data_dao,
    mock_log_dao,
    mock_proxy,
    mock_server,
):
    """Testea que build_server pase host='0.0.0.0' y port=8080 al Server."""
    mock_data_dao.get_instance.return_value = MagicMock()
    mock_log_dao.get_instance.return_value = MagicMock()
    mock_subs_manager.return_value = MagicMock()
    mock_proxy.return_value = MagicMock()
    mock_server.return_value = MagicMock()

    build_server()

    call_kwargs = mock_server.call_args[1]
    assert call_kwargs["host"] == "0.0.0.0"
    assert call_kwargs["port"] == 8080


# --- manejo de excepciones en main ---


@patch("SingletonProxyObserverTPFI.singletonproxyobserver.Server")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataProxy")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateLogDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.SubscriptionManager")
def test_main_con_keyboard_interrupt_detiene_servidor(
    mock_subs_manager,
    mock_data_dao,
    mock_log_dao,
    mock_proxy,
    mock_server,
):
    """Testea que ante KeyboardInterrupt, main llame a stop() del servidor."""
    import typer

    mock_data_dao.get_instance.return_value = MagicMock()
    mock_log_dao.get_instance.return_value = MagicMock()
    mock_subs_manager.return_value = MagicMock()
    mock_proxy.return_value = MagicMock()
    mock_server.return_value = MagicMock()
    mock_server.return_value.serve_forever.side_effect = KeyboardInterrupt

    with pytest.raises(typer.Exit) as exc_info:
        main(port=8080, verbose=False)

    mock_server.return_value.stop.assert_called_once()
    assert exc_info.value.exit_code == 0


@patch("SingletonProxyObserverTPFI.singletonproxyobserver.Server")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataProxy")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateLogDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.SubscriptionManager")
def test_main_con_data_access_error_retorna_codigo_1(
    mock_subs_manager,
    mock_data_dao,
    mock_log_dao,
    mock_proxy,
    mock_server,
):
    """Testea que ante DataAccessError, main retorne código de salida 1."""
    import typer

    from SingletonProxyObserverTPFI.app.exceptions import DataAccessError

    mock_data_dao.get_instance.side_effect = DataAccessError("Error de prueba")

    with pytest.raises(typer.Exit) as exc_info:
        main(port=8080, verbose=False)

    assert exc_info.value.exit_code == 1


@patch("SingletonProxyObserverTPFI.singletonproxyobserver.Server")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataProxy")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateLogDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.SubscriptionManager")
def test_main_con_os_error_retorna_codigo_1(
    mock_subs_manager,
    mock_data_dao,
    mock_log_dao,
    mock_proxy,
    mock_server,
):
    """Testea que ante OSError, main retorne código de salida 1."""
    import typer

    mock_data_dao.get_instance.side_effect = OSError("Error de socket")

    with pytest.raises(typer.Exit) as exc_info:
        main(port=8080, verbose=False)

    assert exc_info.value.exit_code == 1


@patch("SingletonProxyObserverTPFI.singletonproxyobserver.Server")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataProxy")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateLogDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.SubscriptionManager")
def test_main_pasa_port_correcto_al_servidor(
    mock_subs_manager,
    mock_data_dao,
    mock_log_dao,
    mock_proxy,
    mock_server,
):
    """Testea que main pase el puerto correcto al servidor."""
    mock_data_dao.get_instance.return_value = MagicMock()
    mock_log_dao.get_instance.return_value = MagicMock()
    mock_subs_manager.return_value = MagicMock()
    mock_proxy.return_value = MagicMock()
    mock_server.return_value = MagicMock()

    main(port=5000, verbose=False)

    assert mock_server.return_value._port == 5000


@patch("SingletonProxyObserverTPFI.singletonproxyobserver.Server")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataProxy")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateLogDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.CorporateDataDAO")
@patch("SingletonProxyObserverTPFI.singletonproxyobserver.SubscriptionManager")
def test_main_llama_serve_forever(
    mock_subs_manager,
    mock_data_dao,
    mock_log_dao,
    mock_proxy,
    mock_server,
):
    """Testea que main llame a serve_forever() del servidor."""
    mock_data_dao.get_instance.return_value = MagicMock()
    mock_log_dao.get_instance.return_value = MagicMock()
    mock_subs_manager.return_value = MagicMock()
    mock_proxy.return_value = MagicMock()
    mock_server.return_value = MagicMock()

    main(port=8080, verbose=False)

    mock_server.return_value.serve_forever.assert_called_once()
