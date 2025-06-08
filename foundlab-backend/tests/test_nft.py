import pytest
from httpx import AsyncClient
from pydantic_extra_types.color import Color

from app.models.risk import RiskLevel
from app.models.score import FlagWithValue, ScoreResult


@pytest.mark.asyncio
async def test_generate_sigilmesh_nft_metadata_success(client: AsyncClient, create_score_result, create_risk_trigger, faker_instance):
    """Test successful generation of NFT metadata for a high score (implies low risk)."""
    entity_id = faker_instance.uuid4()

    score_result = await create_score_result(
        entity_id=entity_id,
        flags=[
            FlagWithValue(name="kyc_verified", value=True, weight=0.5),
            FlagWithValue(name="high_activity", value=1.0, weight=0.5)
        ],
        metadata={"account_age_days": 1000}
    )

    await client.post("/sentinela/assess", json={"entity_id": entity_id, "score_id": str(score_result.id)})

    input_data = {
        "entity_id": entity_id,
        "score_id": str(score_result.id),
        "custom_name": "My Custom Sigil",
        "custom_description": "This is a custom description for the NFT."
    }
    response = await client.post("/nft/metadata", json=input_data)
    assert response.status_code == 201
    nft_output = response.json()
    assert nft_output["entity_id"] == entity_id
    assert nft_output["score_id"] == str(score_result.id)
    assert nft_output["nft_metadata"]["name"] == "My Custom Sigil"
    assert "FoundLab Score" in [attr["trait_type"] for attr in nft_output["nft_metadata"]["attributes"]]
    assert any(attr["value"] == f"{score_result.probability_score:.4f}" for attr in nft_output["nft_metadata"]["attributes"])
    assert nft_output["nft_metadata"]["background_color"] == "#00FF00"  # Green for low risk


@pytest.mark.asyncio
async def test_generate_sigilmesh_nft_metadata_with_low_score_high_risk(client: AsyncClient, create_score_result, create_risk_trigger, faker_instance):
    """Test NFT metadata generation for a low score, which should imply high risk and red color."""
    entity_id = faker_instance.uuid4()
    score_result = await create_score_result(
        entity_id=entity_id,
        flags=[
            FlagWithValue(name="high_suspicion", value=True, weight=0.9),
            FlagWithValue(name="low_activity", value=False, weight=0.5)
        ],
        metadata={"account_age_days": 10}
    )

    await create_risk_trigger(name="low_score_trigger", score_threshold=score_result.probability_score + 0.01, risk_level=RiskLevel.HIGH)

    risk_assessment = await client.post("/sentinela/assess", json={"entity_id": entity_id, "score_id": str(score_result.id)})
    assert risk_assessment.status_code == 200
    assert risk_assessment.json()["overall_risk_level"] == RiskLevel.HIGH.value

    input_data = {
        "entity_id": entity_id,
        "score_id": str(score_result.id)
    }
    response = await client.post("/nft/metadata", json=input_data)
    assert response.status_code == 201
    nft_output = response.json()
    assert nft_output["entity_id"] == entity_id
    assert nft_output["nft_metadata"]["name"] == f"FoundLab Sigil of Reputation for {entity_id[:10]}..."
    assert nft_output["nft_metadata"]["background_color"] == "#FFA500"  # Orange for HIGH risk
    assert any(attr["trait_type"] == "Risk Tier" and attr["value"] == RiskLevel.HIGH.value for attr in nft_output["nft_metadata"]["attributes"])


@pytest.mark.asyncio
async def test_generate_sigilmesh_nft_metadata_score_not_found(client: AsyncClient, faker_instance):
    """Test NFT metadata generation with a non-existent score ID."""
    input_data = {
        "entity_id": faker_instance.uuid4(),
        "score_id": "653a0f7c2b1e4d5a6f7b8c9d"
    }
    response = await client.post("/nft/metadata", json=input_data)
    assert response.status_code == 404
    assert "Score with ID 653a0f7c2b1e4d5a6f7b8c9d not found." in response.json()["detail"]


@pytest.mark.asyncio
async def test_generate_sigilmesh_nft_metadata_mismatched_entity_id(client: AsyncClient, create_score_result, faker_instance):
    """Test NFT metadata generation with a mismatched entity ID for the score."""
    score_result = await create_score_result(entity_id=faker_instance.uuid4())
    input_data = {
        "entity_id": faker_instance.uuid4(),  # Different entity ID
        "score_id": str(score_result.id)
    }
    response = await client.post("/nft/metadata", json=input_data)
    assert response.status_code == 400
    assert "does not belong to entity" in response.json()["detail"]


@pytest.mark.asyncio
async def test_generate_sigilmesh_nft_metadata_custom_background_color(client: AsyncClient, create_score_result, faker_instance):
    """Test generation with a custom background color provided by the user."""
    entity_id = faker_instance.uuid4()
    score_result = await create_score_result(entity_id=entity_id)

    input_data = {
        "entity_id": entity_id,
        "score_id": str(score_result.id),
        "background_color": "#FFC0CB"
    }

    response = await client.post("/nft/metadata", json=input_data)
    assert response.status_code == 201
    nft_output = response.json()
    assert Color(nft_output["nft_metadata"]["background_color"]) == Color("#FFC0CB")
