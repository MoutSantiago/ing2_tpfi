"""
Tests unitarios para server.py.
"""

import json
from unittest.mock import Mock, patch

import pytest

from SingletonProxyObserverTPFI.app.server import Server


@pytest.fixture
def data():
    """
    Mock del CorporateDataProxy.

    El servidor no necesita conocer la implementación real del Proxy
    durante estas pruebas.
    """

    return Mock()


@pytest.fixture
def publisher():
    """
    Mock del Publisher.
    """

    return Mock()


@pytest.fixture
def server(data, publisher):
    """
    Crea una instancia de Server utilizando mocks.
    """

    return Server(
        host="127.0.0.1",
        port=8080,
        data=data,
        publisher=publisher,
    )


# -------------------------------------------------------------------
# Constructor
# -------------------------------------------------------------------


def test_server_valores_por_defecto(data, publisher):
    """
    Verifica los valores de host y port del constructor.
    """

    server = Server(
        data=data,
        publisher=publisher,
    )

    assert server._host == "0.0.0.0"
    assert server._port == 8080
    assert server._sock is None
    assert server._data is data
    assert server._publisher is publisher
    assert server._stop_event.is_set() is False


def test_server_requiere_data(publisher):
    """
    Verifica que el servidor no pueda crearse sin CorporateDataProxy.
    """

    with pytest.raises(ValueError):
        Server(
            data=None,
            publisher=publisher,
        )


def test_server_requiere_publisher(data):
    """
    Verifica que el servidor no pueda crearse sin Publisher.
    """

    with pytest.raises(ValueError):
        Server(
            data=data,
            publisher=None,
        )


# -------------------------------------------------------------------
# _validate()
# -------------------------------------------------------------------


def test_validate_get_correcto(server):
    """
    Una solicitud get mínima debe ser válida.
    """

    request = {
        "UUID": "uuid-123",
        "ID": "UADER-FCyT-IS2",
        "ACTION": "get",
    }

    assert server._validate(request) is True


def test_validate_list_correcto(server):
    """
    Una solicitud list no necesita ID.
    """

    request = {
        "UUID": "uuid-123",
        "ACTION": "list",
    }

    assert server._validate(request) is True


def test_validate_subscribe_correcto(server):
    """
    Una solicitud subscribe válida solamente necesita UUID y ACTION.
    """

    request = {
        "UUID": "uuid-123",
        "ACTION": "subscribe",
    }

    assert server._validate(request) is True


def test_validate_set_correcto(server):
    """
    Una solicitud set válida debe tener ID y al menos un campo
    de CorporateData.
    """

    request = {
        "UUID": "uuid-123",
        "ID": "UADER-FCyT-IS2",
        "ACTION": "set",
        "cp": "3260",
    }

    assert server._validate(request) is True


def test_validate_rechaza_request_no_dict(server):
    """
    Un array JSON no debe considerarse una petición válida.
    """

    assert server._validate([]) is False


def test_validate_rechaza_uuid_ausente(server):
    """
    UUID es obligatorio.
    """

    request = {
        "ACTION": "list",
    }

    assert server._validate(request) is False


def test_validate_rechaza_uuid_vacio(server):
    """
    UUID no puede ser una cadena vacía.
    """

    request = {
        "UUID": "",
        "ACTION": "list",
    }

    assert server._validate(request) is False


@pytest.mark.parametrize(
    "action",
    [
        "delete",
        "update",
        "foo",
        "",
        "GETTT",
    ],
)
def test_validate_rechaza_action_invalida(server, action):
    """
    Solamente se permiten las cuatro acciones definidas por el TPFI.
    """

    request = {
        "UUID": "uuid-123",
        "ACTION": action,
    }

    assert server._validate(request) is False


def test_validate_rechaza_get_sin_id(server):
    """
    get requiere ID.
    """

    request = {
        "UUID": "uuid-123",
        "ACTION": "get",
    }

    assert server._validate(request) is False


def test_validate_rechaza_set_sin_id(server):
    """
    set requiere ID.
    """

    request = {
        "UUID": "uuid-123",
        "ACTION": "set",
        "cp": "3260",
    }

    assert server._validate(request) is False


def test_validate_rechaza_set_sin_campos(server):
    """
    set requiere al menos un campo de CorporateData.
    """

    request = {
        "UUID": "uuid-123",
        "ID": "UADER-FCyT-IS2",
        "ACTION": "set",
    }

    assert server._validate(request) is False


