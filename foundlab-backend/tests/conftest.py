import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, List

import pytest
import pytest_asyncio
from faker import Faker
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo_inmemory import MongoClient as InMemoryMongoClient

from app.main import app
from app.models.dfc import FlagDefinition, FlagType, Rule, RuleCondition
from app.models.gas_monitor import GasConsumptionRecord
from app.models.risk import RiskLevel, RiskTrigger
from app.models.score import FlagWithValue, ScoreResult
from app.models.sherlock import SherlockValidationResult


@pytest_asyncio.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def mongo_client_fixture() -> AsyncGenerator[AsyncIOMotorClient, None]:
    """
    Fixture for an in-memory MongoDB client for testing.
    This creates a real MongoDB process in memory.
    """
    client = InMemoryMongoClient()
    motor_client = AsyncIOMotorClient(client.connection_string)

    from app import database
    database.client = motor_client

    print("--- Starting in-memory MongoDB for tests ---")
    yield motor_client
    print("--- Stopping in-memory MongoDB ---")
    motor_client.close()
    client.close()


@pytest_asyncio.fixture(autouse=True)
async def clear_database(mongo_client_fixture: AsyncIOMotorClient):
    """
    Clears all collections in the test database before each test.
    Ensures test isolation.
    """
    db = mongo_client_fixture["foundlab_db"]
    for collection_name in await db.list_collection_names():
        if collection_name.startswith("system."):
            continue
        await db.drop_collection(collection_name)
    print(f"Cleared database: {db.name}")

    from app.services.score_service import ScoreLabService
    from app.services.dfc_service import DFCService
    from app.services.sherlock_service import SherlockService
    from app.services.nft_service import SigilMeshService
    from app.services.risk_service import SentinelaService
    from app.services.gas_monitor_service import GasMonitorService

    import app.routers.dfc_router as dfc_router_module
    import app.routers.score_router as score_router_module
    import app.routers.sherlock_router as sherlock_router_module
    import app.routers.nft_router as nft_router_module
    import app.routers.risk_router as risk_router_module
    import app.routers.gas_monitor_router as gas_monitor_router_module

    dfc_router_module.dfc_service = DFCService()
    score_router_module.score_service = ScoreLabService()
    sherlock_router_module.sherlock_service = SherlockService()
    nft_router_module.sigilmesh_service = SigilMeshService()
    risk_router_module.sentinela_service = SentinelaService()
    gas_monitor_router_module.gas_monitor_service = GasMonitorService()


@pytest_asyncio.fixture(scope="session")
async def client(mongo_client_fixture: AsyncIOMotorClient) -> AsyncGenerator[AsyncClient, None]:
    async with app.lifespan_context():
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac


@pytest.fixture(scope="session")
def faker_instance():
    return Faker()


@pytest_asyncio.fixture
async def create_flag_definition(client: AsyncClient, faker_instance: Faker):
    async def _create_flag(
        name: str = None,
        description: str = None,
        flag_type: FlagType = FlagType.BOOLEAN,
        default_value: Any = False,
        rules: List[Dict[str, Any]] = None,
        weight: float = 0.0,
        category: str = None,
    ) -> FlagDefinition:
        flag_data = {
            "name": name if name else faker_instance.word() + "_flag_" + faker_instance.uuid4()[:4],
            "description": description if description else faker_instance.sentence(),
            "type": flag_type.value,
            "default_value": default_value,
            "rules": rules if rules is not None else [],
            "weight": weight,
            "category": category if category else faker_instance.word(),
        }
        response = await client.post("/flags/definitions", json=flag_data)
        assert response.status_code == 201, response.text
        return FlagDefinition(**response.json())
    return _create_flag


@pytest_asyncio.fixture
async def create_score_result(client: AsyncClient, faker_instance: Faker):
    async def _create_score(
        entity_id: str = None,
        flags: List[FlagWithValue] = None,
        metadata: Dict[str, Any] = None,
    ) -> ScoreResult:
        score_input_data = {
            "entity_id": entity_id if entity_id else faker_instance.uuid4(),
            "flags": [f.model_dump() for f in (flags if flags is not None else [])],
            "metadata": metadata if metadata else {},
        }
        response = await client.post("/scores", json=score_input_data)
        assert response.status_code == 201, response.text
        return ScoreResult(**response.json())
    return _create_score


@pytest_asyncio.fixture
async def create_risk_trigger(client: AsyncClient, faker_instance: Faker):
    async def _create_trigger(
        name: str = None,
        description: str = None,
        trigger_type: str = "score_threshold",
        score_threshold: float = None,
        flag_name: str = None,
        custom_logic_params: Dict[str, Any] = None,
        risk_level: RiskLevel = RiskLevel.HIGH,
        is_active: bool = True,
    ) -> RiskTrigger:
        trigger_data = {
            "name": name if name else faker_instance.word() + "_trigger_" + faker_instance.uuid4()[:4],
            "description": description if description else faker_instance.sentence(),
            "trigger_type": trigger_type,
            "score_threshold": score_threshold,
            "flag_name": flag_name,
            "custom_logic_params": custom_logic_params,
            "risk_level": risk_level.value,
            "is_active": is_active,
        }
        response = await client.post("/sentinela/triggers", json=trigger_data)
        assert response.status_code == 201, response.text
        return RiskTrigger(**response.json())
    return _create_trigger


@pytest_asyncio.fixture
async def create_sherlock_validation_result(client: AsyncClient, faker_instance: Faker):
    async def _create_sherlock_result(
        entity_id: str = None,
        entity_type: str = "wallet_address"
    ) -> SherlockValidationResult:
        validation_input_data = {
            "entity_id": entity_id if entity_id else faker_instance.uuid4(),
            "entity_type": entity_type,
        }
        response = await client.post("/sherlock/validate", json=validation_input_data)
        assert response.status_code == 200, response.text
        return SherlockValidationResult(**response.json())
    return _create_sherlock_result


@pytest_asyncio.fixture
async def create_gas_record(client: AsyncClient, faker_instance: Faker):
    async def _create_gas_record(
        entity_id: str = None,
        gas_used: int = None,
        timestamp: datetime = None
    ) -> GasConsumptionRecord:
        record_data = {
            "transaction_hash": faker_instance.sha256(),
            "entity_id": entity_id if entity_id else faker_instance.uuid4(),
            "gas_used": gas_used if gas_used else faker_instance.random_int(min=21000, max=500000),
            "gas_price_gwei": faker_instance.random_int(min=10, max=100),
            "block_number": faker_instance.random_int(min=100000, max=90000000),
            "timestamp": (timestamp if timestamp else datetime.utcnow()).isoformat(),
            "chain_id": 1,
            "transaction_type": "ERC20_Transfer"
        }
        response = await client.post("/gasmonitor/ingest", json=record_data)
        assert response.status_code == 201, response.text
        return GasConsumptionRecord(**response.json())
    return _create_gas_record
