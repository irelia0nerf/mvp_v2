from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

from app.common.health import router as health_router
from app.config import settings
from app.database import close_mongo_connection, connect_to_mongo, get_collection
from app.routers import (
    dfc_router,
    gas_monitor_router,
    nft_router,
    risk_router,
    score_router,
    sherlock_router,
    audit_router,
)

# Middleware de autenticação + log auditoria
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        public_paths = ["/health", "/docs", "/redoc", "/openapi.json", "/painel", "/audit"]
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)

        token = request.headers.get("Authorization")
        if token != settings.API_AUTH_TOKEN:
            raise HTTPException(status_code=401, detail="Unauthorized: Invalid or missing token")

        shadow_mode = request.query_params.get("shadow") == "true"
        request.state.shadow = shadow_mode

        response = await call_next(request)

        try:
            collection = get_collection("audit_logs")
            log = {
                "path": request.url.path,
                "method": request.method,
                "headers": dict(request.headers),
                "query_params": dict(request.query_params),
                "status_code": response.status_code,
                "timestamp": datetime.utcnow(),
                "shadow": shadow_mode
            }
            await collection.insert_one(log)
        except Exception as e:
            print(f"Erro ao registrar audit log: {e}")

        return response

# Conexão e desconexão com o MongoDB
@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

# Instância principal
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend para a infraestrutura de reputação digital FoundLab",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware e rotas
app.add_middleware(AuthMiddleware)
app.include_router(health_router, prefix="", tags=["Monitoring"])
app.include_router(score_router.router, prefix="/scores", tags=["ScoreLab"])
app.include_router(dfc_router.router, prefix="/flags", tags=["DFC"])
app.include_router(sherlock_router.router, prefix="/sherlock", tags=["Sherlock"])
app.include_router(nft_router.router, prefix="/nft", tags=["SigilMesh"])
app.include_router(risk_router.router, prefix="/sentinela", tags=["Sentinela"])
app.include_router(gas_monitor_router.router, prefix="/gasmonitor", tags=["GasMonitor"])
app.include_router(audit_router.router, prefix="", tags=["AuditLog"])

# Painel técnico com template HTML
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "static")

@app.get("/painel", response_class=HTMLResponse)
async def painel(request: Request):
    collection = get_collection("audit_logs")
    logs_cursor = collection.find().sort("timestamp", -1)
    logs = []
    async for log in logs_cursor:
        log["_id"] = str(log["_id"])
        logs.append(log)
    return templates.TemplateResponse("audit_panel.html", {"request": request, "logs": logs})

# Swagger com token
from fastapi.openapi.models import APIKey

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    try:
        openapi_schema = get_openapi(
            title=settings.APP_NAME,
            version=settings.APP_VERSION,
            description="Backend para a infraestrutura de reputação digital FoundLab",
            routes=app.routes,
        )
        openapi_schema["components"]["securitySchemes"] = {
            "APIKeyHeader": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization"
            }
        }
        openapi_schema["security"] = [{"APIKeyHeader": []}]
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    except Exception as e:
        import traceback
        print("⚠️ OPENAPI ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to generate OpenAPI schema")

app.openapi = custom_openapi
