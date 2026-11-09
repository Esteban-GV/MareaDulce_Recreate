# Marea Dulce Cloud-Native Platform — Guía Consolidada de Scripts

Este directorio contiene la suite definitiva y depurada de automatización operativa (`bash` y `python3`) para administrar, validar y demostrar la plataforma **Marea Dulce** sobre Kubernetes (Minikube).

---

## 1. Inventario Consolidado de Scripts

| Script | Permisos | Función Principal | Uso Típico |
| :--- | :---: | :--- | :--- |
| [`start.sh`](start.sh) | `755 (+x)` | **Script maestro de inicio:** Valida prerrequisitos (`docker`, `minikube`, `kubectl`, `helm`, `python3`), auto-activa `newgrp docker`, comprueba si Minikube ya corre (no lo reinicia si está activo), compila imágenes OCI `v1.0.0` y `v2.0.0`, y despliega almacenamiento, observabilidad y workloads. | `bash scripts/start.sh` |
| [`stop.sh`](stop.sh) | `755 (+x)` | **Script de parada:** Cierra ordenadamente todos los túneles locales de red (`port-forward`) y apaga Minikube (`--cluster`, por defecto) o escala las réplicas a cero (`--scale-zero`). | `bash scripts/stop.sh [--cluster \| --scale-zero]` |
| [`status.sh`](status.sh) | `755 (+x)` | **Inspección de salud:** Muestra el estado integral de nodos, deployment, pods, PVC, Ingress, políticas de red y observabilidad. Soporta `--reset-v1` para respaldar SQLite con `.backup` y restaurar v1. | `bash scripts/status.sh [--reset-v1]` |
| [`forward_services.sh`](forward_services.sh) | `755 (+x)` | **Gestor de túneles locales:** Abre túneles persistentes en segundo plano para acceder a la tienda/API (`:8000`), Grafana (`:3000`), Prometheus (`:9090`), Alertmanager (`:9093`) y Kibana (`:5601`). | `bash scripts/forward_services.sh [start \| status \| stop]` |
| [`traffic_generator.py`](traffic_generator.py) | `755 (+x)` | **Medidor de Downtime:** Generador continuo de tráfico cliente (5 req/s) que cronometra con precisión de milisegundos la ventana exacta de corte durante la transición Recreate. | `python3 scripts/traffic_generator.py --url http://recreate.local --interval 0.2` |
| [`rollout_v2.sh`](rollout_v2.sh) | `755 (+x)` | **Demostración de Rollout:** Aplica `k8s/deployment-v2.yaml` bajo la estrategia Recreate, observando la terminación del pod v1 y el inicio de v2 con migración de base de datos. | `bash scripts/rollout_v2.sh` |
| [`reset_v1.sh`](reset_v1.sh) | `755 (+x)` | **Reinicio a v1:** Restablece la versión 1.0.0 de forma limpia y reproducible para repetir demostraciones. | `bash scripts/reset_v1.sh` |
| [`validate.sh`](validate.sh) | `755 (+x)` | **Suite Automatizada E2E:** Ejecuta 16 pruebas continuas que validan conectividad, Recreate, PVC RWO, sondas, catálogo, pedidos atómicos con idempotencia, JWT y observabilidad. | `bash scripts/validate.sh` |
| [`benchmark.sh`](benchmark.sh) | `755 (+x)` | **Benchmark HTTP:** Ejecuta ráfagas sintéticas de peticiones secuenciales contra sondas, catálogo de productos, categorías y métricas. | `bash scripts/benchmark.sh [ITERACIONES]` |
| [`test_alerts.py`](test_alerts.py) | `755 (+x)` | **Disparador de Alarmas:** Genera errores HTTP 500 y latencia inducida para provocar la activación y transición a FIRING en Alertmanager. | `python3 scripts/test_alerts.py --url http://recreate.local` |

---

## 2. Flujo de Trabajo Recomendado

```bash
# Paso 1: Iniciar la plataforma completa
bash scripts/start.sh

# Paso 2: Abrir túneles hacia la tienda web y dashboards
bash scripts/forward_services.sh start

# Paso 3: Inspeccionar estado general
bash scripts/status.sh

# Paso 4: Validar salud con la suite E2E
bash scripts/validate.sh

# Paso 5: Demostración de Recreate con medición de Downtime
# (En terminal 1):
python3 scripts/traffic_generator.py --url http://recreate.local --interval 0.2
# (En terminal 2):
bash scripts/rollout_v2.sh

# Paso 6: Restablecer a v1 cuando termine la prueba
bash scripts/reset_v1.sh

# Paso 7: Apagar todo al finalizar la sesión
bash scripts/stop.sh
```
