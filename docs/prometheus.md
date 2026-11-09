# Prometheus y Alertmanager — Documentación Técnica

**Prometheus** es el sistema líder de monitoreo y base de datos de series temporales (**TSDB**) graduado por la Cloud Native Computing Foundation (CNCF), complementado por **Alertmanager** para la deduplicación, agrupación y enrutamiento de alarmas operativas. En esta plataforma se despliega mediante el operador **`kube-prometheus-stack`** en el namespace `monitoring`.

## Para qué sirve

Sirve para recolectar continuamente métricas numéricas mediante sondeos HTTP periódicos (*scraping*), evaluar reglas de alerta expresadas en lenguaje PromQL y despachar notificaciones cuando los umbrales de salud o rendimiento se ven comprometidos.

**En qué se utilizó en el proyecto:**
- **Recolección de Alta Frecuencia (5 segundos):** Se utilizó un recurso declarativo `ServiceMonitor` (`k8s/servicemonitor.yaml`) configurado con un intervalo de `5s` para raspar las métricas de CoreLedger en el puerto `8000`, permitiendo registrar la ventana de corte de Recreate con precisión.
- **Implementación de Modelos RED y USE:** Se utilizó para medir la tasa de peticiones, porcentaje de errores HTTP 5xx y latencia P95 (modelo RED), así como la utilización y saturación de CPU y memoria de los contenedores (modelo USE).
- **Detección Inmediata de la Ventana Recreate:** Se utilizó la regla de alerta `RecreateDeploymentZeroReplicasWindow` con evaluación sin retraso (`for: 0m`) para activar una alarma en Alertmanager tan pronto como el número de réplicas disponibles cae a `0`.
- **Monitoreo de Integridad de Almacenamiento en PVC:** Se utilizó para vigilar errores de lectura y escritura en la base de datos mediante la regla `PersistentVolumeStorageErrors` sobre la métrica `app_pvc_storage_operations_total`.
- **Generación de Pruebas de Alarma:** Se utilizó el script `scripts/test_alerts.py` para inyectar fallos controlados y comprobar en tiempo real la transición de las 5 reglas desde estado inactivo hasta estado de disparo (*FIRING*).

## Arquitectura

```mermaid
flowchart LR
    subgraph Origenes ["Fuentes de Telemetría"]
        App["CoreLedger Pods (:8000/metrics)\n(prometheus_client Python)"]
        NE["Node Exporter (:9100)\n(CPU, RAM, Disco, Red)"]
        KSM["Kube-State-Metrics (:8080)\n(Pods, Deployments, PVC, HPA)"]
        Cad["Kubelet / cAdvisor\n(Uso de CPU/Memoria por Contenedor)"]
    end

    SM["Recurso: ServiceMonitor\n(recreate-app-servicemonitor\nintervalo: 5s)"] -.-> App
    Origenes --> Prom["Prometheus TSDB (:9090)\n+ Recurso: PrometheusRule (5 Alertas)"]
    Prom -->|"Reglas en estado FIRING"| AM["Alertmanager (:9093)"]
    Prom -->|"Consultas PromQL"| Graf["Grafana (:3000)"]
```

## Configuración

Los manifiestos declarativos y valores de configuración se ubican en:

- **Valores del Despliegue de Observabilidad:** `monitoring/prometheus/values-kube-prometheus-stack.yaml`
- **Recurso de Recolección ServiceMonitor:** `k8s/servicemonitor.yaml`
- **Reglas de Alerta PrometheusRule:** `k8s/prometheusrule.yaml`
- **Instrumentación en el Microservicio:** `app/src/main.py`
- **Script de Pruebas de Alertas:** `scripts/test_alerts.py`

## Parámetros usados

| Parámetro / Regla | Valor Configurado | Descripción |
| :--- | :--- | :--- |
| Intervalo de Recolección | `5s` (tiempo de espera: `3s`) | Alta frecuencia para registrar la ventana de corte de Recreate (~6 a 9 segundos). |
| Preservación de Etiquetas | `honorLabels: true` | Mantiene las etiquetas originales emitidas por la aplicación (`version`, `schema_version`, etc.). |
| Regla 1: Ventana de Cero Réplicas Recreate | `kube_deployment_status_replicas_available == 0` (`for: 0m`) | Disparo inmediato en cuanto el despliegue Recreate detiene todas las réplicas activas. |
| Regla 2: Alta Tasa de Errores HTTP 5xx | `sum(rate(http_requests_total{status_code=~"5.."}[1m])) > 0.2` (`for: 10s`) | Alerta crítica ante ráfagas de errores en la API de la aplicación. |
| Regla 3: Alta Latencia HTTP P95 | `histogram_quantile(0.95, ...) > 1.0` (`for: 10s`) | Alerta cuando el percentil 95 de tiempo de respuesta supera 1.0 segundo. |
| Regla 4: Alto Uso de CPU por Pod | `(rate(container_cpu_usage_seconds_total[1m]) / 0.30) * 100 > 80` (`for: 15s`) | Alerta cuando un contenedor supera el 80% de su límite asignado (`300m`). |
| Regla 5: Errores en Almacenamiento PVC | `rate(app_pvc_storage_operations_total{status="error"}[1m]) > 0` (`for: 5s`) | Alerta crítica ante cualquier fallo en operaciones sobre `/data/recreate_platform.db`. |

## Beneficios

- **Resolución temporal de 5 segundos adaptada a Recreate:** Un intervalo estándar de 30 o 60 segundos pasaría por alto una interrupción de 7 segundos; con 5 segundos la ventana queda registrada fielmente en las gráficas.
- **Descubrimiento automático de réplicas:** El operador detecta y comienza a monitorear nuevas instancias escaladas por el HPA de manera dinámica.

## Riesgos

- **Explosión de cardinalidad en rutas HTTP:** Si cada identificador de transacción generara una etiqueta única, la memoria de la base de series temporales crecería indefinidamente. Se evitó normalizando las rutas dinámicas bajo el prefijo `/api/*`.

## Buenas prácticas

- Configurar selectores abiertos en los valores del operador para que descubra recursos `ServiceMonitor` y `PrometheusRule` ubicados en cualquier namespace del clúster.
