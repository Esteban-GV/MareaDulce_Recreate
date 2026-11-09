#!/usr/bin/env bash
# ==============================================================================
# Suite Automatizada de Validación End-to-End (validate.sh)
# Verifica infraestructura, estrategia Recreate, persistencia SQLite en PVC,
# seguridad NetworkPolicy/SSO, HPA y observabilidad (Prometheus/Grafana/Alertas)
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
echo " SUITE DE VALIDACIÓN AUTOMATIZADA - PLATAFORMA K8S RECREATE DEPLOYMENT"
echo "=============================================================================="

# 1. Conectividad con el clúster
kubectl cluster-info >/dev/null 2>&1
check_result "01. Clúster de Kubernetes accesible vía kubectl" $?

# 2. Existencia del namespace recreate-lab
kubectl get namespace "${APP_NAMESPACE}" >/dev/null 2>&1
check_result "02. Namespace '${APP_NAMESPACE}' existente y activo" $?

# 3. Verificación explícita de estrategia Recreate
STRATEGY=$(kubectl get deployment recreate-app-deployment -n "${APP_NAMESPACE}" -o jsonpath='{.spec.strategy.type}' 2>/dev/null || echo "")
if [[ "${STRATEGY}" == "Recreate" ]]; then
    check_result "03. Deployment 'recreate-app-deployment' configurado con estrategia exclusiva 'Recreate'" 0
else
    check_result "03. Deployment 'recreate-app-deployment' configurado con estrategia exclusiva 'Recreate' (actual: ${STRATEGY})" 1
fi

