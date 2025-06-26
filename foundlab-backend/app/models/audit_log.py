from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class AuditLog(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    endpoint: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    entity_id: Optional[str]
    fallback_override: bool = False