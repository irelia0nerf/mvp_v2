from typing import List

from fastapi import APIRouter, HTTPException, Path, status, Depends

from app.models.score import ScoreInput, ScoreResult
from app.services.score_service import ScoreLabService

router = APIRouter()


async def get_score_service() -> ScoreLabService:
 return ScoreLabService()


@router.post(
    "",
    response_model=ScoreResult,
    status_code=status.HTTP_201_CREATED,
    summary="Calculate a new reputation score",
    response_description="The calculated reputation score for the entity.",
)
async def calculate_score(score_input: ScoreInput):
    """
 Calculates a new reputation score `P(x)` for a given entity.
    """
 score_service: ScoreLabService = Depends(get_score_service)
    try:
 score_service_instance = await score_service(score_service)
        result = await score_service.calculate_score(score_input)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to calculate score: {e}"
        )


@router.get(
    "/{score_id}",
    response_model=ScoreResult,
    summary="Retrieve a reputation score by ID",
    response_description="The stored reputation score.",
)
async def get_score_by_id(score_id: str = Path(..., description="ID of the score to retrieve")):
 """
 Retrieves a previously calculated reputation score by its unique ID.
 """
 score_service: ScoreLabService = Depends(get_score_service)
 score_service_instance = await score_service(score_service)
 score = await score_service_instance.get_score_by_id(score_id)
    if not score:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Score not found.")
    return score


@router.get(
    "/entity/{entity_id}",
    response_model=List[ScoreResult],
    summary="Retrieve all reputation scores for a specific entity",
    response_description="A list of historical reputation scores for the entity.",
)
async def get_scores_by_entity(entity_id: str = Path(..., description="ID of the entity to retrieve scores for")):
 """
 Retrieves all historical reputation scores associated with a specific entity ID.
 """
 score_service: ScoreLabService = Depends(get_score_service)
 score_service_instance = await score_service(score_service)
 return await score_service_instance.get_scores_by_entity_id(entity_id)
