from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status, Request
from bson import ObjectId

from app.models.score import ScoreInput, ScoreResult
from app.utils.score_calculator import ScoreCalculator
from app.repositories.score_repository import ScoreRepository
from app.middleware.request_context_middleware import use_case_context


class ScoreLabService:
    def __init__(self, request: Request):
        self.request = request
        self.score_repository = ScoreRepository()

    async def calculate_score(self, score_input: ScoreInput) -> ScoreResult:
        """
        Calculates a new reputation score P(x) for a given entity based on provided flags and metadata.
        Only flags marked as `is_active=True` will contribute to the P(x) calculation.
        The full list of flags provided in `score_input` (active and inactive) is stored.
        The calculated score result is stored in the database.
        """
        self.score_calculator = ScoreCalculator() # Instantiate calculator here as needed\n
        # --- Definir UseCase no contexto e injetar dados no request.state ---
        use_case_token = use_case_context.set("recalibrate_score") # Setar o use case no contexto

        # Injetar dados no request.state antes da chamada ao call_next no middleware
        # Para este exemplo, score_before será None na primeira execução
        # score_after será o score calculado
        self.request.state.score_before = None # Buscar score_before real se necessário
        self.request.state.flags_triggered = [f.model_dump() for f in score_input.flags if f.is_active] # Exemplo: flags ativas
        active_flags = [f for f in score_input.flags if f.is_active]

        raw_score, probability_score = self.score_calculator.calculate_p_x(
            active_flags, score_input.metadata
        )

        score_data = {
            "entity_id": score_input.entity_id,
            "probability_score": probability_score,
            "raw_score": raw_score,
            "algorithm_version": self.score_calculator.version,
            "flags_used": [f.model_dump() for f in score_input.flags],
            "metadata_used": score_input.metadata,
            "summary": f"Reputation score for {score_input.entity_id} is {probability_score:.4f}.",
        }

        new_score_doc = await self.score_repository.create(score_data)

        # --- Injetar score_after no request.state ---
        self.request.state.score_after = probability_score
        # --------------------------------------------

        # Resetar use_case_context ao sair do escopo deste caso de uso
        use_case_context.reset(use_case_token)

        return ScoreResult(**new_score_doc)

    async def get_score_by_id(self, score_id: str) -> Optional[ScoreResult]:
        """Retrieves a previously calculated score by its unique ID."""
        # --- Definir UseCase no contexto para logs de busca ---
        use_case_token = use_case_context.set("get_score_by_id")
        # Não injetar score_before/after/flags pois é read-only
        # ------------------------------------------------------
        if not ObjectId.is_valid(score_id):
            # Resetar use_case_context em caso de retorno antecipado
            use_case_context.reset(use_case_token)
            return None

        _id_obj = ObjectId(score_id)
        score = await self.score_repository.get_by_id(_id_obj)
        use_case_context.reset(use_case_token)
        return ScoreResult(**score) if score else None
    async def get_scores_by_entity_id(self, entity_id: str) -> List[ScoreResult]:
        """Retrieves all historical scores for a given entity, ordered by most recent first."""
        # --- Definir UseCase no contexto para logs de busca ---
        use_case_token = use_case_context.set("get_scores_by_entity")
        # Não injetar score_before/after/flags pois é read-only
        # ------------------------------------------------------
        score_docs = await self.score_repository.get_by_entity_id(entity_id)
        use_case_context.reset(use_case_token)
        return [ScoreResult(**doc) for doc in score_docs]\n
