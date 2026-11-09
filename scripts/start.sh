#!/usr/bin/env bash
# ==============================================================================
# Marea Dulce Cloud-Native Platform — start.sh (Script Maestro de Inicio)
# ==============================================================================
# Propósito:
#   1. Auto-activar pertenencia al grupo docker (newgrp docker).
#   2. Verificar e informar prerrequisitos necesarios (docker, minikube, kubectl, helm, python3).
#   3. Comprobar si Minikube ya está en ejecución (idempotente: no lo reinicia si ya está activo).
#   4. Si no está iniciado, arrancar Minikube con recursos justificados y habilitar addons
#      (ingress, metrics-server, storage-provisioner, default-storageclass).
#   5. Construir las imágenes OCI unificadas en Minikube (marea-app:v1.0.0 y marea-app:v2.0.0).
#   6. Desplegar PVC, Observabilidad (Prometheus, Grafana, Alertmanager, ELK) y Workloads.
#   7. Dejar la plataforma lista para operar e indicar cómo ejecutar forward_services.sh.
# Uso:
#   bash scripts/start.sh
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=============================================================================="
echo " [Marea Dulce] Inicializando Plataforma Cloud-Native (K8s Recreate Stack)"
echo "=============================================================================="

# ------------------------------------------------------------------------------
# 1. Verificación y auto-activación del grupo Docker en la sesión actual
# ------------------------------------------------------------------------------
if ! docker ps >/dev/null 2>&1; then
  CURRENT_USER="${USER:-$(id -un)}"
  if grep -q "^docker:.*\<${CURRENT_USER}\>" /etc/group 2>/dev/null; then
    echo "[AUTO-FIX] Sesión sin grupo 'docker' activo en terminal actual. Re-ejecutando con newgrp docker..."
    exec newgrp docker -c "bash \"$0\" $*"
  else
    echo "[ERROR] El usuario '${CURRENT_USER}' no pertenece al grupo 'docker' o el demonio Docker no está activo."
    echo "Ejecute: sudo usermod -aG docker ${CURRENT_USER} && sudo systemctl start docker"
    exit 1
  fi
fi

# ------------------------------------------------------------------------------
# 2. Verificación de herramientas y prerrequisitos del sistema
# ------------------------------------------------------------------------------
echo "[1/6] Verificando herramientas y dependencias del host..."
REQUIRED_TOOLS=("docker" "minikube" "kubectl" "helm" "python3")
MISSING_TOOLS=()

for tool in "${REQUIRED_TOOLS[@]}"; do
  if ! command -v "${tool}" &>/dev/null; then
    MISSING_TOOLS+=("${tool}")
  fi
done

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
  echo "[ERROR] Faltan las siguientes herramientas instaladas en el sistema: ${MISSING_TOOLS[*]}"
  echo "Por favor instálelas antes de continuar."
  exit 1
fi
echo "  -> Herramientas verificadas: ${REQUIRED_TOOLS[*]}"

# Verificación de memoria virtual para Elasticsearch (ELK)
CURRENT_MAP_COUNT=$(cat /proc/sys/vm/max_map_count 2>/dev/null || echo "0")
if [ "${CURRENT_MAP_COUNT}" -lt 262144 ]; then
  echo "  -> Ajustando vm.max_map_count a 262144 para Elasticsearch..."
  sudo sysctl -w vm.max_map_count=262144 >/dev/null 2>&1 || true
fi

# ------------------------------------------------------------------------------
# 3. Comprobación y arranque idempotente de Minikube
# ------------------------------------------------------------------------------
echo "[2/6] Comprobando estado del clúster Minikube..."
MINIKUBE_RUNNING=false
if minikube status 2>/dev/null | grep -q "host: Running" && kubectl cluster-info >/dev/null 2>&1; then
  MINIKUBE_RUNNING=true
  echo "  -> Minikube ya se encuentra iniciado y activo. Se omite arranque redundante."
