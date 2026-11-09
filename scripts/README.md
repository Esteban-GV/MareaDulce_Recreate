# CoreLedger Cloud-Native Platform — Guía de Scripts Operativos

Este directorio contiene la suite completa de automatización operativa (`bash` y `python3`) para administrar, inspeccionar, validar y ejecutar demostraciones de la plataforma **CoreLedger (`k8s-recreate-deployment`)** sobre Kubernetes (Minikube).

## Inventario de Scripts

| Script | Permisos | Descripción | Uso |
| :--- | :---: | :--- | :--- |
| [`start-all.sh`](start-all.sh) | `755 (+x)` | Inicia Minikube (si está apagado), construye las imágenes `v1.0.0` y `v2.0.0`, despliega `kube-prometheus-stack`, la pila `ELK` y reconcilia todos los manifiestos de `k8s/`. | `bash scripts/start-all.sh` |
| [`stop-all.sh`](stop-all.sh) | `755 (+x)` | Escala ordenadamente las réplicas del microservicio a cero (`--scale-zero`, por defecto) o detiene el clúster Minikube (`--cluster`). | `bash scripts/stop-all.sh [--scale-zero \| --cluster]` |
| [`restart-all.sh`](restart-all.sh) | `755 (+x)` | Reconcilia manifiestos vía `start-all.sh` y ejecuta un reinicio controlado bajo la estrategia `Recreate`. | `bash scripts/restart-all.sh` |
| [`status.sh`](status.sh) | `755 (+x)` | Imprime el estado completo de Namespaces, Pods, Services, Ingress, PVC, HPA, NetworkPolicies y la base SQLite. Soporta `--reset-v1` para restaurar el estado previo a la demostración. | `bash scripts/status.sh [--reset-v1]` |
| [`validate.sh`](validate.sh) | `755 (+x)` | Ejecuta 16 pruebas automatizadas E2E (salud, PVC, SQLite, migración, SSO/MFA, NetworkPolicy, HPA, Prometheus, Grafana y ELK). Retorna `0` si el 100% aprueba. | `bash scripts/validate.sh` |
| [`benchmark.sh`](benchmark.sh) | `755 (+x)` | Ejecuta pruebas sintéticas secuenciales de latencia y fiabilidad HTTP contra `/healthz`, `/api/info` y `/api/transactions`. | `bash scripts/benchmark.sh [ITERACIONES]` |
| [`forward_services.sh`](forward_services.sh) | `755 (+x)` | Abre túneles `kubectl port-forward` en segundo plano para la aplicación Web (`8080`), Grafana (`3000`), Prometheus (`9090`), Alertmanager (`9093`) y Kibana (`5601`). | `bash scripts/forward_services.sh [start \| status \| stop]` |
| [`start_minikube.sh`](start_minikube.sh) | `755 (+x)` | Inicializa el clúster Minikube con recursos justificados (`6 CPUs`, `10240 MB RAM`, driver `docker`), habilita addons y construye las imágenes OCI. | `bash scripts/start_minikube.sh` |
| [`install_prerequisites.sh`](install_prerequisites.sh) | `755 (+x)` | Verifica e instala las herramientas necesarias en el host (`docker`, `kubectl`, `minikube`, `helm`, `python3`) y ajusta `vm.max_map_count`. | `bash scripts/install_prerequisites.sh` |
| [`traffic_generator.py`](traffic_generator.py) | `755 (+x)` | Sondea continuamente la aplicación y cronometra con precisión de milisegundos la ventana de interrupción (*downtime*) durante la transición `Recreate`. | `python3 scripts/traffic_generator.py --url http://localhost:8080/api/info --interval 0.2` |
| [`test_alerts.py`](test_alerts.py) | `755 (+x)` | Genera ráfagas controladas de errores HTTP 500, latencia artificial y estrés de CPU para verificar el disparo de las 5 reglas en Prometheus y Alertmanager. | `python3 scripts/test_alerts.py --url http://localhost:8080` |
