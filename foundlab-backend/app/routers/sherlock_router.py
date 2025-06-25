from fastapi import APIRouter, Body, HTTPException, status

from app.models.sherlock import SherlockValidationInput, SherlockValidationResult
from app.services.sherlock_service import SherlockService

router = APIRouter()


@router.post(
    "/validate",
    response_model=SherlockValidationResult,
    status_code=status.HTTP_200_OK,
    summary="Run Sherlock validation",
    response_description="Validation result of the Sherlock module.",
)
async def validate_with_sherlock(input_data: SherlockValidationInput = Body(...)):
    """
    Performs a Sherlock validation on the provided input.

    Sherlock is a rule-based validation system that checks input metadata against
    defined schemas, formats, and other basic validations.
    """
    sherlock_service = SherlockService()
    try:
        result = await sherlock_service.validate(input_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run Sherlock validation: {e}"
        )
