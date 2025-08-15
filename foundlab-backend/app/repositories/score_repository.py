from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId

from app.database import get_collection


class ScoreRepository:
    def __init__(self):
        self.scores_collection: AsyncIOMotorCollection = get_collection("scores")

    async def create(self, score_data: Dict[str, Any]) -> ObjectId:
        """Inserts a new score document into the collection and returns its ID."""
        insert_result = await self.scores_collection.insert_one(score_data)
        return insert_result.inserted_id

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