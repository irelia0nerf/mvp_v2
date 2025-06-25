from fastapi import APIRouter, Body, HTTPException, status

from app.models.nft import CreateSigilMeshNFTInput, SigilMeshNFTOutput
from app.services.nft_service import SigilMeshService

router = APIRouter()

@router.post(
    "/metadata",
    response_model=SigilMeshNFTOutput,
    status_code=status.HTTP_201_CREATED,
    summary="Generate SigilMesh NFT metadata",
    response_description="Generated NFT metadata for a given entity and score.",
)
async def generate_sigilmesh_nft_metadata(input_data: CreateSigilMeshNFTInput = Body(...)):
    """
    Generates NFT metadata (compatible with standards like OpenSea) for an entity
    based on a previously calculated ScoreLab score.

    This endpoint retrieves the specified score and incorporates it, along with other
    entity-related data, into a structured JSON metadata block. This JSON is what
    would typically be uploaded to IPFS and referenced by an NFT smart contract.

    **Note:** This endpoint *generates metadata*, it does *not* mint an actual NFT on the blockchain.
    """
    try:
        sigilmesh_service = SigilMeshService()  # ✅ Criação tardia da instância após conexão Mongo
        nft_output = await sigilmesh_service.generate_nft_metadata(
            input_data.entity_id,
            input_data.score_id,
            input_data.custom_name,
            input_data.custom_description,
        )
        return nft_output
    except HTTPException as e:
        raise e  # Re-raise HTTPExceptions from service layer
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate NFT metadata: {e}"
        )