# 4. Pods de la aplicación en estado Ready
READY_REPLICAS=$(kubectl get deployment recreate-app-deployment -n "${APP_NAMESPACE}" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
if [[ "${READY_REPLICAS:-0}" -ge 1 ]]; then
    check_result "04. Réplicas de 'recreate-app-deployment' en estado Running/Ready (${READY_REPLICAS} activas)" 0
else
    check_result "04. Réplicas de 'recreate-app-deployment' en estado Running/Ready" 1
fi

# 5. Volumen Persistente (PVC) en estado Bound
PVC_STATUS=$(kubectl get pvc recreate-app-pvc -n "${APP_NAMESPACE}" -o jsonpath='{.status.phase}' 2>/dev/null || echo "")
if [[ "${PVC_STATUS}" == "Bound" ]]; then
    check_result "05. PersistentVolumeClaim 'recreate-app-pvc' enlazado (Bound)" 0
else
    check_result "05. PersistentVolumeClaim 'recreate-app-pvc' enlazado (actual: ${PVC_STATUS})" 1
fi

# 6. NetworkPolicy aplicada
kubectl get networkpolicy recreate-app-network-policy -n "${APP_NAMESPACE}" >/dev/null 2>&1
check_result "06. Política de aislamiento 'recreate-app-network-policy' activa" $?

# 7. HorizontalPodAutoscaler configurado
kubectl get hpa recreate-app-hpa -n "${APP_NAMESPACE}" >/dev/null 2>&1
check_result "07. Autoescalador Horizontal 'recreate-app-hpa' operativo" $?

# 8. Service e Ingress configurados
kubectl get svc recreate-app-service -n "${APP_NAMESPACE}" >/dev/null 2>&1 && \
kubectl get ingress recreate-app-ingress -n "${APP_NAMESPACE}" >/dev/null 2>&1
check_result "08. Service 'recreate-app-service' e Ingress 'recreate-app-ingress' configurados" $?

# 9. ServiceMonitor y PrometheusRule aplicados
kubectl get servicemonitor recreate-app-servicemonitor -n "${APP_NAMESPACE}" >/dev/null 2>&1 && \
kubectl get prometheusrule recreate-app-alert-rules -n "${APP_NAMESPACE}" >/dev/null 2>&1
check_result "09. CRDs de Observabilidad (ServiceMonitor y PrometheusRule) registrados" $?

# Iniciar túnel temporal hacia el servicio para pruebas funcionales de API
kubectl port-forward svc/recreate-app-service -n "${APP_NAMESPACE}" "${LOCAL_PORT}:80" >/dev/null 2>&1 &
PF_PID=$!
sleep 2

BASE_URL="http://127.0.0.1:${LOCAL_PORT}"

# 10. Sondas de salud /healthz y /ready
HTTP_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/healthz" || echo "000")
HTTP_READY=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/ready" || echo "000")
if [[ "${HTTP_HEALTH}" == "200" && "${HTTP_READY}" == "200" ]]; then
    check_result "10. Sondas Liveness (/healthz) y Readiness (/ready) responden HTTP 200" 0
else
    check_result "10. Sondas Liveness (/healthz) y Readiness (/ready) responden HTTP 200" 1
fi

# 11. Verificación de incremento en contador persistente PVC
C1=$(curl -s "${BASE_URL}/api/info" | python3 -c "import sys, json; print(json.load(sys.stdin).get('persistent_counter', -1))" 2>/dev/null || echo "-1")
C2=$(curl -s "${BASE_URL}/api/info" | python3 -c "import sys, json; print(json.load(sys.stdin).get('persistent_counter', -1))" 2>/dev/null || echo "-1")
if [[ "${C1}" -ge 1 && "${C2}" -gt "${C1}" ]]; then
    check_result "11. Contador atómico en PVC incrementando correctamente (${C1} -> ${C2})" 0
else
    check_result "11. Contador atómico en PVC incrementando correctamente" 1
fi

# 12. Persistencia transaccional SQLite en PVC (/api/transactions)
TX_HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/api/transactions" \
    -H "Content-Type: application/json" \
    -d '{"concept":"Validacion automatizada E2E","amount_usd":150.75,"currency":"USD"}' || echo "000")
TX_TOTAL=$(curl -s "${BASE_URL}/api/transactions" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total_transactions', 0))" 2>/dev/null || echo "0")
if [[ "${TX_HTTP}" == "201" && "${TX_TOTAL}" -ge 1 ]]; then
    check_result "12. Base de datos SQLite en PVC almacena transacciones (${TX_TOTAL} registros)" 0
else
    check_result "12. Base de datos SQLite en PVC almacena transacciones" 1
fi

# 13. Verificación de estado de esquema de base de datos (/api/schema-status)
SCHEMA_VER=$(curl -s "${BASE_URL}/api/schema-status" | python3 -c "import sys, json; print(json.load(sys.stdin).get('active_schema', ''))" 2>/dev/null || echo "")
if [[ -n "${SCHEMA_VER}" ]]; then
    check_result "13. Estado de migración de esquema activo en PVC verificado (${SCHEMA_VER})" 0
else
    check_result "13. Estado de migración de esquema activo en PVC verificado" 1
fi

# 14. Autenticación SSO / OIDC + MFA (/api/auth/token y /api/auth/verify)
TOKEN=$(curl -s -X POST "${BASE_URL}/api/auth/token" \
    -H "Content-Type: application/json" \
    -d '{"username":"esteban.guarin@universidad.edu.co","mfa_code":"482910"}' | \
    python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")
AUTH_OK=$(curl -s -X POST "${BASE_URL}/api/auth/verify" \
    -H "Authorization: Bearer ${TOKEN}" | \
    python3 -c "import sys, json; print(json.load(sys.stdin).get('authenticated', False))" 2>/dev/null || echo "False")
if [[ "${AUTH_OK}" == "True" ]]; then
    check_result "14. Flujo de autenticación SSO / OIDC con MFA validado satisfactoriamente" 0
else
    check_result "14. Flujo de autenticación SSO / OIDC con MFA validado satisfactoriamente" 1
fi

# 15. Exposición de métricas Prometheus (/metrics)
METRICS_CHECK=$(curl -s "${BASE_URL}/metrics" | grep -c "app_ledger_transactions_total" || true)
if [[ "${METRICS_CHECK}" -ge 1 ]]; then
    check_result "15. Endpoint '/metrics' expone telemetría RED y métricas de dominio en PVC" 0
else
    check_result "15. Endpoint '/metrics' expone telemetría RED y métricas de dominio en PVC" 1
fi

# 16. Pods de Prometheus, Grafana y Alertmanager activos
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