def test_validate_acepta_set_con_cualquier_campo_corporate_data(server):
    """
    Comprueba que un único campo del tuple sea suficiente para
    considerar válido un set.
    """

    for field in server.CORPORATE_DATA_FIELDS:
        request = {
            "UUID": "uuid-123",
            "ID": "UADER-FCyT-IS2",
            "ACTION": "set",
            field: "valor",
        }

        assert server._validate(request) is True


# -------------------------------------------------------------------
# _dispatch()
# -------------------------------------------------------------------


def test_dispatch_get(server, data):
    """
    Verifica que get sea derivado al CorporateDataProxy.
    """

    expected = {
        "id": "UADER-FCyT-IS2",
        "cp": "3260",
    }

    data.get.return_value = expected

    request = {
        "UUID": "uuid-123",
        "ID": "UADER-FCyT-IS2",
        "ACTION": "get",
    }

    result = server._dispatch(
        request,
        Mock(),
    )

    assert result == expected

    data.get.assert_called_once_with(
        "UADER-FCyT-IS2",
        "uuid-123",
    )


def test_dispatch_list(server, data):
    """
    Verifica que list sea derivado al CorporateDataProxy.
    """

    expected = [
        {
            "id": "UADER-FCyT-IS2",
        }
    ]

    data.list.return_value = expected

    request = {
        "UUID": "uuid-123",
        "ACTION": "list",
    }

    result = server._dispatch(
        request,
        Mock(),
    )

    assert result == expected

    data.list.assert_called_once_with(
        "uuid-123",
    )


def test_dispatch_set(server, data):
    """
    Verifica que set sea derivado al CorporateDataProxy con los
    campos enviados por el cliente.
    """

    expected = {
        "id": "UADER-FCyT-IS2",
        "cp": "3260",
    }

    data.set.return_value = expected

    request = {
        "UUID": "uuid-123",
        "ID": "UADER-FCyT-IS2",
        "ACTION": "set",
        "cp": "3260",
        "telefono": "03442 43-1442",
    }

    result = server._dispatch(
        request,
        Mock(),
    )

    assert result == expected

    data.set.assert_called_once_with(
        "UADER-FCyT-IS2",
        {
            "cp": "3260",
            "telefono": "03442 43-1442",
        },
        "uuid-123",
    )


def test_dispatch_subscribe(server):
    """
    Verifica que subscribe invoque _handle_subscribe y devuelva None.
    """

    conn = Mock()

    request = {
        "UUID": "uuid-123",
        "ACTION": "subscribe",
    }

    with patch.object(
        server,
        "_handle_subscribe",
    ) as handle_subscribe:
        result = server._dispatch(
            request,
            conn,
        )

    assert result is None

    handle_subscribe.assert_called_once_with(
        conn,
        "uuid-123",
    )


# -------------------------------------------------------------------
# _handle_subscribe()
# -------------------------------------------------------------------


def test_handle_subscribe_audita_antes_de_suscribir(
    server,
    data,
    publisher,
):
    """
    Verifica el orden lógico de la suscripción:

    1. auditoría;
    2. creación del observer;
    3. registro en Publisher.
    """

    conn = Mock()

    with patch(
        "SingletonProxyObserverTPFI.app.server.ClientObserver"
    ) as observer_class:
        observer = Mock()
        observer_class.return_value = observer

        server._handle_subscribe(
            conn,
            "uuid-123",
        )

    data.audit_subscription.assert_called_once_with(
        "uuid-123",
    )

    observer_class.assert_called_once_with(
        sock=conn,
        uuid="uuid-123",
    )

    publisher.subscribe.assert_called_once_with(
        observer,
    )


def test_handle_subscribe_no_crea_observer_si_auditoria_falla(
    server,
    data,
    publisher,
):
    """
    Si la auditoría falla, el cliente no debe registrarse como
    suscriptor.
    """

    data.audit_subscription.side_effect = RuntimeError("Error de auditoría")

    conn = Mock()

    with patch(
        "SingletonProxyObserverTPFI.app.server.ClientObserver"
    ) as observer_class:
        with pytest.raises(RuntimeError):
            server._handle_subscribe(
                conn,
                "uuid-123",
            )

    observer_class.assert_not_called()

    publisher.subscribe.assert_not_called()


# -------------------------------------------------------------------
# _send_json()
# -------------------------------------------------------------------


def test_send_json_envia_json_terminado_en_newline():
    """
    Verifica el formato del protocolo de comunicación.
    """

    conn = Mock()

    response = {
        "id": "UADER-FCyT-IS2",
        "cp": "3260",
    }

    Server._send_json(
        conn,
        response,
    )

    conn.sendall.assert_called_once()

    sent_data = conn.sendall.call_args.args[0]

    assert isinstance(sent_data, bytes)

    sent_text = sent_data.decode("utf-8")

    assert sent_text.endswith("\n")

    assert json.loads(sent_text) == response