else
  echo "  -> Iniciando clúster Minikube con recursos justificados..."
  CPUS=6
  MEMORY=10240
  DRIVER="docker"

  # Limpieza preventiva de contenedores y volúmenes huérfanos
  docker rm -f minikube >/dev/null 2>&1 || true
  docker volume rm minikube >/dev/null 2>&1 || true

  minikube start \
    --driver="${DRIVER}" \
    --cpus="${CPUS}" \
    --memory="${MEMORY}"

  echo "  -> Habilitando complementos indispensables..."
  minikube addons enable ingress
  minikube addons enable metrics-server
  minikube addons enable default-storageclass
  minikube addons enable storage-provisioner
fi

# ------------------------------------------------------------------------------
# 4. Construcción de imágenes OCI unificadas dentro del entorno Minikube
# ------------------------------------------------------------------------------
echo "[3/6] Construyendo imágenes OCI unificadas (marea-app v1.0.0 y v2.0.0)..."
minikube image build -t marea-app:v1.0.0 "${REPO_ROOT}/app"
minikube image build -t marea-app:v2.0.0 "${REPO_ROOT}/app"
echo "  -> Imágenes OCI compiladas y registradas en el clúster."

# ------------------------------------------------------------------------------
# 5. Despliegue de Namespaces, Almacenamiento y Observabilidad
# ------------------------------------------------------------------------------
echo "[4/6] Aplicando Namespace y Almacenamiento Persistente (PVC 1Gi RWO)..."
kubectl apply -f "${REPO_ROOT}/k8s/namespace.yaml"
kubectl apply -f "${REPO_ROOT}/k8s/pvc.yaml"

echo "[5/6] Desplegando Pila de Observabilidad (Prometheus, Grafana, Alertmanager, ELK)..."
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

if ! helm status prometheus-stack -n monitoring >/dev/null 2>&1; then
  echo "  -> Instalando kube-prometheus-stack vía Helm..."
  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null 2>&1 || true
  helm repo update >/dev/null 2>&1 || true
  helm upgrade --install prometheus-stack prometheus-community/kube-prometheus-stack \
    -n monitoring \
    -f "${REPO_ROOT}/monitoring/prometheus/values-kube-prometheus-stack.yaml" \
    --wait --timeout 5m
fi

# Aprovisionar Tablero de Grafana Marea Dulce
kubectl create configmap marea-app-grafana-dashboard \
  -n monitoring \
  --from-file=grafana-dashboard-recreate.json="${REPO_ROOT}/monitoring/prometheus/grafana-dashboard-recreate.json" \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl label configmap marea-app-grafana-dashboard -n monitoring grafana_dashboard="1" --overwrite

# Aplicar Pila ELK
kubectl apply -f "${REPO_ROOT}/monitoring/elk/values-elk.yaml"

# ------------------------------------------------------------------------------
# 6. Despliegue de la Carga de Trabajo Recreate v1.0.0 y Políticas
# ------------------------------------------------------------------------------
echo "[6/6] Desplegando Marea Dulce v1.0.0 (Estrategia Recreate), Ingress y Políticas..."
kubectl apply -f "${REPO_ROOT}/k8s/deployment-v1.yaml"
kubectl apply -f "${REPO_ROOT}/k8s/service.yaml"
kubectl apply -f "${REPO_ROOT}/k8s/ingress.yaml"
kubectl apply -f "${REPO_ROOT}/k8s/networkpolicy.yaml"
kubectl apply -f "${REPO_ROOT}/k8s/servicemonitor.yaml"
kubectl apply -f "${REPO_ROOT}/k8s/prometheusrule.yaml"

echo "  -> Esperando disponibilidad del pod marea-app-deployment..."
kubectl rollout status deployment/marea-app-deployment -n recreate-lab --timeout=120s

echo ""
echo "=============================================================================="
echo " [Marea Dulce] Plataforma iniciada y 100% operativa."
echo "=============================================================================="
echo " Siguiente paso recomendado:"
echo "   Para acceder a la tienda web y dashboards, abra los túneles locales con:"
echo "   -> ./scripts/forward_services.sh start"
echo ""
echo " Para verificar el estado general en cualquier momento:"
echo "   -> ./scripts/status.sh"
echo "=============================================================================="
