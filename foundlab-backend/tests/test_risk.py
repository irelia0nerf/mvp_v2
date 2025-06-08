import pytest
from httpx import AsyncClient

from app.models.risk import RiskLevel, RiskTrigger
from app.models.score import ScoreResult, FlagWithValue


@pytest.mark.asyncio
async def test_create_risk_trigger(client: AsyncClient, create_risk_trigger):
    trigger = await create_risk_trigger(name="low_score_warning", score_threshold=0.3, risk_level=RiskLevel.MEDIUM)
    assert trigger.name == "low_score_warning"
    assert trigger.risk_level == RiskLevel.MEDIUM


@pytest.mark.asyncio
async def test_create_risk_trigger_duplicate(client: AsyncClient, create_risk_trigger):
    await create_risk_trigger(name="duplicate_trigger_risk_test")
    response = await client.post("/sentinela/triggers", json={
        "name": "duplicate_trigger_risk_test",
        "description": "Duplicate test",
        "trigger_type": "score_threshold",
        "score_threshold": 0.1,
        "risk_level": "CRITICAL",
    })
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_all_risk_triggers(client: AsyncClient, create_risk_trigger):
    await create_risk_trigger(name="active_trigger_1", is_active=True)
    await create_risk_trigger(name="inactive_trigger_1", is_active=False)
    response = await client.get("/sentinela/triggers")
    assert response.status_code == 200
    assert any(t["name"] == "active_trigger_1" for t in response.json())
    assert not any(t["name"] == "inactive_trigger_1" for t in response.json())


@pytest.mark.asyncio
async def test_get_risk_trigger_by_name(client: AsyncClient, create_risk_trigger):
    trigger = await create_risk_trigger(name="get_by_name_trigger")
    response = await client.get(f"/sentinela/triggers/{trigger.name}")
    assert response.status_code == 200
    assert response.json()["name"] == trigger.name


@pytest.mark.asyncio
async def test_get_risk_trigger_by_name_not_found(client: AsyncClient):
    response = await client.get("/sentinela/triggers/nonexistent_trigger")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_risk_trigger(client: AsyncClient, create_risk_trigger):
    trigger = await create_risk_trigger(name="update_trigger")
    update_data = {"description": "Updated description for risk trigger.", "is_active": False}
    response = await client.put(f"/sentinela/triggers/{trigger.name}", json=update_data)
    assert response.status_code == 200
    assert response.json()["description"] == "Updated description for risk trigger."
    assert response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_update_risk_trigger_no_changes(client: AsyncClient, create_risk_trigger):
    trigger = await create_risk_trigger(name="no_change_risk_trigger", description="OriginalDesc", is_active=True)
    update_data = {"description": "OriginalDesc", "is_active": True}
    response = await client.put(f"/sentinela/triggers/{trigger.name}", json=update_data)
    assert response.status_code == 200
    assert response.json()["description"] == "OriginalDesc"


