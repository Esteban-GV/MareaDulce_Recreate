import os
import time
import socket
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

# ==============================================================================
# Variables de Configuración y Entorno
# ==============================================================================
APP_VERSION = os.getenv("APP_VERSION", "v1.0.0")
APP_ENV = os.getenv("APP_ENV", "production")
APP_COLOR = os.getenv("APP_COLOR", "#1e3a8a" if APP_VERSION.startswith("v1") else "#14532d")
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
POD_NAME = os.getenv("POD_NAME", socket.gethostname())
POD_IP = os.getenv("POD_IP", "127.0.0.1")
NODE_NAME = os.getenv("NODE_NAME", "minikube")

# ==============================================================================
# Métricas de Telemetría Prometheus (Modelo RED y Estado)
# ==============================================================================
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total acumulado de peticiones HTTP atendidas por la aplicacion",
    ["method", "endpoint", "status_code", "version"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Distribucion de latencia en peticiones HTTP",
    ["method", "endpoint", "version"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

APP_INFO_GAUGE = Gauge(
    "app_version_info",
    "Informacion de version y metadatos de la carga de trabajo",
    ["version", "environment", "pod_name", "node_name"],
)
APP_INFO_GAUGE.labels(
    version=APP_VERSION,
    environment=APP_ENV,
    pod_name=POD_NAME,
    node_name=NODE_NAME,
).set(1)

PVC_OPERATIONS_TOTAL = Counter(
    "app_pvc_storage_operations_total",
    "Total de operaciones de lectura y escritura sobre el volumen PVC",
    ["operation", "status"],
)

START_TIME = time.time()

# ==============================================================================
# Inicialización de FastAPI y Manejo de Almacenamiento Persistente
# ==============================================================================
app = FastAPI(
    title="K8s Recreate Demo Application",
    description="Microservicio de demostracion para despliegue Recreate y Observabilidad",
    version=APP_VERSION,
)


def get_and_increment_counter() -> int:
    """Gestiona un contador en el volumen persistente (PVC)."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        counter_file = DATA_DIR / "counter.txt"
        current_val = 0
        if counter_file.exists():
            content = counter_file.read_text().strip()
            current_val = int(content) if content.isdigit() else 0

        current_val += 1
        counter_file.write_text(str(current_val))
        PVC_OPERATIONS_TOTAL.labels(operation="write", status="success").inc()
        return current_val
    except Exception:
        PVC_OPERATIONS_TOTAL.labels(operation="write", status="error").inc()
        return -1


# ==============================================================================
# Middleware para Registro de Métricas RED
# ==============================================================================
@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    endpoint = request.url.path
    # Normalizar endpoints para evitar cardinalidad infinita en Prometheus
    if endpoint.startswith("/api/"):
        endpoint_label = "/api/*"
    elif endpoint.startswith("/simulate/"):
        endpoint_label = "/simulate/*"
    elif endpoint in ["/", "/healthz", "/ready", "/metrics", "/data"]:
        endpoint_label = endpoint
    else:
        endpoint_label = "other"

    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=endpoint_label,
        status_code=str(response.status_code),
        version=APP_VERSION,
    ).inc()

    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=request.method,
        endpoint=endpoint_label,
        version=APP_VERSION,
    ).observe(duration)

    return response


# ==============================================================================
# Endpoints de Aplicación
# ==============================================================================
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Interfaz visual de la aplicación para demostración en vivo."""
    counter_value = get_and_increment_counter()
    uptime = int(time.time() - START_TIME)
    is_v1 = APP_VERSION.startswith("v1")
    theme_accent = "#3b82f6" if is_v1 else "#22c55e"
    theme_bg = "#0f172a"

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Estrategia Recreate - {APP_VERSION}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: {theme_bg};
            color: #f8fafc;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            box-sizing: border-box;
        }}
        .card {{
            background: #1e293b;
            border-top: 6px solid {theme_accent};
            border-radius: 12px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
            max-width: 600px;
            width: 100%;
            padding: 32px;
        }}
        .badge {{
            display: inline-block;
            background-color: {theme_accent};
            color: #ffffff;
            font-weight: 700;
            font-size: 0.875rem;
            padding: 4px 12px;
            border-radius: 9999px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 16px;
        }}
        h1 {{
            font-size: 1.75rem;
            margin: 0 0 8px 0;
            color: #ffffff;
        }}
        p.subtitle {{
            color: #94a3b8;
            margin: 0 0 24px 0;
            font-size: 0.95rem;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 24px;
        }}
        .grid-item {{
            background: #0f172a;
            padding: 14px;
            border-radius: 8px;
            border: 1px solid #334155;
        }}
        .label {{
            font-size: 0.75rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
        }}
        .value {{
            font-size: 0.95rem;
            color: #e2e8f0;
            font-family: monospace;
            word-break: break-all;
        }}
        .pvc-box {{
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid {theme_accent};
            padding: 16px;
            border-radius: 8px;
            margin-top: 16px;
        }}
        .footer {{
            margin-top: 24px;
            font-size: 0.8rem;
            color: #64748b;
            text-align: center;
            border-top: 1px solid #334155;
            padding-top: 16px;
        }}
    </style>
