from typing import List

from fastapi import APIRouter, HTTPException, Path, status, Body

from app.models.dfc import (
    DynamicFlagCreate,
    DynamicFlagUpdate,
    FlagApplicationInput,
    FlagApplyResponse,
    FlagDefinition,
)
from app.services.dfc_service import DFCService

router = APIRouter()


@router.post(
    "/definitions",
    response_model=FlagDefinition,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new dynamic flag definition",
)
async def create_flag_definition(flag_data: DynamicFlagCreate):
    dfc_service = DFCService()
    try:
        new_flag = await dfc_service.create_flag_definition(flag_data.model_dump())
        if not new_flag:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=f"Flag '{flag_data.name}' already exists."
            )
        return new_flag
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create flag definition: {e}"
        )


@router.get(
    "/definitions",
    response_model=List[FlagDefinition],
    summary="Retrieve all dynamic flag definitions",
)
async def get_all_flag_definitions():
    dfc_service = DFCService()
    try:
        flags = await dfc_service.get_all_flag_definitions()
        return flags
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve flag definitions: {e}"
        )


@router.get(
    "/definitions/{flag_name}",
    response_model=FlagDefinition,
    summary="Retrieve a dynamic flag definition by name",
)
async def get_flag_definition_by_name(flag_name: str = Path(..., description="Name of the flag definition to retrieve")):
    dfc_service = DFCService()
    flag = await dfc_service.get_flag_definition_by_name(flag_name)
    if not flag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flag definition not found.")
    return flag


@router.put(
    "/definitions/{flag_name}",
    response_model=FlagDefinition,
    summary="Update an existing dynamic flag definition",
)
async def update_flag_definition(
    flag_name: str = Path(..., description="Name of the flag definition to update"),
    flag_data: DynamicFlagUpdate = Body(..., description="New data for the flag definition"),
):
    dfc_service = DFCService()
    updated_flag = await dfc_service.update_flag_definition(
        flag_name, flag_data.model_dump(exclude_unset=True)
    )
    if not updated_flag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flag definition not found.")
    return updated_flag


@router.delete(
    "/definitions/{flag_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a dynamic flag definition",
)
async def delete_flag_definition(flag_name: str = Path(..., description="Name of the flag definition to delete")):
    dfc_service = DFCService()
    deleted_count = await dfc_service.delete_flag_definition(flag_name)
    if deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flag definition not found.")
    return


@router.post(
    "/apply",
    response_model=FlagApplyResponse,
    summary="Apply dynamic flags to an entity based on provided metadata",
)
async def apply_dynamic_flags(input_data: FlagApplicationInput):
    dfc_service = DFCService()
    try:
        result = await dfc_service.apply_flags_to_entity(
            input_data.entity_id, input_data.metadata
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply flags: {e}"
        )
