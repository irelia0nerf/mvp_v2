from fastapi import APIRouter
from app.services.audit_log_service import AuditLogService

router = APIRouter()

@router.get("/audit")
async def get_logs():
    audit_service = AuditLogService()
    logs = []
    cursor = audit_service.collection.find().sort("timestamp", -1)
    async for log in cursor:
        log["_id"] = str(log["_id"])  # Converter ObjectId para string
        logs.append(log)
    return logs
