from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId

from app.database import get_collection

# Import módulos do prometheus_client
from prometheus_client import Histogram, Counter
import time



# Definir métricas customizadas para o repositório de Score
SCORE_REPO_OPERATION_LATENCY = Histogram(
    "score_repo_operation_latency_seconds",
    "Latency of Score Repository operations",
    ["method", "collection"], # Labels: nome do método e nome da coleção
)

SCORE_REPO_ERRORS_TOTAL = Counter(
    "score_repo_errors_total",
    "Total errors in Score Repository operations",
    ["method", "collection", "error_type"], # Labels: método, coleção, tipo de erro
)

class ScoreRepository:
    def __init__(self):
        self.scores_collection: AsyncIOMotorCollection = get_collection("scores")

    async def get_by_id(self, score_id: ObjectId) -> Optional[Dict[str, Any]]:
        """Retrieves a score document by its ObjectId."""
        score_doc = await self.scores_collection.find_one({"_id": score_id})
        return score_doc

    async def get_by_entity_id(self, entity_id: str) -> List[Dict[str, Any]]:
        """Retrieves all score documents for a given entity, ordered by most recent first."""
        scores_docs = []
        cursor = self.scores_collection.find({"entity_id": entity_id}).sort("created_at", -1)
        async for score_doc in cursor:
            scores_docs.append(score_doc)
        return scores_docs

    async def create(self, score_data: Dict[str, Any]) -> Dict[str, Any]: # Repositório retorna dict, não Pydantic model
        """Creates a new score record in the database."""
        method_name = "create"
        collection_name = "scores"
        start_time = time.perf_counter()
        try:
            insert_result = await self.scores_collection.insert_one(score_data)
            # Buscar o documento inserido (para retornar o _id e outros campos gerados pelo Mongo)
            # Esta busca pode ser otimizada dependendo da versão do motor/MongoDB
            new_score_doc = await self.scores_collection.find_one({"_id": insert_result.inserted_id})
            # Registrar latência de sucesso
            SCORE_REPO_OPERATION_LATENCY.labels(method=method_name, collection=collection_name).observe(time.perf_counter() - start_time)
            return new_score_doc
        except Exception as e:
            # Registrar erro
            error_type = type(e).__name__
            SCORE_REPO_ERRORS_TOTAL.labels(method=method_name, collection=collection_name, error_type=error_type).inc()
            # Re-raise a exceção para ser tratada nas camadas superiores
            raise

    async def get_by_id(self, object_id: ObjectId) -> Optional[Dict[str, Any]]: # Aceita ObjectId, retorna dict
        """Retrieves a score record by its ObjectId."""
        method_name = "get_by_id"
        collection_name = "scores"
        start_time = time.perf_counter()
        try:
            score_doc = await self.scores_collection.find_one({"_id": object_id})
            # Registrar latência de sucesso
            SCORE_REPO_OPERATION_LATENCY.labels(method=method_name, collection=collection_name).observe(time.perf_counter() - start_time)
            return score_doc
        except Exception as e:
            # Registrar erro
            error_type = type(e).__name__
            SCORE_REPO_ERRORS_TOTAL.labels(method=method_name, collection=collection_name, error_type=error_type).inc()
            # Re-raise a exceção
            raise

