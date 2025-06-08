from typing import List

from fastapi import APIRouter, HTTPException, Path, status, Body

from app.models.risk import (
    CreateRiskTrigger,
    RiskAssessmentInput,
    RiskAssessmentResult,
    RiskTrigger,
    UpdateRiskTrigger,
)
from app.services.risk_service import SentinelaService

router = APIRouter()
sentinela_service = SentinelaService()


@router.post(
    "/triggers",
    response_model=RiskTrigger,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new risk trigger rule",
)
async def create_risk_trigger(trigger_data: CreateRiskTrigger):
    """
    Creates a new risk trigger definition for Sentinela.
    These triggers define conditions that, when met, indicate a risk.
    """
    try:
        new_trigger = await sentinela_service.create_risk_trigger(trigger_data.model_dump())
        if not new_trigger:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=f"Trigger '{trigger_data.name}' already exists."
            )
        return new_trigger
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create risk trigger: {e}"
        )


@router.get(
    "/triggers",
    response_model=List[RiskTrigger],
    summary="Retrieve all risk trigger rules",
)
async def get_all_risk_triggers():
    """
    Retrieves all defined risk trigger rules.
    """
    try:
        triggers = await sentinela_service.get_all_risk_triggers()
        return triggers
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve risk triggers: {e}"
        )


@router.get(
    "/triggers/{trigger_name}",
    response_model=RiskTrigger,
    summary="Retrieve a risk trigger rule by name",
)
async def get_risk_trigger_by_name(
    trigger_name: str = Path(..., description="Name of the risk trigger to retrieve")
):
    """
    Retrieves a single risk trigger definition by its unique name.
    """
    trigger = await sentinela_service.get_risk_trigger_by_name(trigger_name)
    if not trigger:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk trigger not found.")
    return trigger


@router.put(
    "/triggers/{trigger_name}",
    response_model=RiskTrigger,
    summary="Update an existing risk trigger rule",
)
async def update_risk_trigger(
    trigger_name: str = Path(..., description="Name of the risk trigger to update"),
    trigger_data: UpdateRiskTrigger = Body(..., description="New data for the risk trigger"),
):
    """
    Updates an existing risk trigger definition.
    """
    updated_trigger = await sentinela_service.update_risk_trigger(
        trigger_name, trigger_data.model_dump(exclude_unset=True)
    )
    if not updated_trigger:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk trigger not found.")
    return updated_trigger


@router.delete(
    "/triggers/{trigger_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a risk trigger rule",
)
async def delete_risk_trigger(
    trigger_name: str = Path(..., description="Name of the risk trigger to delete")
):
    """
    Deletes a risk trigger definition by its unique name.
    """
    deleted_count = await sentinela_service.delete_risk_trigger(trigger_name)
    if deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk trigger not found.")
    return


@router.post(
    "/assess",
    response_model=RiskAssessmentResult,
    status_code=status.HTTP_200_OK,
    summary="Assess risk for an entity based on its ScoreLab score and flags",
    response_description="Detailed risk assessment results from Sentinela.",
)
async def assess_risk(assessment_input: RiskAssessmentInput):
    """
    Performs a risk assessment for a given entity using its ScoreLab score
    and potentially other flags/context.

    The Sentinela engine evaluates the provided score against a set of predefined
    risk triggers (e.g., score below a certain threshold, presence of specific flags)
    to determine an overall risk level and identify activated rules.
    """
    try:
        result = await sentinela_service.assess_entity_risk(
            assessment_input.entity_id, assessment_input.score_id, assessment_input.additional_context
        )
        return result
    except HTTPException as e:
        raise e  # Re-raise HTTPExceptions from service layer
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to assess risk: {e}"
        )
