import threading

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from SingletonProxyObserverTPFI.app.singleton.corporate_log_dao import (
    CorporateLogDAO,
    DataAccessError,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def reset_singleton():
    """Resetea el singleton antes y después de cada test."""
    CorporateLogDAO._instance = None
    yield
    CorporateLogDAO._instance = None


@pytest.fixture
def dynamodb_table():
    """Crea una tabla CorporateLog mock en DynamoDB usando moto."""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        # Crear tabla CorporateLog
        table = dynamodb.create_table(
            TableName="CorporateLog",
            KeySchema=[
                {"AttributeName": "id", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        yield table


# Fixture para tests de singleton que necesitan DynamoDB mock
@pytest.fixture
def mock_dynamodb():
    """Provee un contexto mock_aws para tests de singleton básicos."""
    with mock_aws():
        # Crear tabla CorporateLog por defecto
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName="CorporateLog",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        yield


# =============================================================================
# Tests de Singleton
# =============================================================================


@mock_aws
def test_misma_instancia():
    """Verifica que dos llamadas a get_instance devuelven la misma
    instancia."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    dynamodb.create_table(
        TableName="CorporateLog",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    assert CorporateLogDAO.get_instance() is CorporateLogDAO.get_instance()


@mock_aws
def test_get_instance_retorna_misma_instancia():
    """Verifica que get_instance() siempre retorna la misma instancia."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    dynamodb.create_table(
        TableName="CorporateLog",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    dao1 = CorporateLogDAO.get_instance()
    dao2 = CorporateLogDAO.get_instance()
    assert dao1 is dao2


@mock_aws
def test_get_instance_crea_instancia_si_no_existe():
    """Verifica que get_instance() crea la instancia si no existe."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    dynamodb.create_table(
        TableName="CorporateLog",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    CorporateLogDAO._instance = None
    dao = CorporateLogDAO.get_instance()
    assert dao is not None
    assert isinstance(dao, CorporateLogDAO)


@mock_aws
def test_constructor_directo_lanza_error():
    """Verifica que llamar al constructor directamente lanza RuntimeError."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    dynamodb.create_table(
        TableName="CorporateLog",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    # Primera vez via get_instance
    CorporateLogDAO.get_instance()
    # Segunda vez directa debe fallar
    with pytest.raises(RuntimeError) as exc_info:
        CorporateLogDAO()
    assert "No instanciar directamente" in str(exc_info.value)


@mock_aws
def test_clases_distintas_no_comparten():
    """Verifica que subclases tienen su propio singleton."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    dynamodb.create_table(
        TableName="CorporateLog",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    class Otra(CorporateLogDAO):
        pass

    # Cada clase tiene su propio _instance
    assert Otra.get_instance() is not CorporateLogDAO.get_instance()
    assert Otra.get_instance() is Otra.get_instance()


# =============================================================================
# Tests de Inicialización y Conexión
# =============================================================================


@mock_aws
def test_init_conecta_a_dynamodb(dynamodb_table):
    """Verifica que __init__ se conecta correctamente a DynamoDB."""
    dao = CorporateLogDAO()
    assert dao._table is not None
    assert dao._table.name == "CorporateLog"


@mock_aws
def test_init_verifica_table_status(dynamodb_table):
    """Verifica que __init__ verifica el estado de la tabla."""
    dao = CorporateLogDAO()
    # Si llega aquí, table_status se accedió sin error
    assert dao._table.table_status == "ACTIVE"


@mock_aws
def test_init_falla_si_tabla_no_existe():
    """Verifica que __init__ lanza DataAccessError si la tabla no existe."""
    # No creamos la tabla, solo usamos moto sin tabla CorporateLog
    with pytest.raises(DataAccessError) as exc_info:
        CorporateLogDAO()
    assert "CorporateLog" in str(exc_info.value)


# =============================================================================
# Tests de write_entry
# =============================================================================


@mock_aws
def test_write_entry_inserta_registro_basico(dynamodb_table):
    """Verifica que write_entry inserta un registro con todos los campos."""
    dao = CorporateLogDAO()

    dao.write_entry(
        uuid="client-123",
        session_id="session-456",
        action="get",
        item_id="item-789",
        timestamp="2025-01-15 10:30:00",
    )

    # Verificar que el item se escribió
    response = dynamodb_table.get_item(Key={"id": "client-123"})
    item = response["Item"]

    assert item["id"] == "client-123"
    assert item["CPUid"] == "client-123"
    assert item["sessionid"] == "session-456"
    assert item["timestamp"] == "2025-01-15 10:30:00"
    assert item["action"] == "get"
    assert item["item_id"] == "item-789"


@mock_aws
def test_write_entry_sin_item_id_para_list(dynamodb_table):
    """Verifica que write_entry omite item_id cuando es None
    (list/subscribe)."""
    dao = CorporateLogDAO()

    dao.write_entry(
        uuid="client-123",
        session_id="session-456",
        action="list",
        item_id=None,
        timestamp="2025-01-15 10:30:00",
    )

    response = dynamodb_table.get_item(Key={"id": "client-123"})
    item = response["Item"]

    assert "item_id" not in item
    assert item["action"] == "list"


@mock_aws
def test_write_entry_sin_item_id_para_subscribe(dynamodb_table):
    """Verifica que write_entry omite item_id para subscribe."""
    dao = CorporateLogDAO()

    dao.write_entry(
        uuid="client-123",
        session_id="session-456",
        action="subscribe",
        item_id=None,
        timestamp="2025-01-15 10:30:00",
    )

    response = dynamodb_table.get_item(Key={"id": "client-123"})
    item = response["Item"]

    assert "item_id" not in item
    assert item["action"] == "subscribe"


@mock_aws
def test_write_entry_con_item_id_para_set(dynamodb_table):
    """Verifica que write_entry incluye item_id para set."""
    dao = CorporateLogDAO()

    dao.write_entry(
        uuid="client-123",
        session_id="session-456",
        action="set",
        item_id="item-789",
        timestamp="2025-01-15 10:30:00",
    )

    response = dynamodb_table.get_item(Key={"id": "client-123"})
    item = response["Item"]

    assert item["item_id"] == "item-789"
    assert item["action"] == "set"


@mock_aws
def test_write_entry_multiples_registros(dynamodb_table):
    """Verifica que se pueden insertar múltiples registros con diferentes
    UUIDs."""
    dao = CorporateLogDAO()

    dao.write_entry("uuid-1", "sess-1", "get", "item-1", "2025-01-15 10:00:00")
    dao.write_entry("uuid-2", "sess-2", "set", "item-2", "2025-01-15 10:01:00")
    dao.write_entry("uuid-3", "sess-3", "list", None, "2025-01-15 10:02:00")

    # Verificar los 3 registros
    for i in range(1, 4):
        response = dynamodb_table.get_item(Key={"id": f"uuid-{i}"})
        assert "Item" in response
        assert response["Item"]["action"] in ("get", "set", "list")


@mock_aws
def test_write_entry_no_retorna_valor(dynamodb_table):
    """Verifica que write_entry retorna None."""
    dao = CorporateLogDAO()

    result = dao.write_entry(
        uuid="client-123",
        session_id="session-456",
        action="get",
        item_id="item-789",
        timestamp="2025-01-15 10:30:00",
    )

    assert result is None


# =============================================================================
# Tests de Manejo de Errores
# =============================================================================


@mock_aws
def test_write_entry_lanza_dataaccesserror_si_falla_put_item(dynamodb_table):
    """Verifica que write_entry envuelve ClientError en DataAccessError."""
    dao = CorporateLogDAO()

    # Borrar la tabla para simular error
    dynamodb_table.delete()

    with pytest.raises(DataAccessError) as exc_info:
        dao.write_entry(
            uuid="client-123",
            session_id="session-456",
            action="get",
            item_id="item-789",
            timestamp="2025-01-15 10:30:00",
        )

    assert "Error escribiendo en CorporateLog" in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, ClientError)


@mock_aws
def test_get_instance_lanza_dataaccesserror_si_falla_init():
    """Verifica que get_instance propaga DataAccessError del constructor."""
    CorporateLogDAO._instance = None

    # Sin tabla CorporateLog, el init fallará
    with pytest.raises(DataAccessError) as exc_info:
        CorporateLogDAO.get_instance()

    assert "CorporateLogDAO" in str(exc_info.value) or "CorporateLog" in str(
        exc_info.value
    )


# =============================================================================
# Tests de Thread Safety (básicos)
# =============================================================================


@mock_aws
def test_get_instance_thread_safety(dynamodb_table):
    """Verifica que get_instance es thread-safe (básico)."""
    results = []
    errors = []

    def get_dao():
        try:
            dao = CorporateLogDAO.get_instance()
            results.append(dao)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=get_dao) for _ in range(10)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert len(results) == 10
    # Todas deben ser la misma instancia
    assert all(r is results[0] for r in results)


@mock_aws
def test_write_entry_concurrente(dynamodb_table):
    """Verifica que write_entry maneja escrituras concurrentes."""
    dao = CorporateLogDAO()
    errors = []

    def write_log(i):
        try:
            dao.write_entry(
                uuid=f"client-{i}",
                session_id=f"session-{i}",
                action="get",
                item_id=f"item-{i}",
                timestamp=f"2025-01-15 10:{i:02d}:00",
            )
        except Exception as e:
            errors.append(e)

    threads = [
        threading.Thread(target=write_log, args=(i,)) for i in range(20)
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0

    # Verificar que se escribieron los 20 items
    response = dynamodb_table.scan()
    assert response["Count"] == 20
