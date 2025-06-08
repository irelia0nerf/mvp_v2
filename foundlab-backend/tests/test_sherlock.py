import pytest
from httpx import AsyncClient

from app.models.sherlock import SanctionStatus, SherlockValidationInput


@pytest.mark.asyncio
async def test_validate_entity_reputation_success(client: AsyncClient, faker_instance):
    input_data = SherlockValidationInput(
        entity_id=faker_instance.uuid4() + "_clean_user",
        entity_type="wallet_address",
    )
    response = await client.post("/sherlock/validate", json=input_data.model_dump())
    assert response.status_code == 200
    assert response.json()["entity_id"] == input_data.entity_id
    assert response.json()["overall_sanction_status"] == SanctionStatus.CLEAN.value
    assert response.json()["overall_risk_score"] < 0.2
    assert len(response.json()["provider_results"]) == 2
    assert response.json()["_id"] is not None
    assert response.json()["suggested_action"] == "proceed"
    assert len(response.json()["sherlock_flags"]) == 0


@pytest.mark.asyncio
async def test_validate_entity_reputation_sanctioned_by_chainalysis(client: AsyncClient, faker_instance):
    input_data = SherlockValidationInput(
        entity_id="sanctioned_entity_mock_test",
        entity_type="wallet_address",
    )
    response = await client.post("/sherlock/validate", json=input_data.model_dump())
    assert response.status_code == 200
    assert response.json()["overall_sanction_status"] == SanctionStatus.SANCTIONED.value
    assert response.json()["overall_risk_score"] == 1.0
    assert any("OFAC_SDN_Match" in flag["flag_name"] for flag in response.json()["sherlock_flags"])
    assert response.json()["suggested_action"] == "block"


@pytest.mark.asyncio
async def test_validate_entity_reputation_sanctioned_by_trm(client: AsyncClient, faker_instance):
    input_data = SherlockValidationInput(
        entity_id="cft_listed_example",
        entity_type="organization",
    )
    response = await client.post("/sherlock/validate", json=input_data.model_dump())
    assert response.status_code == 200
    assert response.json()["overall_sanction_status"] == SanctionStatus.SANCTIONED.value
    assert response.json()["overall_risk_score"] == 0.98
    assert any("CFT_List_Match" in flag["flag_name"] for flag in response.json()["sherlock_flags"])
    assert response.json()["suggested_action"] == "block"


@pytest.mark.asyncio
async def test_validate_entity_reputation_high_risk_aml(client: AsyncClient, faker_instance):
    input_data = SherlockValidationInput(
        entity_id="high_volume_gambling_user",
        entity_type="user_id",
    )
    response = await client.post("/sherlock/validate", json=input_data.model_dump())
    assert response.status_code == 200
    assert response.json()["overall_sanction_status"] == SanctionStatus.HIGH_RISK.value
    assert response.json()["overall_risk_score"] == 0.7
    assert any(flag["category"] == "AML" and flag["severity"] >= 0.7 for flag in response.json()["sherlock_flags"])
    assert response.json()["suggested_action"] == "review_manual"


@pytest.mark.asyncio
async def test_validate_entity_reputation_pep_exposed(client: AsyncClient, faker_instance):
    input_data = SherlockValidationInput(
        entity_id="pep_exposed_politician",
        entity_type="person",
    )
    response = await client.post("/sherlock/validate", json=input_data.model_dump())
    assert response.status_code == 200
    assert response.json()["overall_sanction_status"] == SanctionStatus.HIGH_RISK.value
    assert response.json()["overall_risk_score"] == 0.6
    assert any("PEP_Exposure" in flag["flag_name"] for flag in response.json()["sherlock_flags"])
    assert response.json()["suggested_action"] == "review_manual"


@pytest.mark.asyncio
async def test_validate_entity_reputation_pending_status(client: AsyncClient, faker_instance):
    input_data = SherlockValidationInput(
        entity_id="under_investigation_entity",
        entity_type="account",
    )
    response = await client.post("/sherlock/validate", json=input_data.model_dump())
    assert response.status_code == 200
    assert response.json()["overall_sanction_status"] == SanctionStatus.UNKNOWN.value
    assert response.json()["suggested_action"] == "review_manual"
    assert any(p["provider_name"] == "Chainalysis" and p["status"] == "pending" for p in response.json()["provider_results"])
    assert any(p["provider_name"] == "TRM Labs" and p["status"] == "success" for p in response.json()["provider_results"])


@pytest.mark.asyncio
async def test_get_validation_results_by_entity(client: AsyncClient, create_sherlock_validation_result, faker_instance):
    entity_id = faker_instance.uuid4() + "_history_entity"
    result1 = await create_sherlock_validation_result(entity_id=entity_id, entity_type="wallet_address")
    result2 = await create_sherlock_validation_result(entity_id=entity_id, entity_type="wallet_address")
    result3 = await create_sherlock_validation_result(entity_id=entity_id, entity_type="wallet_address")

    response = await client.get(f"/sherlock/{entity_id}")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 3
    assert all(r["entity_id"] == entity_id for r in results)

    created_at_dates = [r["created_at"] for r in results]
    assert all(created_at_dates[i] >= created_at_dates[i + 1] for i in range(len(created_at_dates) - 1))
    assert results[0]["_id"] == str(result3.id)


@pytest.mark.asyncio
async def test_get_validation_results_by_entity_no_results(client: AsyncClient, faker_instance):
    entity_id = faker_instance.uuid4() + "_no_history"
    response = await client.get(f"/sherlock/{entity_id}")
    assert response.status_code == 200
    assert len(response.json()) == 0
