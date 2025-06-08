from datetime import datetime, timedelta

import pytest
from faker import Faker
from httpx import AsyncClient

from app.models.gas_monitor import GasConsumptionRecord


@pytest.mark.asyncio
async def test_ingest_gas_consumption_record(client: AsyncClient, create_gas_record, faker_instance: Faker):
    """Test successful ingestion of a gas consumption record."""
    record = await create_gas_record(entity_id=faker_instance.uuid4())
    assert record.transaction_hash is not None
    assert record.id is not None


@pytest.mark.asyncio
async def test_get_records_for_entity(client: AsyncClient, create_gas_record, faker_instance: Faker):
    """Test retrieving gas consumption records for a specific entity."""
    entity_id = faker_instance.uuid4()
    for i in range(3):
        await create_gas_record(entity_id=entity_id, timestamp=datetime.utcnow() - timedelta(minutes=i))

    response = await client.get(f"/gasmonitor/records/{entity_id}")
    assert response.status_code == 200
    records = response.json()
    assert len(records) == 3
    assert all(r["entity_id"] == entity_id for r in records)
    assert records[0]["timestamp"] > records[1]["timestamp"]


@pytest.mark.asyncio
async def test_get_records_for_entity_pagination(client: AsyncClient, create_gas_record, faker_instance: Faker):
    """Test pagination for retrieving gas consumption records."""
    entity_id = faker_instance.uuid4()
    for i in range(10):
        await create_gas_record(entity_id=entity_id, timestamp=datetime.utcnow() - timedelta(minutes=i))

    response_limit_3 = await client.get(f"/gasmonitor/records/{entity_id}?limit=3")
    assert response_limit_3.status_code == 200
    assert len(response_limit_3.json()) == 3

    response_skip_5 = await client.get(f"/gasmonitor/records/{entity_id}?skip=5&limit=3")
    assert response_skip_5.status_code == 200
    assert len(response_skip_5.json()) == 3

    full_list_response = await client.get(f"/gasmonitor/records/{entity_id}?limit=10")
    full_list = full_list_response.json()
    assert response_skip_5.json()[0]["transaction_hash"] == full_list[5]["transaction_hash"]


@pytest.mark.asyncio
async def test_analyze_gas_patterns_no_records_found(client: AsyncClient, faker_instance: Faker):
    """Test analysis for an entity with no records."""
    non_existent_entity_id = faker_instance.uuid4()
    response = await client.post(f"/gasmonitor/analyze/{non_existent_entity_id}", json={"lookBackDays": 7})
    assert response.status_code == 404
    assert "No gas consumption records found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_analyze_gas_patterns_detect_high_spike(client: AsyncClient, create_gas_record, faker_instance: Faker):
    """Test analysis detecting a high gas spike."""
    entity_id = faker_instance.uuid4()
    for i in range(5):
        await create_gas_record(entity_id=entity_id, gas_used=faker_instance.random_int(min=50000, max=100000), timestamp=datetime.utcnow() - timedelta(hours=i))
    spike_record = await create_gas_record(entity_id=entity_id, gas_used=5000000, timestamp=datetime.utcnow() - timedelta(minutes=1))

    response = await client.post(f"/gasmonitor/analyze/{entity_id}", json={"lookBackDays": 7})
    assert response.status_code == 200
    analysis_result = response.json()
    assert analysis_result["total_transactions_analyzed"] == 6
    assert len(analysis_result["anomalies"]) >= 1
    assert any(a["anomaly_type"] == "high_gas_spike" for a in analysis_result["anomalies"])
    assert analysis_result["anomalies"][0]["transactions_involved"][0] == spike_record.transaction_hash
    assert analysis_result["summary_message"].startswith(f"Analysis for entity '{entity_id}'")
    assert "Detected 1 potential anomalies." in analysis_result["summary_message"]


@pytest.mark.asyncio
async def test_analyze_gas_patterns_no_anomaly(client: AsyncClient, create_gas_record, faker_instance: Faker):
    """Test analysis with no anomalies detected."""
    entity_id = faker_instance.uuid4()
    for _ in range(5):
        await create_gas_record(entity_id=entity_id, gas_used=faker_instance.random_int(min=50000, max=70000))

    response = await client.post(f"/gasmonitor/analyze/{entity_id}", json={"lookBackDays": 7})
    assert response.status_code == 200
    analysis_result = response.json()
    assert len(analysis_result["anomalies"]) == 0
    assert "No significant anomalies detected" in analysis_result["summary_message"]
