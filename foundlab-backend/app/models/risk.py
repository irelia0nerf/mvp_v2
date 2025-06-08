from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Literal, Any

from pydantic import BaseModel, Field

from app.models.base import MongoBaseModel


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskTrigger(MongoBaseModel):
    """Defines a specific risk trigger rule."""

    name: str = Field(description="Unique name for the risk trigger (e.g., 'HighScoreBelowThreshold').")
    description: str = Field(description="Description of what this trigger monitors.")
    trigger_type: Literal["score_threshold", "flag_presence", "custom_logic"] = Field(
        description="Type of condition that activates this trigger."
    )
    score_threshold: Optional[float] = Field(None, description="Score threshold (e.g., if score < 0.3 for 'HIGH' risk).")
    flag_name: Optional[str] = Field(None, description="Name of a DFC flag that triggers this risk.")
    custom_logic_params: Optional[Dict[str, Any]] = Field(None, description="Parameters for custom logic evaluation.")
    risk_level: RiskLevel = Field(description="Level of risk associated with this trigger.")
    is_active: bool = Field(True, description="Whether this trigger is currently active.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "critical_score_drop",
                    "description": "Triggers if the P(x) score falls below 0.1.",
                    "trigger_type": "score_threshold",
                    "score_threshold": 0.1,
                    "risk_level": "CRITICAL",
                    "is_active": True,
                },
                {
                    "name": "sanctioned_entity_flag_active",
                    "description": "Triggers if 'is_sanctioned_entity' flag is active.",
                    "trigger_type": "flag_presence",
                    "flag_name": "is_sanctioned_entity",
                    "risk_level": "CRITICAL",
                    "is_active": True,
                },
                {
                    "name": "suspicious_combo_risk",
                    "description": "Triggers for specific combined conditions (e.g., low score AND specific metadata).",
                    "trigger_type": "custom_logic",
                    "custom_logic_params": {"min_transaction_count": 5, "max_score": 0.3},
                    "risk_level": "HIGH",
                    "is_active": True,
                }
            ]
        }
    }


class RiskAssessmentInput(BaseModel):
    """Input for assessing risk."""

    entity_id: str = Field(description="The unique identifier of the entity to assess risk for.")
    score_id: str = Field(description="The ID of the ScoreLab evaluation result to use for assessment.")
    additional_context: Optional[Dict[str, Any]] = Field(
        None, description="Any additional context (e.g., transaction details) for deeper risk analysis."
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "entity_id": "user_123",
                    "score_id": "some_score_id_here",
                    "additional_context": {
                        "user_daily_transactions": 7,
                        "last_kyc_date": "2023-01-15"
                    }
                }
            ]
        }
    }


class RiskTriggerDetail(BaseModel):
    """Details about a specific trigger that was activated."""

    trigger_name: str
    risk_level: RiskLevel
    reason: str
    activated_at: datetime = Field(default_factory=datetime.utcnow)


class RiskAssessmentResult(MongoBaseModel):
    """Result of a risk assessment by Sentinela."""

    entity_id: str = Field(description="The ID of the entity that was assessed.")
    score_id: str = Field(description="The ID of the ScoreLab evaluation result used.")
    overall_risk_level: RiskLevel = Field(description="The highest risk level identified for the entity.")
    triggered_rules: List[RiskTriggerDetail] = Field(
        default_factory=list, description="List of specific risk triggers that were activated."
    )
    summary_message: str = Field(description="A concise summary of the risk assessment.")


class CreateRiskTrigger(BaseModel):
    name: str
    description: str
    trigger_type: Literal["score_threshold", "flag_presence", "custom_logic"]
    score_threshold: Optional[float] = None
    flag_name: Optional[str] = None
    custom_logic_params: Optional[Dict[str, Any]] = None
    risk_level: RiskLevel
    is_active: bool = True

    model_config = {
        "json_schema_extra": {
            "examples": RiskTrigger.model_config["json_schema_extra"]["examples"]
        }
    }


class UpdateRiskTrigger(BaseModel):
    description: Optional[str] = None
    trigger_type: Optional[Literal["score_threshold", "flag_presence", "custom_logic"]] = None
    score_threshold: Optional[float] = None
    flag_name: Optional[str] = None
    custom_logic_params: Optional[Dict[str, Any]] = None
    risk_level: Optional[RiskLevel] = None
    is_active: Optional[bool] = None
