from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Métricas de Versión y Arquitectura de Despliegue
APP_VERSION_INFO = Gauge(
    "app_version_info",
    "Información de versión de aplicación y esquema de datos activa",
    ["version", "schema_version", "strategy"]
)

# Métricas de Tráfico HTTP (RED)
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total de peticiones HTTP procesadas por el backend",
    ["method", "endpoint", "status", "version"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Duración de las peticiones HTTP en segundos",
    ["method", "endpoint", "version"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 10.0]
)

# Métricas de Negocio E-Commerce
MAREA_ORDERS_TOTAL = Counter(
    "marea_orders_total",
    "Total acumulado de órdenes registradas en Marea Dulce",
    ["status", "schema_version"]
)

MAREA_REVENUE_COP_TOTAL = Counter(
    "marea_revenue_cop_total",
    "Ingresos totales acumulados en Pesos Colombianos (COP)"
)

MAREA_INVENTORY_STOCK = Gauge(
    "marea_inventory_stock",
    "Nivel actual de inventario por producto",
    ["product_id", "product_name"]
)

MAREA_ACTIVE_SESSIONS = Gauge(
    "marea_active_sessions",
    "Número estimado de usuarios activos en la tienda"
)

# Métricas de Almacenamiento y Concurrencia SQLite en PVC
MAREA_DB_OPERATIONS_TOTAL = Counter(
    "marea_db_operations_total",
    "Operaciones de base de datos SQLite en disco persistente",
    ["operation", "status"]
)

MAREA_DB_STORAGE_ERRORS_TOTAL = Counter(
    "marea_db_storage_errors_total",
    "Errores de acceso o escritura en el volumen persistente PVC"
)

def get_metrics_response():
    """Genera la respuesta formateada para Prometheus."""
    return generate_latest(), CONTENT_TYPE_LATEST
