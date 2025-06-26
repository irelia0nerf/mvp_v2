from app.database import get_collection
from app.models.audit_log import AuditLog

class AuditLogService:
    def __init__(self):
        self.collection = get_collection("audit_logs")

    async def log_call(self, endpoint: str, input_data, output_data, entity_id=None, fallback_override=False):
        log = AuditLog(
            endpoint=endpoint,
            input_data=input_data,
            output_data=output_data,
            entity_id=entity_id,
            fallback_override=fallback_override,
        )
        await self.collection.insert_one(log.model_dump())