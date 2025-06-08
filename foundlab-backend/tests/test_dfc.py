import pytest
from httpx import AsyncClient

from app.models.dfc import FlagDefinition, FlagType, Rule, RuleCondition


@pytest.mark.asyncio
async def test_create_flag_definition(client: AsyncClient, create_flag_definition):
    """Test creating a new flag definition."""
    flag = await create_flag_definition(name="test_flag_1", rules=[{"field": "age", "condition": RuleCondition.GTE, "value": 18}])
    assert flag.name == "test_flag_1"
    assert flag.id is not None
    assert flag.rules[0].field == "age"


@pytest.mark.asyncio
async def test_create_flag_definition_duplicate_name(client: AsyncClient, create_flag_definition):
    """Test creating a flag definition with a duplicate name."""
    await create_flag_definition(name="duplicate_flag")
    response = await client.post("/flags/definitions", json={
        "name": "duplicate_flag",
        "description": "Another test flag.",
        "type": "boolean",
        "rules": [],
    })
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_all_flag_definitions(client: AsyncClient, create_flag_definition):
    """Test retrieving all flag definitions."""
    flag1 = await create_flag_definition(name="all_flag_1")
    flag2 = await create_flag_definition(name="all_flag_2")
    response = await client.get("/flags/definitions")
    assert response.status_code == 200
    assert len(response.json()) >= 2
    assert any(f["name"] == flag1.name for f in response.json())
    assert any(f["name"] == flag2.name for f in response.json())


@pytest.mark.asyncio
async def test_get_flag_definition_by_name(client: AsyncClient, create_flag_definition):
    """Test retrieving a flag definition by name."""
    flag = await create_flag_definition(name="get_by_name_flag")
    response = await client.get(f"/flags/definitions/{flag.name}")
    assert response.status_code == 200
    assert response.json()["name"] == flag.name


@pytest.mark.asyncio
async def test_get_flag_definition_by_name_not_found(client: AsyncClient):
    """Test retrieving a non-existent flag definition."""
    response = await client.get("/flags/definitions/nonexistent_flag")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_flag_definition(client: AsyncClient, create_flag_definition):
    """Test updating an existing flag definition."""
    flag = await create_flag_definition(name="update_flag")
    update_data = {"description": "Updated description.", "weight": 0.8}
    response = await client.put(f"/flags/definitions/{flag.name}", json=update_data)
    assert response.status_code == 200
    assert response.json()["description"] == "Updated description."
    assert response.json()["weight"] == 0.8
    assert response.json()["name"] == flag.name
    assert response.json()["type"] == flag.type.value


@pytest.mark.asyncio
async def test_update_flag_definition_no_changes(client: AsyncClient, create_flag_definition):
    """Test updating a flag definition with no actual changes."""
    flag = await create_flag_definition(name="no_change_flag", description="OriginalDesc", weight=0.2)
    update_data = {"description": "OriginalDesc", "weight": 0.2}
    response = await client.put(f"/flags/definitions/{flag.name}", json=update_data)
    assert response.status_code == 200
    assert response.json()["description"] == "OriginalDesc"


