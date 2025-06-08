from datetime import datetime
from typing import Annotated, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, BeforeValidator


# Custom type for MongoDB's ObjectId
PyObjectId = Annotated[str, BeforeValidator(str)]


class MongoBaseModel(BaseModel):
    """
    Base model for MongoDB documents, handling ObjectId and timestamps.
    """

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }
