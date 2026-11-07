#!/usr/bin/env bash
# ==============================================================================
# Script de Inicialización del Clúster Minikube con Especificaciones Justificadas
# Proyecto: k8s-recreate-deployment (Plataformas II)
# ==============================================================================

set -euo pipefail

CPUS=4
MEMORY=8192
DRIVER="docker"

echo "=== Iniciando Minikube ==="
echo "Configuración: Driver=$DRIVER | CPUs=$CPUS | Memoria=${MEMORY}MB"
echo "Justificación: Recursos dimensionados para alojar la aplicación, kube-prometheus-stack, ELK y Kubecost."

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

echo "=== Estado del Clúster ==="
kubectl cluster-info
kubectl get nodes -o wide

