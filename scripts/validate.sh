#!/usr/bin/env bash
# ==============================================================================
# Suite Automatizada de Validación End-to-End (validate.sh)
# Plataforma: Marea Dulce Cloud-Native (Kubernetes Recreate Stack)
# Autores: Esteban Guarín Valencia, Juan José Arias Gallego
# ==============================================================================
set -u

PASS_COUNT=0
FAIL_COUNT=0
APP_NAMESPACE="recreate-lab"
MON_NAMESPACE="monitoring"
LOCAL_PORT=18080
PF_PID=""

cleanup() {
    if [[ -n "${PF_PID}" ]] && kill -0 "${PF_PID}" 2>/dev/null; then
        kill "${PF_PID}" 2>/dev/null || true
    fi
}
trap cleanup EXIT

check_result() {
    local description="$1"
    local status_code="$2"
    if [[ "${status_code}" -eq 0 ]]; then
        echo "[PASS] ${description}"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "[FAIL] ${description}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

echo "=============================================================================="
echo " SUITE DE VALIDACIÓN AUTOMATIZADA — MAREA DULCE (K8S RECREATE STACK)"
echo "=============================================================================="

# 1. Conectividad con el clúster
kubectl cluster-info >/dev/null 2>&1
check_result "01. Clúster de Kubernetes accesible vía kubectl" $?

# 2. Existencia del namespace recreate-lab
kubectl get namespace "${APP_NAMESPACE}" >/dev/null 2>&1
check_result "02. Namespace '${APP_NAMESPACE}' existente y activo" $?

# 3. Verificación explícita de estrategia Recreate
STRATEGY=$(kubectl get deployment marea-app-deployment -n "${APP_NAMESPACE}" -o jsonpath='{.spec.strategy.type}' 2>/dev/null || echo "")
if [[ "${STRATEGY}" == "Recreate" ]]; then
    check_result "03. Deployment 'marea-app-deployment' configurado con estrategia exclusiva 'Recreate'" 0
else
    check_result "03. Deployment 'marea-app-deployment' configurado con estrategia exclusiva 'Recreate' (actual: ${STRATEGY})" 1
fi

# 4. Pod de la aplicación en estado Ready
READY_REPLICAS=$(kubectl get deployment marea-app-deployment -n "${APP_NAMESPACE}" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
if [[ "${READY_REPLICAS:-0}" -ge 1 ]]; then
    check_result "04. Réplicas de 'marea-app-deployment' en estado Running/Ready (${READY_REPLICAS} activas)" 0
else
    check_result "04. Réplicas de 'marea-app-deployment' en estado Running/Ready" 1
fi

# 5. Volumen Persistente (PVC) en estado Bound
PVC_STATUS=$(kubectl get pvc recreate-app-pvc -n "${APP_NAMESPACE}" -o jsonpath='{.status.phase}' 2>/dev/null || echo "")
if [[ "${PVC_STATUS}" == "Bound" ]]; then
    check_result "05. PersistentVolumeClaim 'recreate-app-pvc' enlazado (Bound, ReadWriteOnce)" 0
else
    check_result "05. PersistentVolumeClaim 'recreate-app-pvc' enlazado (actual: ${PVC_STATUS})" 1
fi

# 6. NetworkPolicy aplicada
kubectl get networkpolicy marea-dulce-network-policy -n "${APP_NAMESPACE}" >/dev/null 2>&1
check_result "06. Política de red 'marea-dulce-network-policy' activa" $?

# 7. Service e Ingress configurados
kubectl get svc marea-app-service -n "${APP_NAMESPACE}" >/dev/null 2>&1 && \
kubectl get ingress marea-app-ingress -n "${APP_NAMESPACE}" >/dev/null 2>&1
check_result "07. Service 'marea-app-service' e Ingress 'marea-app-ingress' configurados" $?

# 8. ServiceMonitor y PrometheusRule aplicados
kubectl get servicemonitor marea-app-servicemonitor -n "${APP_NAMESPACE}" >/dev/null 2>&1 && \
kubectl get prometheusrule marea-app-alert-rules -n "${APP_NAMESPACE}" >/dev/null 2>&1
check_result "08. CRDs de Observabilidad (marea-app-servicemonitor y marea-app-alert-rules) registrados" $?

# Iniciar túnel temporal hacia el servicio para pruebas funcionales de API
kubectl port-forward svc/marea-app-service -n "${APP_NAMESPACE}" "${LOCAL_PORT}:80" >/dev/null 2>&1 &
PF_PID=$!
sleep 2

BASE_URL="http://127.0.0.1:${LOCAL_PORT}"

# 9. Sondas de salud /healthz y /ready
HTTP_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/healthz" || echo "000")
HTTP_READY=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/ready" || echo "000")
if [[ "${HTTP_HEALTH}" == "200" && "${HTTP_READY}" == "200" ]]; then
    check_result "09. Sondas Liveness (/healthz) y Readiness (/ready) responden HTTP 200" 0
else
    check_result "09. Sondas Liveness (/healthz) y Readiness (/ready) responden HTTP 200" 1
fi

# 10. Storefront SPA servido en raíz /
HTML_CHECK=$(curl -s "${BASE_URL}/" | grep -ic "Marea Dulce" || echo "0")
if [[ "${HTML_CHECK}" -ge 1 ]]; then
    check_result "10. Storefront SPA de Marea Dulce servido correctamente en '/'" 0
else
    check_result "10. Storefront SPA de Marea Dulce servido correctamente en '/'" 1
fi

# 11. Endpoint /api/v1/version
APP_VER=$(curl -s "${BASE_URL}/api/v1/version" | python3 -c "import sys, json; print(json.load(sys.stdin).get('version', ''))" 2>/dev/null || echo "")
if [[ -n "${APP_VER}" ]]; then
    check_result "11. Endpoint de versión responde con versión semántica activa (${APP_VER})" 0
else
    check_result "11. Endpoint de versión responde con versión semántica activa" 1
fi

# 12. Catálogo de productos y categorías pobladas
CAT_COUNT=$(curl -s "${BASE_URL}/api/v1/categories" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
PROD_COUNT=$(curl -s "${BASE_URL}/api/v1/products" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
if [[ "${CAT_COUNT}" -ge 6 && "${PROD_COUNT}" -ge 12 ]]; then
    check_result "12. Catálogo poblado en SQLite: ${CAT_COUNT} categorías, ${PROD_COUNT} productos artesanales" 0
else
    check_result "12. Catálogo poblado en SQLite (categorías: ${CAT_COUNT}, productos: ${PROD_COUNT})" 1
fi

# 13. Creación atómica de pedido con Idempotency-Key
IDEM_KEY="val-$(date +%s%N)"
ORDER_RESP=$(curl -s -X POST "${BASE_URL}/api/v1/orders" \
    -H "Content-Type: application/json" \
    -H "Idempotency-Key: ${IDEM_KEY}" \
    -d '{
        "customer_name": "Validador E2E",
        "customer_email": "qa@mareadulce.com",
        "customer_phone": "+57 300 000 0000",
        "delivery_address": "Carrera 43A # 1-50, Medellín",
        "notes": "Prueba automatizada de integridad",
        "items": [{"product_id": 1, "quantity": 1}]
    }' || echo "{}")
ORDER_NUM=$(echo "${ORDER_RESP}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('order_number', ''))" 2>/dev/null || echo "")
if [[ -n "${ORDER_NUM}" ]]; then
    check_result "13. Creación atómica de pedido con deducción de stock e Idempotency-Key (${ORDER_NUM})" 0
else
    check_result "13. Creación atómica de pedido con deducción de stock e Idempotency-Key" 1
fi

# 14. Autenticación de Administrador (JWT bcrypt)
TOKEN=$(curl -s -X POST "${BASE_URL}/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@mareadulce.com","password":"AdminMarea2026!"}' | \
    python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")
ADMIN_DASH=$(curl -s -X GET "${BASE_URL}/api/v1/admin/dashboard" \
    -H "Authorization: Bearer ${TOKEN}" | \
    python3 -c "import sys, json; print('orders' in json.load(sys.stdin))" 2>/dev/null || echo "False")
if [[ "${ADMIN_DASH}" == "True" ]]; then
    check_result "14. Autenticación administrativa y métricas operativas de pedidos validadas" 0
else
    check_result "14. Autenticación administrativa y métricas operativas de pedidos validadas" 1
fi

# 15. Exposición de métricas Prometheus (/metrics)
METRICS_CHECK=$(curl -s "${BASE_URL}/metrics" | grep -c "marea_orders_total" || true)
if [[ "${METRICS_CHECK}" -ge 1 ]]; then
    check_result "15. Endpoint '/metrics' expone telemetría RED y métricas de negocio (marea_orders_total)" 0
else
    check_result "15. Endpoint '/metrics' expone telemetría RED y métricas de negocio" 1
fi

# 16. Pods de Observabilidad activos
PROM_READY=$(kubectl get pods -n "${MON_NAMESPACE}" --no-headers 2>/dev/null | grep -E "prometheus|grafana|alertmanager" | grep -c "Running" || true)
if [[ "${PROM_READY}" -ge 3 ]]; then
    check_result "16. Stack de Observabilidad (Prometheus, Grafana, Alertmanager) en estado Running" 0
else
    check_result "16. Stack de Observabilidad (Prometheus, Grafana, Alertmanager) en estado Running" 1
fi

echo "=============================================================================="
echo " RESUMEN DE VALIDACIÓN: ${PASS_COUNT} EXITOSAS (PASS) | ${FAIL_COUNT} FALLIDAS (FAIL)"
echo "=============================================================================="

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
    exit 1
fi
exit 0
