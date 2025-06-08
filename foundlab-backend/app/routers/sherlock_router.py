from typing import List

from fastapi import APIRouter, HTTPException, Path, status

from app.models.sherlock import SherlockValidationInput, SherlockValidationResult
from app.services.sherlock_service import SherlockService

router = APIRouter()
sherlock_service = SherlockService()


@router.post(
    "/validate",
    response_model=SherlockValidationResult,
    status_code=status.HTTP_200_OK,
    summary="Perform reputational validation on an entity",
    response_description="The comprehensive validation result, including provider checks.",
)
async def validate_entity_reputation(validation_input: SherlockValidationInput):
    """
    Performs a comprehensive reputational validation on an entity.

    This involves querying various external compliance providers (like Chainalysis)
    and aggregating their results to provide an overall sanction status and risk score.

    **Current Implementation Notes:**
    *   Currently, external provider calls are mocked. In a production environment,
        this service would integrate with actual APIs from Chainalysis, TRM Labs, etc.
    *   The aggregation logic is simplified for demonstration. Real aggregation would
        involve complex weighting, conflict resolution, and detailed flag processing.
    """
    try:
        result = await sherlock_service.validate_entity(validation_input)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to validate entity: {e}"
        )


@router.get(
    "/{entity_id}",
    response_model=List[SherlockValidationResult],
    summary="Retrieve historical validation results for an entity",
    response_description="A list of historical validation results for the entity.",
)
async def get_validation_results_by_entity(
    entity_id: str = Path(..., description="ID of the entity to retrieve validation results for")
):
    """
    Retrieves all historical reputational validation results associated with a specific entity ID.
    Results are ordered by most recent first.
    """
    results = await sherlock_service.get_validation_results_by_entity_id(entity_id)
    return results
