from typing import List

from fastapi import APIRouter, Body, HTTPException, Query, status

from app.models.gas_monitor import (
    GasConsumptionRecord,
    GasMonitorAnalysisResult,
    IngestGasConsumptionInput,
)
from app.services.gas_monitor_service import GasMonitorService

router = APIRouter()
gas_monitor_service = GasMonitorService()


@router.post(
    "/ingest",
    response_model=GasConsumptionRecord,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest new gas consumption record",
)
async def ingest_gas_consumption(record: IngestGasConsumptionInput):
    """
    Ingests a new gas consumption record into the GasMonitor system.
    This data will be used for pattern analysis and fraud detection.
    """
    try:
        new_record = await gas_monitor_service.ingest_record(record.model_dump())
        return new_record
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest gas consumption record: {e}",
        )


@router.get(
    "/records/{entity_id}",
    response_model=List[GasConsumptionRecord],
    summary="Retrieve gas consumption records for an entity",
)
async def get_records_for_entity(
    entity_id: str,
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
):
    """
    Retrieves a list of gas consumption records for a specific entity ID.
    Supports pagination.
    """
    try:
        records = await gas_monitor_service.get_records_by_entity(entity_id, limit, skip)
        return records
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve records: {e}"
        )


@router.post(
    "/analyze/{entity_id}",
    response_model=GasMonitorAnalysisResult,
    summary="Analyze gas consumption patterns for an entity",
    response_description="Result of the gas consumption pattern anomaly analysis.",
)
async def analyze_gas_patterns(
    entity_id: str,
    lookback_days: int = Body(
        7,
        alias="lookBackDays",
        ge=1,
        le=90,
        description="Number of days to look back for analysis (e.g., 7 for last week's data).",
    ),
):
    """
    Analyzes historical gas consumption patterns for a given entity to detect anomalies.

    **Current Logic (Simple Placeholder):**
    This implementation performs a basic anomaly check by comparing recent total gas consumption
    against a simple average (e.g., average of previous daily totals).
    It will flag if the current total deviates significantly. For a real-world system,
    this would involve more sophisticated statistical models (e.g., Z-score, clustering)
    or machine learning algorithms.

    **Future Enhancements (Pseudocode Concept):**
    ```python
    # 1. Fetch historical data for entity_id within lookback_days
    #    records = db.collection.find({"entity_id": entity_id, "timestamp": {"$gte": start_date, "$lte": end_date}})

    # 2. Extract features:
    #    - Daily total gas
    #    - Number of transactions per day
    #    - Average gas per transaction
    #    - Gas price volatility
    #    - Transaction type distribution

    # 3. Apply anomaly detection model:
    #    - For simple patterns: calculate moving averages and standard deviations.
    #      flag_if_deviation_gt_3_sigma(current_gas, historical_avg, historical_std_dev)
    #    - For complex patterns (ML):
    #      - Train an Isolation Forest or One-Class SVM on "normal" behavior.
    #      - Use a time-series anomaly detection model (e.g., ARIMA with anomalies, Prophet).
    #      - Cluster similar entities and detect deviations from the cluster norm.

    # 4. Generate anomaly report based on detected flags and their severity.
    ```
    """
    try:
        analysis_result = await gas_monitor_service.analyze_patterns(entity_id, lookback_days)
        return analysis_result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze gas patterns: {e}",
        )
