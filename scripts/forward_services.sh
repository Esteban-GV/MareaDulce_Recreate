#!/usr/bin/env bash
# ==============================================================================
# Gestor de Túneles Port-Forward hacia Servicios y Dashboards (forward_services.sh)
# Uso:
#   ./scripts/forward_services.sh start   -> Abre túneles en segundo plano
#   ./scripts/forward_services.sh status  -> Lista túneles activos y URLs
#   ./scripts/forward_services.sh stop    -> Cierra todos los túneles activos
# ==============================================================================
set -euo pipefail

ACTION="${1:-status}"

start_forwards() {
    echo "Iniciando túneles locales (port-forward) en segundo plano..."

    # Detener instancias previas para evitar colisión de puertos
    pkill -f "kubectl port-forward.*recreate-app-service" 2>/dev/null || true
    pkill -f "kubectl port-forward.*prometheus-stack-grafana" 2>/dev/null || true
    pkill -f "kubectl port-forward.*prometheus-stack-kube-prom-prometheus" 2>/dev/null || true
    pkill -f "kubectl port-forward.*prometheus-stack-kube-prom-alertmanager" 2>/dev/null || true
    pkill -f "kubectl port-forward.*svc/kibana" 2>/dev/null || true
    sleep 1

    setsid bash -c "while true; do kubectl port-forward --address 0.0.0.0 svc/recreate-app-service -n recreate-lab 8080:80 </dev/null >>/tmp/pf-app.log 2>&1 || true; sleep 1; done" </dev/null >/dev/null 2>&1 &
    setsid bash -c "while true; do kubectl port-forward --address 0.0.0.0 svc/prometheus-stack-grafana -n monitoring 3000:80 </dev/null >>/tmp/pf-grafana.log 2>&1 || true; sleep 1; done" </dev/null >/dev/null 2>&1 &
    setsid bash -c "while true; do kubectl port-forward --address 0.0.0.0 svc/prometheus-stack-kube-prom-prometheus -n monitoring 9090:9090 </dev/null >>/tmp/pf-prometheus.log 2>&1 || true; sleep 1; done" </dev/null >/dev/null 2>&1 &
    setsid bash -c "while true; do kubectl port-forward --address 0.0.0.0 svc/prometheus-stack-kube-prom-alertmanager -n monitoring 9093:9093 </dev/null >>/tmp/pf-alertmanager.log 2>&1 || true; sleep 1; done" </dev/null >/dev/null 2>&1 &
    if kubectl get svc kibana -n monitoring >/dev/null 2>&1; then
        setsid bash -c "while true; do kubectl port-forward --address 0.0.0.0 svc/kibana -n monitoring 5601:5601 </dev/null >>/tmp/pf-kibana.log 2>&1 || true; sleep 1; done" </dev/null >/dev/null 2>&1 &
    fi
    sleep 2

    show_status
}

stop_forwards() {
    echo "Deteniendo túneles kubectl port-forward activos..."
    pkill -f "port-forward.*recreate-app-service" 2>/dev/null || true
    pkill -f "port-forward.*prometheus-stack-grafana" 2>/dev/null || true
    pkill -f "port-forward.*prometheus-stack-kube-prom-prometheus" 2>/dev/null || true
    pkill -f "port-forward.*prometheus-stack-kube-prom-alertmanager" 2>/dev/null || true
    pkill -f "port-forward.*svc/kibana" 2>/dev/null || true
    pkill -f "kubectl port-forward" 2>/dev/null || true
    echo "Túneles detenidos."
}

show_status() {
    echo "=============================================================================="
    echo " ACCESO LOCAL A SERVICIOS Y DASHBOARDS DE LA PLATAFORMA"
    echo "=============================================================================="
    echo " 1. Aplicación Web CoreLedger (UI):     http://localhost:8080"
    echo "    - Info JSON y Contador PVC:         http://localhost:8080/api/info"
    echo "    - Transacciones SQLite en PVC:      http://localhost:8080/api/transactions"
    echo "    - Estado de Esquema BD:             http://localhost:8080/api/schema-status"
    echo "    - Métricas Prometheus:              http://localhost:8080/metrics"
    echo "    - Documentación OpenAPI (Swagger):  http://localhost:8080/docs"
    echo ""
    echo " 2. Grafana (Dashboards Visuales):      http://localhost:3000"
    echo "    - Dashboard Recreate & FinOps:      http://localhost:3000/d/coreledger-recreate-red-use"
    echo "    - Usuario / Contraseña (Lab):       admin / admin123"
    echo ""
    echo " 3. Prometheus (Consultas y Alertas):   http://localhost:9090"
    echo "    - Targets de Scrape:                http://localhost:9090/targets"
    echo "    - Reglas de Alerta:                 http://localhost:9090/alerts"
    echo ""
    echo " 4. Alertmanager (Gestión de Alarmas):  http://localhost:9093"
    echo ""
    echo " 5. Kibana - Pila ELK (Logs K8s):       http://localhost:5601/app/discover"
    echo "=============================================================================="
    echo " Procesos port-forward en ejecución:"
    pgrep -af "kubectl port-forward" || echo "  (Ningún túnel activo. Ejecute: ./scripts/forward_services.sh start)"
    echo "=============================================================================="
}

case "${ACTION}" in
    start)
        start_forwards
        ;;
    stop)
        stop_forwards
        ;;
    status|*)
        show_status
        ;;
esac
