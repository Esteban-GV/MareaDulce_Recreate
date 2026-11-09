#!/usr/bin/env bash
# ==============================================================================
# Script de Inicialización del Clúster Minikube con Especificaciones Justificadas
# Proyecto: k8s-recreate-deployment (Plataformas II)
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

CPUS=6
MEMORY=10240
DRIVER="docker"

echo "=== Iniciando Minikube ==="
echo "Configuración: Driver=$DRIVER | CPUs=$CPUS | Memoria=${MEMORY}MB"
echo "Justificación: Recursos dimensionados sobre host de 8 hilos y 16 GB RAM para alojar CoreLedger, kube-prometheus-stack, pila ELK (Elasticsearch + Filebeat + Kibana) e Ingress NGINX."

# Limpieza preventiva de volumen Docker huérfano para evitar colisiones en etcd
if ! minikube status 2>/dev/null | grep -q "host: Running"; then
  echo "Limpiando posibles contenedores y volúmenes Docker huérfanos de minikube..."
  docker rm -f minikube >/dev/null 2>&1 || true
  docker volume rm minikube >/dev/null 2>&1 || true
fi

minikube start \
    --driver="$DRIVER" \
    --cpus="$CPUS" \
    --memory="$MEMORY"

echo "=== Habilitando complementos indispensables ==="
echo "1. Ingress Controller (enrutamiento HTTP externo)"
minikube addons enable ingress

echo "2. Metrics Server (requerido para HPA y telemetría de pods)"
minikube addons enable metrics-server

echo "3. Default Storage Class (requerido para aprovisionamiento dinámico de PVC)"
minikube addons enable default-storageclass
minikube addons enable storage-provisioner

echo "=== Construyendo imágenes de contenedor en Minikube ==="
minikube image build -t recreate-app:v1.0.0 "${REPO_ROOT}/app"
minikube image build -t recreate-app:v2.0.0 "${REPO_ROOT}/app"

echo "=== Estado del Clúster ==="
kubectl cluster-info
kubectl get nodes -o wide

