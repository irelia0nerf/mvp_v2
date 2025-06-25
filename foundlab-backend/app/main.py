from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.common.health import router as health_router
from app.config import settings
from app.database import close_mongo_connection, connect_to_mongo
from app.routers import (
    dfc_router,
    gas_monitor_router,
    nft_router,
    risk_router,
    score_router,
    sherlock_router,
)

# Middleware de autenticação via token
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        public_paths = ["/health", "/docs", "/redoc", "/openapi.json"]
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)

        token = request.headers.get("Authorization")
        if token != settings.API_AUTH_TOKEN:
            raise HTTPException(status_code=401, detail="Unauthorized: Invalid or missing token")
        return await call_next(request)

# Conexão e desconexão com o MongoDB
@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

# Criação da instância principal
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend para a infraestrutura de reputação digital FoundLab",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Adiciona o middleware de autenticação
app.add_middleware(AuthMiddleware)

# Rotas principais
app.include_router(health_router, prefix="", tags=["Monitoring"])
app.include_router(score_router.router, prefix="/scores", tags=["ScoreLab"])
app.include_router(dfc_router.router, prefix="/flags", tags=["DFC"])
app.include_router(sherlock_router.router, prefix="/sherlock", tags=["Sherlock"])
app.include_router(nft_router.router, prefix="/nft", tags=["SigilMesh"])
app.include_router(risk_router.router, prefix="/sentinela", tags=["Sentinela"])
app.include_router(gas_monitor_router.router, prefix="/gasmonitor", tags=["GasMonitor"])

# Configuração do Swagger UI para aceitar token via header
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.models import APIKey, APIKeyIn, SecuritySchemeType

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
