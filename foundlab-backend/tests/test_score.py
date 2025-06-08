import pytest
from httpx import AsyncClient

from app.models.score import FlagWithValue


@pytest.mark.asyncio
async def test_calculate_score_success(client: AsyncClient, create_score_result, faker_instance):
    entity_id = faker_instance.uuid4()
    flags = [
        FlagWithValue(name="flag_a", value=True, weight=0.5, is_active=True),
        FlagWithValue(name="flag_b", value=0.7, weight=0.3, is_active=True),
        FlagWithValue(name="flag_c_inactive", value=0.9, weight=0.2, is_active=False),
    ]
    metadata = {"transaction_volume": 10000.0, "account_age_days": 300}

    score_result = await create_score_result(entity_id=entity_id, flags=flags, metadata=metadata)

    assert score_result.entity_id == entity_id
    assert 0.0 <= score_result.probability_score <= 1.0
    assert score_result.id is not None
    assert score_result.flags_used[2].is_active is False

    assert score_result.raw_score == pytest.approx(0.71)
    assert score_result.probability_score == pytest.approx(0.8875)


@pytest.mark.asyncio
async def test_calculate_score_no_active_flags(client: AsyncClient, create_score_result, faker_instance):
    entity_id = faker_instance.uuid4()
    flags = [
        FlagWithValue(name="inactive_flag", value=True, weight=0.5, is_active=False)
    ]
    score_result = await create_score_result(entity_id=entity_id, flags=flags, metadata={})

    assert score_result.probability_score == pytest.approx(0.5)
    assert score_result.raw_score == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_calculate_score_zero_sum_of_weights(client: AsyncClient, create_score_result, faker_instance):
    entity_id = faker_instance.uuid4()
    flags = [
        FlagWithValue(name="zero_weight_flag", value=True, weight=0.0, is_active=True)
    ]
    score_result = await create_score_result(entity_id=entity_id, flags=flags, metadata={})

    assert score_result.probability_score == pytest.approx(0.5)
    assert score_result.raw_score == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_get_score_by_id_success(client: AsyncClient, create_score_result):
    score = await create_score_result()
    response = await client.get(f"/scores/{score.id}")
    assert response.status_code == 200
    assert response.json()["entity_id"] == score.entity_id
    assert response.json()["probability_score"] == pytest.approx(score.probability_score, rel=1e-9)


@pytest.mark.asyncio
async def test_get_score_by_id_not_found(client: AsyncClient):
    response = await client.get("/scores/60a7d9b01c9d440000a7b4c8")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_score_by_id_invalid_format(client: AsyncClient):
    response = await client.get("/scores/invalid_id_format")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_scores_by_entity_success(client: AsyncClient, create_score_result, faker_instance):
    entity_id = faker_instance.uuid4()
    score1 = await create_score_result(entity_id=entity_id, flags=[FlagWithValue(name="f1", value=0.5, weight=0.1)], metadata={})
    score2 = await create_score_result(entity_id=entity_id, flags=[FlagWithValue(name="f2", value=0.8, weight=0.2)], metadata={})
    score3 = await create_score_result(entity_id=entity_id, flags=[FlagWithValue(name="f3", value=0.1, weight=0.3)], metadata={})

    response = await client.get(f"/scores/entity/{entity_id}")
    assert response.status_code == 200
    scores_from_api = response.json()
    assert len(scores_from_api) == 3
    assert all(s["entity_id"] == entity_id for s in scores_from_api)

    created_at_dates = [s["created_at"] for s in scores_from_api]
    assert all(created_at_dates[i] >= created_at_dates[i + 1] for i in range(len(created_at_dates) - 1))
    assert scores_from_api[0]["_id"] == str(score3.id)


@pytest.mark.asyncio
async def test_get_scores_by_entity_no_scores(client: AsyncClient, faker_instance):
    entity_id = faker_instance.uuid4()
    response = await client.get(f"/scores/entity/{entity_id}")
    assert response.status_code == 200
    assert len(response.json()) == 0
