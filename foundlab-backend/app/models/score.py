from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.base import MongoBaseModel


class FlagWithValue(BaseModel):
    """Represents a flag with its evaluated value, used as input for scoring."""

    name: str = Field(description="Name of the flag (e.g., 'high_risk_country').")
    value: Any = Field(description="Evaluated value of the flag (e.g., True, 0.8, 'sanctioned').")
    weight: float = Field(0.0, description="Numerical weight for this flag for scoring.")
    is_active: bool = Field(True, description="Whether this flag is considered 'active' or contributing.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"name": "is_kyc_verified", "value": True, "weight": 0.2, "is_active": True},
                {"name": "fraud_score", "value": 0.8, "weight": 0.5, "is_active": True},
                {"name": "geographic_risk", "value": 0.3, "weight": 0.3, "is_active": False}
            ]
        }
    }


class ScoreInput(BaseModel):
    """Input model for requesting a ScoreLab score calculation."""

    entity_id: str = Field(description="Unique identifier for the entity being scored.")
    flags: List[FlagWithValue] = Field(default_factory=list, description="List of DFC flags with their values to consider.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata (e.g., transaction_volume, account_age) to incorporate into scoring.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "entity_id": "wallet_0xabc123...",
                    "flags": [
                        {"name": "is_kyc_verified", "value": True, "weight": 0.2, "is_active": True},
                        {"name": "fraud_risk_score", "value": 0.7, "weight": 0.5, "is_active": True},
                        {"name": "sanctioned_country_origin", "value": False, "weight": -0.3, "is_active": True}
                    ],
                    "metadata": {
                        "account_age_days": 730,
                        "total_volume_usd": 150000.0,
                        "transaction_count_last_30_days": 50
                    }
                }
            ]
        }
    }


class ScoreResult(MongoBaseModel):
    """Result model for a ScoreLab score calculation."""

    entity_id: str = Field(description="The unique identifier of the entity that was scored.")
    probability_score: float = Field(
        ge=0.0, le=1.0, description="The calculated probability score P(x), ranging from 0.0 to 1.0."
    )
    raw_score: float = Field(description="The raw numerical score before normalization to P(x).")
    algorithm_version: str = Field(description="Version of the scoring algorithm used.")
    flags_used: List[FlagWithValue] = Field(description="The flags and their values that contributed to this score.")
    metadata_used: Dict[str, Any] = Field(description="The metadata that contributed to this score.")
    summary: str = Field(description="A brief summary or interpretation of the score.")