</head>
<body>
    <div class="card">
        <span class="badge">Versión {APP_VERSION}</span>
        <h1>Estrategia de Despliegue: Recreate</h1>
        <p class="subtitle">Demostración en vivo y observabilidad en Kubernetes (Plataformas II)</p>

        <div class="grid">
            <div class="grid-item">
                <div class="label">Identificador de Pod</div>
                <div class="value">{POD_NAME}</div>
            </div>
            <div class="grid-item">
                <div class="label">Dirección IP del Pod</div>
                <div class="value">{POD_IP}</div>
            </div>
            <div class="grid-item">
                <div class="label">Nodo Host</div>
                <div class="value">{NODE_NAME}</div>
            </div>
            <div class="grid-item">
                <div class="label">Tiempo Activo (Uptime)</div>
                <div class="value">{uptime} segundos</div>
            </div>
        </div>

        <div class="pvc-box">
            <div class="label">Persistencia en Volumen (PVC en /data)</div>
            <div class="value" style="font-size: 1.1rem; color: #ffffff;">
                Contador acumulado de peticiones persistidas: <strong>{counter_value}</strong>
            </div>
            <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 6px;">
                Evidencia de conservación de datos entre versiones v1.0 y v2.0 tras recreación de réplicas.
            </div>
        </div>

        <div class="footer">
            Integrantes: Esteban Guarín Valencia | Juan José Arias Gallego
        </div>
    </div>
</body>
</html>
"""
    return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)


@app.get("/api/info", response_class=JSONResponse)
async def api_info() -> Dict[str, Any]:
    """Retorna los metadatos de la aplicación en formato JSON."""
    return {
        "version": APP_VERSION,
        "environment": APP_ENV,
        "pod_name": POD_NAME,
        "pod_ip": POD_IP,
        "node_name": NODE_NAME,
        "uptime_seconds": int(time.time() - START_TIME),
        "persistent_counter": get_and_increment_counter(),
    }


# ==============================================================================
# Sondas de Salud de Kubernetes (Liveness y Readiness)
# ==============================================================================
@app.get("/healthz", response_class=JSONResponse)
async def healthz():
    """Sonda de Actividad (livenessProbe): verifica si el proceso está vivo."""
    return {"status": "alive", "timestamp": time.time()}


@app.get("/ready", response_class=JSONResponse)
async def ready():
    """Sonda de Preparación (readinessProbe): verifica si el servicio acepta tráfico."""
    return {"status": "ready", "version": APP_VERSION}


# ==============================================================================
# Endpoint de Autenticación / Verificación de Identidad (SSO Requisito)
# ==============================================================================
@app.post("/api/auth/verify", response_class=JSONResponse)
async def auth_verify(request: Request):
    """Simulación de autenticación robusta / SSO mediante validación de token y contexto."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        return {
            "authenticated": True,
            "mechanism": "Single-Sign-On (SSO) / OAuth2 Token",
            "token_valid": bool(token),
            "user": "esteban.guarin@universidad.edu.co",
            "role": "Platform Engineer",
        }
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"authenticated": False, "error": "Token de autenticacion requerido"},
    )


# ==============================================================================
# Endpoint de Métricas Prometheus
# ==============================================================================
@app.get("/metrics")
async def metrics():
    """Endpoint oficial de scrape para Prometheus."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ==============================================================================
# Endpoints de Simulación para Pruebas de HPA y Alarmas
# ==============================================================================
@app.get("/simulate/cpu-load")
async def simulate_cpu_load(seconds: float = 1.0):
    """Genera consumo de CPU sintético para disparar métricas y probar el HPA."""
    end_time = time.time() + min(seconds, 5.0)
    # Ciclo de cálculo intensivo
    while time.time() < end_time:
        _ = [x ** 2 for x in range(2000)]
    return {"message": "Carga de CPU ejecutada satisfactoriamente", "duration_seconds": seconds}


@app.get("/simulate/error")
async def simulate_error(status_code: int = 500):
    """Genera errores HTTP controlados (500, 502, 503) para probar alarmas de tasa de error."""
    valid_status = status_code if status_code in [500, 502, 503, 504] else 500
    return JSONResponse(
        status_code=valid_status,
        content={"error": f"Fallo simulado con código HTTP {valid_status}", "pod": POD_NAME},
    )


@app.get("/simulate/latency")
async def simulate_latency(delay: float = 1.5):
    """Introduce latencia artificial para disparar alertas de degradación de respuesta."""
    sleep_time = min(max(delay, 0.1), 5.0)
    time.sleep(sleep_time)
    return {"message": "Respuesta con latencia completada", "delay_seconds": sleep_time}


