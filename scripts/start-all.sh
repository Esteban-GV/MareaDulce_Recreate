#!/usr/bin/env bash
# ==============================================================================
# CoreLedger Cloud-Native Platform — start-all.sh
# Propósito: Iniciar Minikube de forma idempotente, construir imágenes OCI,
#            desplegar kube-prometheus-stack y ELK, y reconciliar todos los
#            manifiestos de Kubernetes del proyecto k8s-recreate-deployment.
# Uso:       bash scripts/start-all.sh
# ==============================================================================
set -euo pipefail

# Auto-activación de pertenencia al grupo docker si la sesión actual no lo tiene activo
if ! docker ps >/dev/null 2>&1; then
  if grep -q "^docker:.*\<${USER:-$(id -un)}\>" /etc/group 2>/dev/null; then
    echo "[AUTO-FIX] Sesión sin grupo 'docker' activo en terminal actual. Re-ejecutando con newgrp docker..."
    exec newgrp docker -c "bash \"$0\" $*"
  fi
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=================================================================="
echo " [CoreLedger] Iniciando Plataforma Cloud-Native (Recreate Stack)"
echo "=================================================================="

if ! minikube status 2>/dev/null | grep -q "host: Running" || ! kubectl cluster-info >/dev/null 2>&1; then
  echo "[1/6] Iniciando clúster Minikube y construyendo imágenes..."
  bash "${SCRIPT_DIR}/start_minikube.sh"
else
  echo "[1/6] Clúster Minikube ya está en ejecución. Sincronizando imágenes..."
  minikube image build -t recreate-app:v1.0.0 "${REPO_ROOT}/app"
  minikube image build -t recreate-app:v2.0.0 "${REPO_ROOT}/app"
fi

echo "[2/6] Aplicando Namespace y Almacenamiento Persistente (PVC 1Gi RWO)..."
kubectl apply -f "${REPO_ROOT}/k8s/namespace.yaml"
kubectl apply -f "${REPO_ROOT}/k8s/pvc.yaml"

echo "[3/6] Desplegando Pila de Observabilidad (Prometheus, Grafana, Alertmanager)..."
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
if ! helm status prometheus-stack -n monitoring >/dev/null 2>&1; then
  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null 2>&1 || true
  helm repo update >/dev/null 2>&1 || true
  helm upgrade --install prometheus-stack prometheus-community/kube-prometheus-stack \
    -n monitoring \
    -f "${REPO_ROOT}/monitoring/prometheus/values-kube-prometheus-stack.yaml" \
    --wait --timeout 5m
fi

kubectl create configmap recreate-app-grafana-dashboard \
  -n monitoring \
  --from-file=grafana-dashboard-recreate.json="${REPO_ROOT}/monitoring/prometheus/grafana-dashboard-recreate.json" \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl label configmap recreate-app-grafana-dashboard -n monitoring grafana_dashboard="1" --overwrite

echo "[4/6] Aplicando Pila ELK (Elasticsearch, Filebeat, Kibana)..."
kubectl apply -f "${REPO_ROOT}/monitoring/elk/values-elk.yaml"

echo "[5/6] Aplicando Deployment (Recreate), Service, Ingress, NetworkPolicy y HPA..."
if ! kubectl get deployment recreate-app-deployment -n recreate-lab >/dev/null 2>&1; then
  kubectl apply -f "${REPO_ROOT}/k8s/deployment-v1.yaml"
fi
kubectl apply -f "${REPO_ROOT}/k8s/service.yaml"
kubectl apply -f "${REPO_ROOT}/k8s/ingress.yaml"
kubectl apply -f "${REPO_ROOT}/k8s/networkpolicy.yaml"
kubectl apply -f "${REPO_ROOT}/k8s/hpa.yaml"

echo "[6/6] Aplicando ServiceMonitor y Reglas de Alerta (PrometheusRule)..."
kubectl apply -f "${REPO_ROOT}/k8s/servicemonitor.yaml"
kubectl apply -f "${REPO_ROOT}/k8s/prometheusrule.yaml"

echo "Esperando disponibilidad de réplicas en recreate-lab..."
kubectl rollout status deployment/recreate-app-deployment -n recreate-lab --timeout=120s

echo "=================================================================="
echo " [CoreLedger] Todos los manifiestos fueron reconciliados con éxito."
echo "=================================================================="
