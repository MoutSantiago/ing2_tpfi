import threading
from typing import Any

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from SingletonProxyObserverTPFI.app.exceptions import (
    DataAccessError,
    RecordNotFoundError,
)
from SingletonProxyObserverTPFI.app.proxy.corporate_data_interface import (
    CorporateDataInterface,
)
from SingletonProxyObserverTPFI.app.singleton.corporate_data_dao import (
    CorporateDataDAO,
)

REGISTRO = {
    "id": "UADER-FCyT-IS2",
    "cp": "3260",
    "CUIT": "30-70925411-8",
    "domicilio": "25 de Mayo 385-1P",
    "idreq": "473",
    "idSeq": "1146",
    "localidad": "Concepción del Uruguay",
    "provincia": "Entre Rios",
    "sede": "FCyT",
    "seqID": "23",
    "telefono": "03442 43-1442",
    "web": "http://www.uader.edu.ar",
}


def crear_tabla(nombre: str = "CorporateData") -> None:
    """Crea una tabla mock en DynamoDB usando moto."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    dynamodb.create_table(
        TableName=nombre,
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )


def tabla() -> Any:
    """Devuelve el recurso Table de la tabla CorporateData mock."""
    return boto3.resource("dynamodb", region_name="us-east-1").Table(
        "CorporateData"
    )


@pytest.fixture(autouse=True)
def reset_singleton():
    """Resetea el singleton antes y después de cada test."""
    CorporateDataDAO._instance = None
    yield
    CorporateDataDAO._instance = None


@mock_aws
def crear_dao() -> CorporateDataDAO:
    """Devuelve un DAO conectado a una tabla CorporateData mock."""
    try:
        crear_tabla()
    except Exception:  # noqa: BLE001 - la tabla puede ya existir
        pass
    return CorporateDataDAO()


# =============================================================================
# Tests de Singleton
# =============================================================================


@mock_aws
def test_get_instance_retorna_misma_instancia():
    """Verifica que get_instance() siempre retorne la misma instancia."""
    crear_tabla()
    dao1 = CorporateDataDAO.get_instance()
    dao2 = CorporateDataDAO.get_instance()
    assert dao1 is dao2


def test_constructor_directo_lanza_error():
    """Verifica que el constructor directo de una instancia ya existente
    lance RuntimeError."""
    with mock_aws():
        crear_tabla()
        CorporateDataDAO.get_instance()
        with pytest.raises(RuntimeError) as exc_info:
            CorporateDataDAO()
        assert "No instanciar directamente" in str(exc_info.value)


def test_constructor_lanza_data_access_error_si_tabla_no_existe():
    """Verifica que el constructor envuelva en DataAccessError la falta de
    la tabla (moto genera un ClientError)."""
    with mock_aws():
        with pytest.raises(DataAccessError) as exc_info:
            CorporateDataDAO()
        assert "CorporateData" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, ClientError)


def test_get_instance_lanza_data_access_error_si_falla_init():
    """Verifica que get_instance propague el DataAccessError del
    constructor."""
    with mock_aws():
        with pytest.raises(DataAccessError):
            CorporateDataDAO.get_instance()


def test_get_instance_thread_safety():
    """Verifica que get_instance sea thread-safe bajo concurrencia."""
    with mock_aws():
        crear_tabla()
        resultados: list[CorporateDataDAO] = []
        errores: list[Exception] = []

        def obtener() -> None:
            try:
                resultados.append(CorporateDataDAO.get_instance())
            except Exception as e:  # noqa: BLE001
                errores.append(e)

        hilos = [threading.Thread(target=obtener) for _ in range(10)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()

        assert not errores
        assert len(resultados) == 10
        # Todas las llamadas deben devolver la misma instancia.
        assert all(r is resultados[0] for r in resultados)


# =============================================================================
# Tests del contrato con la interfaz
# =============================================================================


def test_implementa_corporate_data_interface():
    """Verifica que CorporateDataDAO implemente el contrato de la interfaz."""
    with mock_aws():
        dao = crear_dao()
        assert isinstance(dao, CorporateDataInterface)
        assert not dao.__abstractmethods__


# =============================================================================
# Tests de get
# =============================================================================


def test_get_retorna_registro():
    """Verifica que get devuelva el registro con la clave solicitada."""
    with mock_aws():
        crear_tabla()
        tabla().put_item(Item=REGISTRO)
        dao = crear_dao()

        resultado = dao.get("UADER-FCyT-IS2", "uuid-cliente")

        assert resultado == REGISTRO


def test_get_lanza_record_not_found():
    """Verifica que get lance RecordNotFoundError cuando el registro no
    existe, y que esa excepción sea a su vez una DataAccessError."""
    with mock_aws():
        dao = crear_dao()

        with pytest.raises(RecordNotFoundError) as exc_info:
            dao.get("no-existe", "uuid-cliente")

        assert "no-existe" in str(exc_info.value)
        assert isinstance(exc_info.value, DataAccessError)


def test_get_convierte_numeros_a_texto():
    """Verifica que los valores numéricos (Decimal en DynamoDB) se entreguen
    como strings, respetando el dict[str, str] del contrato."""
    with mock_aws():
        crear_tabla()
        tabla().put_item(Item={"id": "con-numeros", "idreq": 473, "seqID": 23})
        dao = crear_dao()

        resultado = dao.get("con-numeros", "uuid-cliente")

        assert resultado["idreq"] == "473"
        assert resultado["seqID"] == "23"
        assert all(isinstance(v, str) for v in resultado.values())


def test_get_lanza_data_access_error_si_falla_tabla():
    """Verifica que un error de DynamoDB se traduzca a DataAccessError
    conservando la causa original, sin exponer boto3 a las capas altas."""
    with mock_aws():
        dao = crear_dao()
        # Borrar la tabla para provocar un ClientError en la operación.
        boto3.resource("dynamodb", region_name="us-east-1").Table(
            "CorporateData"
        ).delete()

        with pytest.raises(DataAccessError) as exc_info:
            dao.get("UADER-FCyT-IS2", "uuid-cliente")

        assert "Error leyendo de CorporateData" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, ClientError)


# =============================================================================
# Tests de set
# =============================================================================


def test_set_crea_registro_nuevo():
    """Verifica que set cree un registro inexistente con los campos
    informados."""
    with mock_aws():
        dao = crear_dao()

        resultado = dao.set("nuevo", {"CUIT": "30-70925411-8"}, "uuid-cliente")

        assert resultado["id"] == "nuevo"
        assert resultado["CUIT"] == "30-70925411-8"


def test_set_registro_nuevo_campos_no_informados_en_blanco():
    """Verifica que al crear un registro, los campos no informados queden en
    blanco, como indica el enunciado."""
    with mock_aws():
        dao = crear_dao()

        resultado = dao.set("nuevo", {"CUIT": "30-70925411-8"}, "uuid")

        assert resultado["sede"] == ""
        assert resultado["web"] == ""
        assert resultado["localidad"] == ""


def test_set_modifica_solo_campos_informados():
    """Verifica que set modifique solo los campos informados y conserve el
    resto del registro existente."""
    with mock_aws():
        crear_tabla()
        tabla().put_item(Item=REGISTRO)
        dao = crear_dao()

        resultado = dao.set("UADER-FCyT-IS2", {"web": "http://nuevo"}, "uuid")

        assert resultado["web"] == "http://nuevo"
        assert resultado["CUIT"] == "30-70925411-8"
        assert resultado["sede"] == "FCyT"


def test_set_retorna_registro_resultante():
    """Verifica que set devuelva el registro tal como queda en la base."""
    with mock_aws():
        dao = crear_dao()

        resultado = dao.set("r1", {"sede": "FCyT"}, "uuid")

        assert resultado["id"] == "r1"
        assert resultado["sede"] == "FCyT"


def test_set_lanza_data_access_error_si_falla_tabla():
    """Verifica que un error de DynamoDB al escribir se traduzca a
    DataAccessError."""
    with mock_aws():
        dao = crear_dao()
        boto3.resource("dynamodb", region_name="us-east-1").Table(
            "CorporateData"
        ).delete()

        with pytest.raises(DataAccessError) as exc_info:
            dao.set("r1", {"sede": "FCyT"}, "uuid")

        assert "Error escribiendo en CorporateData" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, ClientError)


# =============================================================================
# Tests de list
# =============================================================================


def test_list_retorna_todos_los_registros():
    """Verifica que list devuelva todos los registros de la tabla."""
    with mock_aws():
        crear_tabla()
        tabla().put_item(Item=REGISTRO)
        tabla().put_item(Item={"id": "segundo", "sede": "FCyT"})
        dao = crear_dao()

        resultado = dao.list("uuid")

        ids = {r["id"] for r in resultado}
        assert ids == {"UADER-FCyT-IS2", "segundo"}


def test_list_tabla_vacia_devuelve_lista_vacia():
    """Verifica que list sobre una tabla vacía devuelva una lista vacía."""
    with mock_aws():
        dao = crear_dao()
        assert dao.list("uuid") == []


def test_list_recorre_paginas():
    """Verifica que list recorra todas las páginas que devuelve DynamoDB.

    Con moto, cada scan devuelve un solo item sin paginar; para forzar la
    paginación se pide un tamaño de página de 1, que devuelve 3 páginas con
    3 registros. El resultado debe contener los 3.
    """
    with mock_aws():
        crear_tabla()
        for i in range(3):
            tabla().put_item(Item={"id": f"registro-{i}"})
        dao = crear_dao()

        # Forzar paginación llamando directamente al scan con límite 1.
        pagina = dao._table.scan(Limit=1)
        assert "LastEvaluatedKey" in pagina

        resultado = dao.list("uuid")

        assert len(resultado) == 3


def test_list_convierte_numeros_a_texto():
    """Verifica que list también normalice los valores numéricos."""
    with mock_aws():
        crear_tabla()
        tabla().put_item(Item={"id": "x", "idreq": 473})
        dao = crear_dao()

        resultado = dao.list("uuid")

        assert resultado[0]["idreq"] == "473"
        assert all(isinstance(v, str) for r in resultado for v in r.values())


def test_list_lanza_data_access_error_si_falla_tabla():
    """Verifica que un error de DynamoDB al listar se traduzca a
    DataAccessError."""
    with mock_aws():
        dao = crear_dao()
        boto3.resource("dynamodb", region_name="us-east-1").Table(
            "CorporateData"
        ).delete()

        with pytest.raises(DataAccessError) as exc_info:
            dao.list("uuid")

        assert "Error listando CorporateData" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, ClientError)