def test_send_error_envia_formato_error():
    """
    Verifica que los errores se envíen como JSON.
    """

    conn = Mock()

    Server._send_error(
        conn,
        "Petición inválida.",
    )

    sent_data = conn.sendall.call_args.args[0]

    response = json.loads(sent_data.decode("utf-8"))

    assert response == {
        "Error": "Petición inválida.",
    }


# -------------------------------------------------------------------
# _receive_request()
# -------------------------------------------------------------------


def test_receive_request_lee_hasta_newline(server):
    """
    Verifica que la petición se interprete como una línea JSON.
    """

    conn = Mock()

    conn.recv.side_effect = [
        b'{"UUID": "abc",',
        b'"ACTION": "list"}\n',
    ]

    result = server._receive_request(conn)

    assert result == ('{"UUID": "abc","ACTION": "list"}')


def test_receive_request_rechaza_request_demasiado_grande(server):
    """
    Verifica que exista un límite para el tamaño de la petición.
    """

    conn = Mock()

    conn.recv.return_value = b"x" * server.MAX_REQUEST_SIZE

    with pytest.raises(ValueError):
        server._receive_request(conn)


def test_receive_request_cliente_cierra_sin_enviar_datos(server):
    """
    Verifica el caso en que el cliente cierre el socket antes de
    enviar una petición.
    """

    conn = Mock()

    conn.recv.return_value = b""

    with pytest.raises(ConnectionError):
        server._receive_request(conn)


# -------------------------------------------------------------------
# stop()
# -------------------------------------------------------------------


def test_stop_activa_stop_event(server):
    """
    Verifica que stop() solicite la detención del servidor.
    """

    server.stop()

    assert server._stop_event.is_set() is True


def test_stop_cierra_socket_de_escucha(server):
    """
    Verifica que stop() cierre el socket de escucha.
    """

    sock = Mock()

    server._sock = sock

    server.stop()

    sock.close.assert_called_once()

    assert server._sock is None


def test_stop_no_falla_si_no_hay_socket(server):
    """
    stop() debe poder llamarse incluso antes de iniciar
    serve_forever().
    """

    server.stop()

    assert server._stop_event.is_set() is True


# -------------------------------------------------------------------
# _handle_client()
# -------------------------------------------------------------------


def test_handle_client_get_envia_respuesta_y_cierra(
    server,
    data,
):
    """
    Verifica el camino feliz de una petición get.

    Para esta prueba se utiliza un socket mockeado, por lo que no se
    abre ningún puerto real.
    """

    conn = Mock()

    request = b'{"UUID":"uuid-123","ID":"registro-1","ACTION":"get"}\n'

    conn.recv.return_value = request

    data.get.return_value = {
        "id": "registro-1",
        "cp": "3260",
    }

    server._handle_client(
        conn,
        ("127.0.0.1", 50000),
    )

    assert conn.sendall.called

    conn.close.assert_called_once()


def test_handle_client_subscribe_no_cierra_socket(
    server,
    data,
    publisher,
):
    """
    Verifica que subscribe deje la conexión abierta.
    """

    conn = Mock()

    request = b'{"UUID":"uuid-123","ACTION":"subscribe"}\n'

    conn.recv.return_value = request

    server._handle_client(
        conn,
        ("127.0.0.1", 50000),
    )

    publisher.subscribe.assert_called_once()

    # El socket queda abierto porque será utilizado por
    # ClientObserver para enviar futuras notificaciones.
    conn.close.assert_not_called()


def test_handle_client_json_invalido_envia_error(
    server,
):
    """
    Verifica el manejo de JSON inválido.
    """

    conn = Mock()

    conn.recv.return_value = b"{JSON INVALIDO}\n"

    server._handle_client(
        conn,
        ("127.0.0.1", 50000),
    )

    assert conn.sendall.called

    sent_data = conn.sendall.call_args.args[0]

    response = json.loads(sent_data.decode("utf-8"))

    assert "Error" in response

    conn.close.assert_called_once()


def test_handle_client_request_invalido_envia_error(
    server,
):
    """
    Verifica que una petición JSON válida pero con campos incorrectos
    también sea rechazada.
    """

    conn = Mock()

    conn.recv.return_value = b'{"UUID":"uuid-123","ACTION":"delete"}\n'

    server._handle_client(
        conn,
        ("127.0.0.1", 50000),
    )

    assert conn.sendall.called

    sent_data = conn.sendall.call_args.args[0]

    response = json.loads(sent_data.decode("utf-8"))

    assert response["Error"] == "Petición inválida."

    conn.close.assert_called_once()