@pytest.mark.asyncio
async def test_update_risk_trigger_not_found(client: AsyncClient):
    response = await client.put("/sentinela/triggers/nonexistent_trigger", json={"description": "Updated description."})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_risk_trigger(client: AsyncClient, create_risk_trigger):
    trigger = await create_risk_trigger(name="delete_risk_trigger")
    response = await client.delete(f"/sentinela/triggers/{trigger.name}")
    assert response.status_code == 204
    response = await client.get(f"/sentinela/triggers/{trigger.name}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_risk_trigger_not_found(client: AsyncClient):
    response = await client.delete("/sentinela/triggers/nonexistent_trigger")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_assess_risk_score_threshold_triggered(client: AsyncClient, create_score_result, create_risk_trigger, faker_instance):
    entity_id = faker_instance.uuid4()
    score_result = await create_score_result(
        entity_id=entity_id,
        flags=[FlagWithValue(name="negative_impact", value=0.0, weight=1.0)],
        metadata={"some_val": 100}
    )
    assert score_result.probability_score < 0.5

    await create_risk_trigger(
        name="critical_low_score",
        trigger_type="score_threshold",
        score_threshold=score_result.probability_score + 0.01,
        risk_level=RiskLevel.CRITICAL,
    )

    response = await client.post("/sentinela/assess", json={
        "entity_id": entity_id,
        "score_id": str(score_result.id),
        "additional_context": {"transaction_id": faker_instance.uuid4()}
    })
    result = response.json()
    assert response.status_code == 200
    assert result["overall_risk_level"] == RiskLevel.CRITICAL.value
    assert result["triggered_rules"][0]["trigger_name"] == "critical_low_score"


@pytest.mark.asyncio
async def test_assess_risk_flag_presence_triggered(client: AsyncClient, create_score_result, create_risk_trigger, faker_instance):
    entity_id = faker_instance.uuid4()
    score_result = await create_score_result(
        entity_id=entity_id,
        flags=[FlagWithValue(name="sanctioned_country_flag", value=1.0, weight=1.0, is_active=True)],
        metadata={"country": "SanctionedCountry"}
    )

    await create_risk_trigger(
        name="sanction_flag_risk",
        trigger_type="flag_presence",
        flag_name="sanctioned_country_flag",
        risk_level=RiskLevel.HIGH,
    )

    response = await client.post("/sentinela/assess", json={
        "entity_id": entity_id,
        "score_id": str(score_result.id),
    })
    result = response.json()
    assert response.status_code == 200
    assert result["overall_risk_level"] == RiskLevel.HIGH.value
    assert result["triggered_rules"][0]["trigger_name"] == "sanction_flag_risk"


@pytest.mark.asyncio
async def test_assess_risk_custom_logic_triggered(client: AsyncClient, create_score_result, create_risk_trigger, faker_instance):
    entity_id = faker_instance.uuid4()
    score_result = await create_score_result(
        entity_id=entity_id,
        flags=[FlagWithValue(name="default_score", value=0.1, weight=1.0)],
        metadata={"transaction_count_last_24h": 10}
    )

    await create_risk_trigger(
        name="high_freq_low_score_risk",
        trigger_type="custom_logic",
        custom_logic_params={
            "min_transaction_count": 5,
            "max_score": 0.2,
            "suspicious_keywords_found": True
        },
        risk_level=RiskLevel.CRITICAL,
    )

    response = await client.post("/sentinela/assess", json={
        "entity_id": entity_id,
        "score_id": str(score_result.id),
        "additional_context": {
            "user_daily_transactions": 7,
            "suspicious_keywords_found": True
        }
    })
    result = response.json()
    assert response.status_code == 200
    assert result["overall_risk_level"] == RiskLevel.CRITICAL.value
    assert result["triggered_rules"][0]["trigger_name"] == "high_freq_low_score_risk"


@pytest.mark.asyncio
async def test_assess_risk_multiple_triggers_highest_level(client: AsyncClient, create_score_result, create_risk_trigger, faker_instance):
    entity_id = faker_instance.uuid4()
    score_result = await create_score_result(
        entity_id=entity_id,
        flags=[FlagWithValue(name="is_sanctioned", value=1.0, weight=1.0, is_active=True)],
        metadata={"some_val": 10}
    )
    await create_risk_trigger(name="medium_score_trigger", score_threshold=score_result.probability_score + 0.01, risk_level=RiskLevel.MEDIUM)
    await create_risk_trigger(name="critical_flag_trigger", flag_name="is_sanctioned", risk_level=RiskLevel.CRITICAL)

    response = await client.post("/sentinela/assess", json={
        "entity_id": entity_id,
        "score_id": str(score_result.id),
    })
    result = response.json()
    assert response.status_code == 200
    assert result["overall_risk_level"] == RiskLevel.CRITICAL.value
    assert len(result["triggered_rules"]) == 2


@pytest.mark.asyncio
async def test_assess_risk_no_triggers(client: AsyncClient, create_score_result, faker_instance):
    entity_id = faker_instance.uuid4()
    score_result = await create_score_result(entity_id=entity_id)

    response = await client.post("/sentinela/assess", json={
        "entity_id": entity_id,
        "score_id": str(score_result.id),
        "additional_context": {"transaction_id": "tx123"}
    })
    result = response.json()
    assert response.status_code == 200
    assert result["overall_risk_level"] == RiskLevel.LOW.value
    assert len(result["triggered_rules"]) == 0


@pytest.mark.asyncio
async def test_assess_risk_score_not_found(client: AsyncClient, faker_instance):
    non_existent_score_id = "60a7d9b01c9d440000a7b4c8"
    response = await client.post("/sentinela/assess", json={
        "entity_id": faker_instance.uuid4(),
        "score_id": non_existent_score_id,
    })
    assert response.status_code == 404
    assert f"Score with ID {non_existent_score_id} not found." in response.json()["detail"]


@pytest.mark.asyncio
async def test_assess_risk_mismatched_entity_id(client: AsyncClient, create_score_result, faker_instance):
    score_result = await create_score_result(entity_id=faker_instance.uuid4())
    wrong_entity_id = faker_instance.uuid4()
    response = await client.post("/sentinela/assess", json={
        "entity_id": wrong_entity_id,
        "score_id": str(score_result.id),
    })
    assert response.status_code == 400
    assert "does not belong to entity" in response.json()["detail"]
