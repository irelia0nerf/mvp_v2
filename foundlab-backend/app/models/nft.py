from typing import Dict, List, Optional, Literal

from pydantic import BaseModel, Field
from pydantic_extra_types.color import Color


class SigilMeshNFTMetadata(BaseModel):
    """
    Schema for the NFT metadata, compliant with common standards (e.g., OpenSea).
    """

    name: str = Field(description="Name of the NFT.")
    description: str = Field(description="Description of the NFT, often including context about the reputation.")
    image: Optional[str] = Field(
        None, description="URL to the SVG or PNG image of the NFT. Can be IPFS."
    )
    external_url: Optional[str] = Field(
        None, description="A URL where users can learn more about the NFT and its associated entity."
    )
    attributes: List[Dict[str, str | float | int]] = Field(
        default_factory=list,
        description="Array of key-value pairs that are displayed as traits. "
        "Standard format: `{'trait_type': 'string', 'value': 'string/number'}`",
    )
    background_color: Optional[Color] = Field(  # Usando Pydantic Color para validação
        None,
        description="Background color for the item on OpenSea (e.g., '#FF00FF'). Must be a valid hex color.",
    )
    animation_url: Optional[str] = Field(None, description="URL to a multimedia attachment for the NFT. Can be IPFS.")
    youtube_url: Optional[str] = Field(
        None, description="A URL to a YouTube video for the NFT."
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "FoundLab Reputational Sigil #12345",
                    "description": "Reputation score of 0.95 for address 0x123abc...",
                    "image": "https://ipfs.io/ipfs/QmVG...",
                    "external_url": "https://foundlab.io/entity/0x123abc...",
                    "attributes": [
                        {"trait_type": "Probability Score", "value": 0.95},
                        {"trait_type": "Risk Tier", "value": "Low"},
                        {"trait_type": "KYC Verified", "value": "Yes"},
                        {"trait_type": "Evaluation Date", "value": "2023-10-26"}
                    ],
                    "background_color": "#00FF00"
                }
            ]
        }
    }


class CreateSigilMeshNFTInput(BaseModel):
    """
    Input model for creating SigilMesh NFT metadata.
    """

    entity_id: str = Field(description="The unique identifier of the entity whose reputation is being tokenized.")
    score_id: str = Field(description="The ID of the ScoreLab evaluation result to associate with this NFT.")
    custom_name: Optional[str] = Field(None, description="Optional custom name for the NFT.")
    custom_description: Optional[str] = Field(None, description="Optional custom description for the NFT.")
    image_url: Optional[str] = Field(None, description="Optional URL for the NFT image.")
    background_color: Optional[Color] = Field(None, description="Optional custom background color for the NFT.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "entity_id": "0x123abc456def789",
                    "score_id": "653a0f7c2b1e4d5a6f7b8c9d",
                    "custom_name": "My KYC Verified Investor Sigil",
                    "custom_description": "A customized Sigil for a verified investor with high reputation.",
                    "background_color": "#228B22"  # Forest green
                }
            ]
        }
    }


class SigilMeshNFTOutput(BaseModel):
    """
    Output model for SigilMesh NFT metadata creation, including the generated metadata.
    """

    entity_id: str
    score_id: str
    nft_metadata: SigilMeshNFTMetadata
    message: str = "NFT metadata generated successfully."
