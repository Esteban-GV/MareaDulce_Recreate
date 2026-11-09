from fastapi import APIRouter, Response, status
from src.core.config import settings
from src.core.metrics import get_metrics_response
from src.infrastructure.database import get_raw_connection

router = APIRouter(tags=["Sistema"])

@router.get("/healthz", summary="Liveness Probe de Kubernetes")
def healthz():
    """Comprueba que el proceso esté vivo y el hilo de ejecución responda."""
    return {"status": "ok", "service": "marea-dulce-backend", "version": settings.VERSION}

@router.get("/ready", summary="Readiness Probe de Kubernetes")
def ready():
    """Comprueba que la base de datos SQLite esté conectada y lista para recibir tráfico."""
    try:
        conn = get_raw_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        cursor.fetchone()
        conn.close()
        return {"status": "ready", "database": "connected", "version": settings.VERSION}
    except Exception as e:
        return Response(
            content=f'{{"status":"not_ready","error":"{str(e)}"}}',
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json"
        )

@router.get("/api/v1/version", summary="Información de Versión y Arquitectura")
def get_version():
    """Retorna la versión activa de la API y metadatos de despliegue Recreate."""
    return {
        "version": settings.VERSION,
        "environment": settings.ENV,
        "deployment_strategy": "Recreate",
        "database": "SQLite WAL on PVC ReadWriteOnce",
        "demo_mode": settings.DEMO_MODE
    }

@router.get("/metrics", summary="Endpoint de Métricas Prometheus")
def metrics():
    """Expone métricas del microservicio para Prometheus Operator / ServiceMonitor."""
    data, content_type = get_metrics_response()
    return Response(content=data, media_type=content_type)

@router.get("/simulate/error", summary="Simulación de Errores HTTP para Alertas")
def simulate_error(status_code: int = 500):
    """Simula una respuesta de error para verificar alertas de Prometheus y Grafana."""
    return Response(
        content=f'{{"simulated_error": true, "code": {status_code}}}',
        status_code=status_code,
        media_type="application/json"
    )

@router.get("/simulate/cpu", summary="Simulación de Carga CPU")
def simulate_cpu(duration_seconds: int = 3):
    """Genera consumo de CPU sintético para probar telemetría de recursos."""
    import time
    end_time = time.time() + min(duration_seconds, 15)
    while time.time() < end_time:
        _ = [x ** 2 for x in range(10000)]
    return {"simulated_cpu": True, "duration_seconds": duration_seconds}
