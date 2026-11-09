import os
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from src.core.config import settings
from src.core.metrics import HTTP_REQUESTS_TOTAL, HTTP_REQUEST_DURATION_SECONDS, APP_VERSION_INFO
from src.infrastructure.migrations import run_migrations
from src.infrastructure.seed import seed_database
from src.routers import system, auth, categories, products, orders, custom_orders, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("marea.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación Marea Dulce: migraciones e inicialización."""
    logger.info("Iniciando Marea Dulce Cloud-Native v%s...", settings.VERSION)
    try:
        # 1. Aplicar migraciones estructurales con respaldo e integridad SQLite
        run_migrations()
        # 2. Cargar datos iniciales del catálogo oficial de pastelería
        seed_database()
        schema_ver = "v2" if settings.VERSION.startswith("2") else "v1"
        APP_VERSION_INFO.labels(
            version=settings.VERSION,
            schema_version=schema_ver,
            strategy="Recreate"
        ).set(1)
        logger.info("Persistencia y catálogo oficial inicializados correctamente en SQLite WAL.")
    except Exception as e:
        logger.error("Fallo crítico en inicialización: %s", e, exc_info=True)
        raise e
    yield
    logger.info("Cerrando Marea Dulce API...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Plataforma de comercio electrónico de pastelería artesanal Cloud-Native sobre Kubernetes (Estrategia Recreate).",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de Métricas Prometheus
@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    start_time = time.time()
    endpoint = request.url.path
    method = request.method
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        status_code = str(response.status_code)
        
        if endpoint != "/metrics":
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=endpoint,
                status=status_code,
                version=settings.VERSION
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method,
                endpoint=endpoint,
                version=settings.VERSION
            ).observe(duration)
            
        return response
    except Exception as e:
        duration = time.time() - start_time
        HTTP_REQUESTS_TOTAL.labels(
            method=method,
            endpoint=endpoint,
            status="500",
            version=settings.VERSION
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=method,
            endpoint=endpoint,
            version=settings.VERSION
        ).observe(duration)
        raise e

# Montaje de Enrutadores de la API
app.include_router(system.router)
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(custom_orders.router)
app.include_router(admin.router)

# Ruta estática de activos del Frontend SPA (JS, CSS, SVGs)
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(STATIC_DIR):
    # Montar directorio assets si existe
    assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # Fallback SPA para todas las rutas del navegador
    @app.get("/{full_path:path}", tags=["Frontend SPA"])
    async def serve_spa(full_path: str):
        # Excluir rutas de API y métricas
        if full_path.startswith("api/") or full_path in ("healthz", "ready", "metrics", "docs", "openapi.json"):
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Not Found"})
            
        # Si es un archivo específico existente en static (ej. favicon.svg)
        target_file = os.path.join(STATIC_DIR, full_path)
        if full_path and os.path.isfile(target_file):
            return FileResponse(target_file)
            
        # Retornar el index.html de React
        index_file = os.path.join(STATIC_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
            
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Frontend no disponible"})
