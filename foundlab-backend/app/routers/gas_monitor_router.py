from typing import List

from fastapi import APIRouter, Body, HTTPException, Query, status

from app.models.gas_monitor import (
    GasConsumptionRecord,
    GasMonitorAnalysisResult,
    IngestGasConsumptionInput,
)
from app.services.gas_monitor_service import GasMonitorService

router = APIRouter()


@router.post(
    "/ingest",
    response_model=GasConsumptionRecord,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest new gas consumption record",
)
async def ingest_gas_consumption(record: IngestGasConsumptionInput):
    try:
        gas_monitor_service = GasMonitorService()
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
    limit: int = Query(10, ge=1, le=100),
    skip: int = Query(0, ge=0),
):
    try:
        gas_monitor_service = GasMonitorService()
        records = await gas_monitor_service.get_records_by_entity(entity_id, limit, skip)
        return records
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve records: {e}"
        )


@router.post(
    "/analyze/{entity_id}",
    response_model=GasMonitorAnalysisResult,
    summary="Analyze gas consumption patterns for an entity",
    response_description="Result of the gas consumption pattern anomaly analysis.",
)
async def analyze_gas_patterns(
    entity_id: str,
    lookback_days: int = Body(7, alias="lookBackDays", ge=1, le=90),
):
    try:
        gas_monitor_service = GasMonitorService()
        analysis_result = await gas_monitor_service.analyze_patterns(entity_id, lookback_days)
        return analysis_result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze gas patterns: {e}"
        )
