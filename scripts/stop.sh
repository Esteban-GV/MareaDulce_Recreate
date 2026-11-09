#!/usr/bin/env bash
# ==============================================================================
# Marea Dulce Cloud-Native Platform — stop.sh (Script de Parada Limpia)
# ==============================================================================
# Propósito:
#   Detiene los túneles locales de port-forward y apaga ordenadamente las cargas
#   de trabajo o el clúster Minikube completo.
# Uso:
#   ./scripts/stop.sh             -> Detiene port-forward y apaga Minikube (por defecto)
#   ./scripts/stop.sh --cluster   -> Detiene port-forward y apaga Minikube
#   ./scripts/stop.sh --scale-zero-> Escala las réplicas a 0 conservando el clúster
# ==============================================================================
set -euo pipefail

# Auto-activación de pertenencia al grupo docker si la sesión actual no lo tiene activo
if ! docker ps >/dev/null 2>&1; then
  if grep -q "^docker:.*\<${USER:-$(id -un)}\>" /etc/group 2>/dev/null; then
    echo "[AUTO-FIX] Sesión sin grupo 'docker' activo en terminal actual. Re-ejecutando con newgrp docker..."
    exec newgrp docker -c "bash \"$0\" $*"
  fi
fi

MODE="${1:---cluster}"

echo "=============================================================================="
echo " [Marea Dulce] Deteniendo Plataforma (Modo: ${MODE})"
echo "=============================================================================="

echo "[1/2] Deteniendo túneles locales de red (port-forward)..."
pkill -f "kubectl port-forward" 2>/dev/null || true
echo "  -> Túneles port-forward cerrados."

if [ "${MODE}" = "--cluster" ]; then
  echo "[2/2] Deteniendo el clúster Minikube..."
  minikube stop
  echo "  -> Clúster Minikube detenido exitosamente. Estado de PVC y datos preservados en disco."
elif [ "${MODE}" = "--scale-zero" ]; then
  echo "[2/2] Escalando deployment marea-app-deployment a 0 réplicas..."
  kubectl scale deployment/marea-app-deployment --replicas=0 -n recreate-lab || true
  echo "  -> Réplicas escaladas a 0. Clúster sigue activo y datos en PVC (/data) intactos."
else
  echo "[AVISO] Modo desconocido. Uso: ./scripts/stop.sh [--cluster | --scale-zero]"
fi

echo "=============================================================================="
echo " Parada completada."
echo "=============================================================================="
