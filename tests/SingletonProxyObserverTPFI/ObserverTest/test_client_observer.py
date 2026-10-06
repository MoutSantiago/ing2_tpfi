"""
Tests unitarios para client_observer.py.
"""

import json
from unittest.mock import Mock

import pytest

from SingletonProxyObserverTPFI.app.observer.client_observer import (
    ClientObserver,
)
from SingletonProxyObserverTPFI.app.observer.observer import (
    Observer,
    ObserverUnavailableError,
)


def test_client_observer_implementa_observer():
    """
    Verifica que ClientObserver sea una implementación concreta
    de la interfaz Observer.
    """

    sock = Mock()

    observer = ClientObserver(
        sock,
        "uuid-123",
    )

    assert isinstance(observer, Observer)


def test_constructor_guarda_socket_y_uuid():
    """
    Verifica que el constructor almacene correctamente sus
    dependencias internas.
    """

    sock = Mock()

    observer = ClientObserver(
        sock,
        "uuid-123",
    )

    assert observer._sock is sock
    assert observer.uuid == "uuid-123"


def test_uuid_es_solo_lectura():
    """
    Verifica que uuid sea una propiedad de solo lectura.
    """

    observer = ClientObserver(
        Mock(),
        "uuid-123",
    )

    with pytest.raises(AttributeError):
        # El error de asignación es intencional: el test verifica que
        # la propiedad sea de solo lectura.
        observer.uuid = "otro-uuid"  # pyright: ignore[reportAttributeAccessIssue]


def test_update_serializa_y_envia_json():
    """
    Verifica que update() transforme el mensaje a JSON y lo envíe
    mediante el socket.
    """

    sock = Mock()

    observer = ClientObserver(
        sock,
        "uuid-123",
    )

    message = {
        "UUID": "uuid-123",
        "ID": "registro-1",
        "ACTION": "change",
        "cp": "3260",
    }

    observer.update(message)

    sock.sendall.assert_called_once()

    # Recuperamos exactamente lo que se envió.
    sent_data = sock.sendall.call_args.args[0]

    # Debe enviarse como bytes.
    assert isinstance(sent_data, bytes)

    # Convertimos nuevamente a texto.
    sent_text = sent_data.decode("utf-8")

    # Debe terminar en newline porque el protocolo utiliza
    # una línea por mensaje.
    assert sent_text.endswith("\n")

    # Eliminamos el newline y volvemos a interpretar el JSON.
    received_message = json.loads(sent_text)

    assert received_message == message


def test_update_lanza_observer_unavailable_si_socket_falla():
    """
    Verifica que un error de socket sea transformado en
    ObserverUnavailableError.
    """

    sock = Mock()

    sock.sendall.side_effect = OSError("socket cerrado")

    observer = ClientObserver(
        sock,
        "uuid-123",
    )

    message = {
        "UUID": "uuid-123",
        "ACTION": "change",
    }

    with pytest.raises(ObserverUnavailableError):
        observer.update(message)


def test_update_lanza_observer_unavailable_si_json_no_es_serializable():
    """
    Verifica el manejo de un mensaje que json.dumps() no puede
    serializar.
    """

    sock = Mock()

    observer = ClientObserver(
        sock,
        "uuid-123",
    )

    # object() no puede serializarse mediante json.dumps().
    message = {
        "invalid": object(),
    }

    with pytest.raises(ObserverUnavailableError):
        observer.update(message)

    sock.sendall.assert_not_called()


def test_close_cierra_socket():
    """
    Verifica que close() cierre el socket del cliente.
    """

    sock = Mock()

    observer = ClientObserver(
        sock,
        "uuid-123",
    )

    observer.close()

    sock.close.assert_called_once()


def test_close_no_falla_si_socket_ya_esta_cerrado():
    """
    Verifica que close() no propague OSError si el socket ya estaba
    cerrado.
    """

    sock = Mock()

    sock.close.side_effect = OSError("socket already closed")

    observer = ClientObserver(
        sock,
        "uuid-123",
    )

    # No debe lanzar excepción.
    observer.close()
