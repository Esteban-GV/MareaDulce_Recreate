# Kubernetes (Minikube / K8s) — Documentación Técnica

**Kubernetes (K8s)** es la plataforma estándar de código abierto graduada por la Cloud Native Computing Foundation (CNCF) para la orquestación declarativa de cargas de trabajo en contenedores. En esta plataforma se ejecuta sobre **Minikube (`Kubernetes v1.35` / driver `docker`)** proporcionando reconciliación continua de estado deseado, descubrimiento de servicios DNS (`CoreDNS`), enrutamiento L7 (`ingress-nginx`), almacenamiento persistente (`PVC ReadWriteOnce`) y aislamiento de red (`NetworkPolicy`).

## Para qué sirve

Sirve para automatizar el ciclo de vida de los contenedores, garantizando autorrecuperación (*self-healing*) mediante sondas de salud, balanceo de carga interno, orquestación de la estrategia de despliegue Recreate y gestión centralizada de configuración.

**En qué se utilizó en el proyecto:**
- **Orquestación de la Plataforma Marea Dulce:** Se utilizó para gestionar el ciclo de vida de `marea-app-deployment` dentro del namespace aislado `recreate-lab`, ejecutando de forma estricta la estrategia de despliegue `Recreate` (`spec.strategy.type: Recreate`) con 1 réplica exclusiva sobre el volumen de datos.
- **Enrutamiento y Exposición Externa:** Se utilizó el controlador Ingress NGINX para enrutar el tráfico HTTP entrante del host hacia el Service `marea-app-service` a través del dominio `recreate.local`.
- **Aislamiento Multi-Namespace:** Se utilizó para separar las cargas de trabajo de la aplicación (`recreate-lab`) de la infraestructura de telemetría y registros (`monitoring`).
- **Gobernanza de Persistencia con Sondas de Salud:** Las sondas `livenessProbe` (`/healthz`) y `readinessProbe` (`/ready`) aseguran que el pod no reciba tráfico hasta que la base de datos SQLite y las migraciones atómicas concluyan satisfactoriamente.

## Arquitectura

```mermaid
flowchart TB
    Ingress["NGINX Ingress Controller\n(recreate.local:80)"] --> AppSvc["Service: marea-app-service\n(80/TCP -> 8000/TCP)"]

    subgraph AppNS ["Namespace: recreate-lab"]
        AppSvc --> AppPods["Deployment: marea-app-deployment\n(Strategy: Recreate | 1 Réplica Estricta)"]
        AppPods --> PVC["PVC: recreate-app-pvc (1Gi RWO)\n/data/marea_dulce.db"]
        NP["NetworkPolicy: recreate-app-network-policy"] -.-> AppPods
        SM["ServiceMonitor: recreate-app-servicemonitor"] -.-> AppPods
        PR["PrometheusRule: recreate-app-alert-rules"]
    end
```

## Configuración

Los manifiestos declarativos se organizan dentro de `k8s/`:

- **Namespace:** `k8s/namespace.yaml`
- **Almacenamiento Persistente (PVC):** `k8s/pvc.yaml`
- **Despliegues (Recreate v1 y v2):** `k8s/deployment-v1.yaml` y `k8s/deployment-v2.yaml`
- **Servicio e Ingress:** `k8s/service.yaml` y `k8s/ingress.yaml`
- **Seguridad de Red:** `k8s/networkpolicy.yaml`
- **Observabilidad:** `k8s/servicemonitor.yaml` y `k8s/prometheusrule.yaml`

## Parámetros usados

| Recurso / Componente | Parámetro | Valor Configurado | Propósito |
| :--- | :--- | :--- | :--- |
| Clúster Minikube | `--cpus` / `--memory` | `6 CPUs` / `10240 MB` | Capacidad dimensionada para alojar Marea Dulce, Prometheus/Grafana y la pila ELK concurrentemente. |
| `marea-app-deployment` | `strategy.type` | `Recreate` | Garantiza que el pod anterior termine al 100% antes de iniciar la nueva versión sobre el PVC. |
| `marea-app-deployment` | `spec.replicas` | `1` | Garantiza acceso monousuario y exclusivo a SQLite en PVC ReadWriteOnce. |
| `marea-app-deployment` | `requests` / `limits` | `100m CPU, 128Mi` / `300m CPU, 256Mi` | Garantiza clase QoS `Burstable` y cálculo predecible de recursos en FinOps. |
| Sonda de vida (`livenessProbe`) | `httpGet /healthz` | `initialDelay: 5s, period: 10s` | Reinicia el contenedor automáticamente si el proceso FastAPI deja de responder. |
| Sonda de preparación (`readinessProbe`) | `httpGet /ready` | `initialDelay: 3s, period: 5s` | Retira el pod de los endpoints del Service hasta que la base de datos esté lista. |
| Ingress | `host` / `ingressClassName` | `recreate.local` / `nginx` | Enrutamiento HTTP L7 hacia `marea-app-service` en el puerto `80`. |

## Beneficios

- **Reconciliación declarativa e idempotencia:** Todo el estado de la infraestructura se versiona en Git y se aplica mediante scripts automatizados.
- **Coordinación exacta con el ciclo de vida de datos:** Las sondas de preparación aseguran que ningún cliente reciba errores mientras se inicializa el pod v2.

## Riesgos

- **Multi-Attach en volúmenes RWO:** Prevenido mediante la estrategia Recreate, que asegura 0 réplicas activas antes de montar el volumen en el nuevo pod.

## Buenas prácticas

- Establecer siempre `terminationGracePeriodSeconds: 30` para dar tiempo a la base de datos de cerrar transacciones y sincronizar el WAL a disco.
