from datetime import datetime
from typing import Literal, Optional, List

from pydantic import BaseModel, Field

from app.models.base import MongoBaseModel


class GasConsumptionRecord(MongoBaseModel):
    """
    Represents a single record of gas consumption for a transaction.
    """

    transaction_hash: str = Field(description="Unique hash of the transaction.")
    entity_id: str = Field(description="Identifier of the entity (wallet address, user ID) associated with the transaction.")
    gas_used: int = Field(gt=0, description="Amount of gas consumed by the transaction.")
    gas_price_gwei: int = Field(gt=0, description="Gas price in Gwei at the time of the transaction.")
    block_number: int = Field(gt=0, description="Block number where the transaction was included.")
    timestamp: datetime = Field(description="Timestamp of the transaction.")
    chain_id: Optional[int] = Field(None, description="Blockchain network ID (e.g., 1 for Ethereum Mainnet).")
    transaction_type: Optional[str] = Field(None, description="Type of transaction (e.g., 'ERC20 Transfer', 'Contract Interaction').")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "transaction_hash": "0xabc123def456...",
                    "entity_id": "0x123abc...",
                    "gas_used": 50000,
                    "gas_price_gwei": 30,
                    "block_number": 12345678,
                    "timestamp": "2023-10-26T10:00:00Z",
                    "chain_id": 1,
                    "transaction_type": "ERC20 Transfer"
                }
            ]
        }
    }


class IngestGasConsumptionInput(BaseModel):
    """Input model for ingesting gas consumption data."""

    transaction_hash: str
    entity_id: str
    gas_used: int
    gas_price_gwei: int
    block_number: int
    timestamp: datetime
    chain_id: Optional[int] = None
    transaction_type: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": GasConsumptionRecord.model_config["json_schema_extra"]["examples"]
        }
    }


class GasPatternAnomaly(BaseModel):
    """
    Represents a detected anomaly in gas consumption patterns.
    """

    entity_id: str = Field(description="Entity for which the anomaly was detected.")
    anomaly_type: Literal["high_gas_spike", "low_gas_deviation", "unusual_pattern"] = Field(
        description="Type of anomaly detected."
    )
    score: float = Field(ge=0.0, le=1.0, description="Anomaly score, higher indicates stronger anomaly.")
    description: str = Field(description="A human-readable description of the anomaly.")
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    transactions_involved: Optional[List[str]] = Field(
        None, description="List of transaction hashes involved in the anomaly."
    )


class GasMonitorAnalysisResult(BaseModel):
    """
    Response model for gas pattern analysis.
    """

    entity_id: str
    analysis_period_start: datetime
    analysis_period_end: datetime
    total_transactions_analyzed: int
    anomalies: List[GasPatternAnomaly]
    summary_message: str