@pytest.mark.asyncio
async def test_update_flag_definition_not_found(client: AsyncClient):
    """Test updating a non-existent flag definition."""
    update_data = {"description": "Updated description."}
    response = await client.put("/flags/definitions/nonexistent_flag", json=update_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_flag_definition(client: AsyncClient, create_flag_definition):
    """Test deleting a flag definition."""
    flag = await create_flag_definition(name="delete_flag")
    response = await client.delete(f"/flags/definitions/{flag.name}")
    assert response.status_code == 204
    response = await client.get(f"/flags/definitions/{flag.name}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_flag_definition_not_found(client: AsyncClient):
    """Test deleting a non-existent flag definition."""
    response = await client.delete("/flags/definitions/nonexistent_flag")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_apply_dynamic_flags_simple_match(client: AsyncClient, create_flag_definition, faker_instance):
    """Test applying dynamic flags with a simple match."""
    await create_flag_definition(
        name="high_risk_user",
        rules=[{"field": "risk_score", "condition": RuleCondition.GT, "value": 0.7}],
        weight=1.0,
    )
    input_data = {
        "entity_id": faker_instance.uuid4(),
        "metadata": {"risk_score": 0.8, "country": "USA"},
    }
    response = await client.post("/flags/apply", json=input_data)
    assert response.status_code == 200
    assert response.json()["entity_id"] == input_data["entity_id"]
    assert len(response.json()["evaluated_flags"]) == 1
    assert response.json()["evaluated_flags"][0]["flag_name"] == "high_risk_user"
    assert response.json()["evaluated_flags"][0]["is_active"] is True
    assert response.json()["active_flags_summary"]["high_risk_user"] is True


@pytest.mark.asyncio
async def test_apply_dynamic_flags_no_match(client: AsyncClient, create_flag_definition, faker_instance):
    """Test applying dynamic flags with no match."""
    await create_flag_definition(
        name="high_risk_user_no_match",
        rules=[{"field": "risk_score", "condition": RuleCondition.GT, "value": 0.7}],
        weight=1.0,
    )
    input_data = {
        "entity_id": faker_instance.uuid4(),
        "metadata": {"risk_score": 0.5, "country": "USA"},
    }
    response = await client.post("/flags/apply", json=input_data)
    assert response.status_code == 200
    assert len(response.json()["evaluated_flags"]) == 1
    assert response.json()["evaluated_flags"][0]["flag_name"] == "high_risk_user_no_match"
    assert response.json()["evaluated_flags"][0]["is_active"] is False
    assert "high_risk_user_no_match" not in response.json()["active_flags_summary"]


@pytest.mark.asyncio
async def test_apply_dynamic_flags_default_value_no_rules(client: AsyncClient, create_flag_definition, faker_instance):
    """Test applying a flag definition with default value and no rules."""
    await create_flag_definition(
        name="always_on_flag",
        description="This flag is always on.",
        flag_type=FlagType.BOOLEAN,
        default_value=True,
        rules=[],
        weight=0.1,
    )
    input_data = {
        "entity_id": faker_instance.uuid4(),
        "metadata": {},
    }
    response = await client.post("/flags/apply", json=input_data)
    assert response.status_code == 200
    assert response.json()["evaluated_flags"][0]["flag_name"] == "always_on_flag"
    assert response.json()["evaluated_flags"][0]["is_active"] is True
    assert response.json()["evaluated_flags"][0]["value"] is True
    assert response.json()["evaluated_flags"][0]["reason"] == "No rules defined for dynamic evaluation, using default value."
    assert response.json()["active_flags_summary"]["always_on_flag"] is True


@pytest.mark.asyncio
async def test_apply_dynamic_flags_boolean_output_value(client: AsyncClient, create_flag_definition, faker_instance):
    """Test that boolean flags correctly output True/False as value."""
    await create_flag_definition(
        name="is_adult",
        flag_type=FlagType.BOOLEAN,
        rules=[{"field": "age", "condition": RuleCondition.GTE, "value": 18}],
    )
    input_data_true = {"entity_id": faker_instance.uuid4(), "metadata": {"age": 20}}
    response_true = await client.post("/flags/apply", json=input_data_true)
    assert response_true.status_code == 200
    assert response_true.json()["evaluated_flags"][0]["flag_name"] == "is_adult"
    assert response_true.json()["evaluated_flags"][0]["is_active"] is True
    assert response_true.json()["evaluated_flags"][0]["value"] is True

    input_data_false = {"entity_id": faker_instance.uuid4(), "metadata": {"age": 16}}
    response_false = await client.post("/flags/apply", json=input_data_false)
    assert response_false.status_code == 200
    assert response_false.json()["evaluated_flags"][0]["flag_name"] == "is_adult"
    assert response_false.json()["evaluated_flags"][0]["is_active"] is False
    assert response_false.json()["evaluated_flags"][0]["value"] is False


@pytest.mark.asyncio
async def test_apply_dynamic_flags_numeric_output_value(client: AsyncClient, create_flag_definition, faker_instance):
    """Test that numeric flags correctly output the field value when rule matches."""
    await create_flag_definition(
        name="transaction_volume_flag",
        flag_type=FlagType.NUMERIC,
        rules=[{"field": "volume", "condition": RuleCondition.GT, "value": 1000}],
        default_value=0.0
    )
    input_data = {"entity_id": faker_instance.uuid4(), "metadata": {"volume": 1500.50}}
    response = await client.post("/flags/apply", json=input_data)
    assert response.status_code == 200
    assert response.json()["evaluated_flags"][0]["flag_name"] == "transaction_volume_flag"
    assert response.json()["evaluated_flags"][0]["is_active"] is True
    assert response.json()["evaluated_flags"][0]["value"] == 1500.50
