# Base de Conocimiento y Guía de Defensa Técnica

Este documento recopila los fundamentos teóricos, la arquitectura interna paso a paso de cada comando y script, y una batería exhaustiva de preguntas y respuestas ("¿Qué pasaría si...?") diseñadas para sustentar y defender el proyecto ante evaluadores técnicos y líderes de ingeniería.

---

## 1. Fundamentos Teóricos de Arquitectura

### 1.1. Estrategias de Despliegue en Kubernetes: Recreate vs. RollingUpdate
- **RollingUpdate (Estrategia Predeterminada):**
  - **Mecanismo:** Actualiza réplicas de forma progresiva. Mediante los parámetros `maxSurge` y `maxUnavailable`, crea Pods de la versión nueva mientras destruye gradualmente los de la versión antigua.
  - **Ventaja:** Cero tiempo de indisponibilidad aparente para el usuario final.
  - **Problema Crítico:** Durante la transición conviven réplicas de ambas versiones. Si la versión 2.0 introduce una migración destructiva en la base de datos (por ejemplo, eliminó una columna o cambió un tipo de dato), las réplicas de la versión 1.0 comenzarán a fallar de forma masiva o corromperán registros en producción.
- **Recreate (`spec.strategy.type: Recreate`):**
  - **Mecanismo:** Ordena al controlador del Deployment reducir inmediatamente las réplicas de la versión anterior a cero. Solo cuando todos los Pods antiguos han sido completamente terminados y desregistrados, programa la creación del nuevo ReplicaSet.
  - **Ventaja:** Garantía absoluta de no convivencia de versiones. Estado determinista en almacenamiento y esquemas.
  - **Trade-off:** Genera una ventana obligatoria de indisponibilidad (*downtime*) que debe ser medida, justificada y minimizada.

### 1.2. Ciclo de Vida del Pod durante la Terminación y Recreación
Cuando se aplica la actualización Recreate (`kubectl apply -f k8s/deployment-v2.yaml`), el plano de control ejecuta los siguientes pasos:
1. **Envío de Señal SIGTERM:** Kubernetes cambia el estado del Pod a `Terminating` y envía la señal de terminación al proceso principal del contenedor (en nuestro caso, `uvicorn`).
2. **Desasociación de Endpoints:** Simultáneamente, el controlador de Endpoints elimina la IP del Pod del objeto `Endpoints` asociado al Servicio. `kube-proxy` actualiza las reglas de filtrado en el nodo (iptables/IPVS).
3. **Periodo de Gracia (`terminationGracePeriodSeconds`):** Por defecto son 30 segundos. El proceso dispone de este lapso para cerrar conexiones activas y vaciar buffers. Si termina antes, el proceso finaliza limpiamente. Si no finaliza al expirar el tiempo, el Kernel envía `SIGKILL`.
4. **Liberación del Volumen:** Al destruirse el Pod, el subsistema de almacenamiento de Kubernetes desmonta el volumen persistente (PVC).
5. **Programación del Nuevo ReplicaSet:** Una vez que el contador de réplicas activas llega estrictamente a cero, el Scheduler programa los nuevos Pods en el nodo.
6. **Ejecución de Sondas:** El contenedor arranca, y hasta que la sonda de preparación (`readinessProbe`) no responda con éxito, el Pod no se añade a los endpoints del Servicio ni recibe tráfico.

### 1.3. Sondas de Salud: Liveness vs. Readiness
- **LivenessProbe (`/healthz`):** Determina si la aplicación está viva. Si falla de forma consecutiva según `failureThreshold`, `kubelet` mata el contenedor y lo reinicia según la política de reinicio.
- **ReadinessProbe (`/ready`):** Determina si la aplicación está lista para procesar tráfico. Si devuelve error o no ha respondido en el arranque, el Pod permanece en estado `Running` pero `Ready: 0/1`. Durante ese periodo, **no recibe tráfico del balanceador**.
- **Impacto en Recreate:** La sonda de readiness evita que el cliente reciba tráfico en Pods a medio inicializar. El downtime medido finaliza en el instante exacto en que la readinessProbe de la versión 2.0 responde con éxito.

### 1.4. Almacenamiento Persistente y Modos de Acceso
- **PersistentVolumeClaim (PVC):** Reclamo declarativo de almacenamiento desacoplado del ciclo de vida efímero del Pod.
- **Modo `ReadWriteOnce` (RWO):** El volumen solo puede ser montado en modo lectura/escritura por un único nodo a la vez. En clústeres multinodo con volúmenes de bloque (ej. AWS EBS o GCE Persistent Disk), un RollingUpdate falla si el nuevo Pod se programa en otro nodo, ya que el disco continúa bloqueado por el Pod antiguo. La estrategia Recreate resuelve esto liberando el disco antes de montar la nueva versión.

### 1.5. Modelos de Telemetría: RED y USE
- **Modelo RED (Diseñado para Microservicios y Servicios Orientados a Solicitudes):**
  - **Rate:** Frecuencia de peticiones por segundo. PromQL: `sum(rate(http_requests_total[1m]))`.
  - **Errors:** Cantidad de peticiones fallidas. PromQL: `sum(rate(http_requests_total{status_code=~"5.."}[1m]))`.
  - **Duration:** Tiempo que toma procesar una solicitud (latencia). PromQL: `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[1m])) by (le))`.
- **Modelo USE (Diseñado para Recursos e Infraestructura):**
  - **Utilization:** Porcentaje de tiempo que el recurso está ocupado.
  - **Saturation:** Grado de sobrecarga o trabajo en cola que no puede procesarse de inmediato.
  - **Errors:** Número de eventos anómalos a nivel de hardware o sistema operativo.

---

## 2. Funcionamiento Paso a Paso de Scripts y Comandos

### 2.1. `scripts/traffic_generator.py` (Medidor de Downtime)
- **Propósito:** Enviar un flujo continuo de peticiones HTTP con intervalo de alta frecuencia (ej. cada 100 ms = 10 peticiones/segundo) para capturar el instante exacto de indisponibilidad.
- **Lógica Interna:**
  1. Utiliza `urllib.request` con un timeout estricto de 1.5 segundos para evitar bloqueos por socket colgado.
  2. Cuando una petición lanza `URLError` (conexión rechazada porque no hay endpoints) o `HTTPError` 502/503 (el Ingress no encuentra backend activo), el script detecta el fallo.
  3. Si es el primer fallo, registra la marca de tiempo exacta en memoria: `downtime_start = time.time()`.
  4. Continúa enviando solicitudes en bucle registrando los errores.
  5. En el instante en que una solicitud responde exitosamente con HTTP 200, calcula la diferencia:
     $$\text{Downtime} = \text{time.time}() - \text{downtime\_start}$$
  6. Imprime el reporte consolidado: solicitudes totales, exitosas, fallidas y duración del corte en segundos con precisión de milisegundos.

### 2.2. `scripts/test_hpa_scaling.py` (Prueba de Estrés para HPA)
- **Propósito:** Generar consumo real de CPU sobre los contenedores para forzar al `HorizontalPodAutoscaler` a rebasar el umbral del 70% y escalar de 2 a 6 réplicas.
- **Lógica Interna:**
  1. Invoca de forma concurrente mediante hilos (`threading.Thread`) el endpoint `/simulate/cpu-load?seconds=0.5`.
  2. En el microservicio, este endpoint ejecuta un bucle iterativo de cálculo matemático intensivo en memoria que mantiene saturado el hilo del procesador asignado al contenedor.
  3. `metrics-server` en Minikube consulta cada 15 segundos el consumo reportado por `cgroup` a través del `kubelet`.
  4. El controlador de HPA calcula la métrica:
     $$\text{Réplicas deseada} = \left\lceil \text{Réplicas actuales} \times \left( \frac{\text{Uso CPU actual}}{\text{Uso CPU objetivo}} \right) \right\rceil$$
  5. Al superar el 70%, el HPA ordena al Deployment duplicar réplicas hasta alcanzar el techo máximo de 6 réplicas.
  6. Cuando el script finaliza, cesa el tráfico y se comprueba la ventana de enfriamiento (*stabilizationWindowSeconds: 60*) antes de reducir réplicas a 2.

### 2.3. `scripts/test_alerts.py` (Disparador de Alarmas)
- **Propósito:** Validar que la pila de observabilidad no es pasiva, sino que notifica incidentes operativos.
- **Lógica Interna:**
  1. Para probar la alarma de tasa de error, envía una ráfaga continua de peticiones al endpoint `/simulate/error?status_code=500`.
  2. El middleware de FastAPI en `app/src/main.py` registra cada petición incrementando la métrica:
     `http_requests_total{status_code="500", endpoint="/simulate/*"}`.
  3. Prometheus evalúa periódicamente su regla de alerta (ej. errores 5xx superiores al 10% en ventana de 1 minuto).
  4. En la consola web de Prometheus, la regla transita:
     - `Inactive`: Condición normal (errores < 10%).
     - `Pending`: La condición se cumple, pero espera el periodo de persistencia (`for: 30s`) para evitar falsos positivos por picos transitorios.
     - `Firing`: La condición se sostuvo más de 30 segundos; la alerta se dispara activamente hacia Alertmanager y Grafana.

---

## 3. Batería de Preguntas Difíciles del Evaluador ("¿Qué Pasaría Si...?")

### Pregunta 1: "¿Por qué el downtime medido fue de ~6 segundos y no de 30 segundos si el grace period de Kubernetes es de 30s?"
- **Respuesta Técnica:**
  > "Porque el parámetro `terminationGracePeriodSeconds: 30` representa un límite máximo de espera, no un retardo forzado. Nuestro microservicio en Python gestiona la señal SIGTERM a través del servidor ASGI Uvicorn. Al recibir la señal, Uvicorn deja de aceptar conexiones nuevas y finaliza inmediatamente las solicitudes en curso. Como el proceso concluyó limpiamente en menos de 1 segundo, el contenedor finalizó de inmediato. Los ~5 segundos restantes del downtime corresponden a la programación del nuevo Pod, la inicialización del entorno y el retardo de 3 segundos configurado en la `readinessProbe` para verificar que la aplicación esté 100% operativa antes de abrir el tráfico."

### Pregunta 2: "¿Qué pasaría si la nueva imagen `v2.0.0` contiene un error de sintaxis y nunca supera el readinessProbe?"
- **Respuesta Técnica:**
  > "En la estrategia Recreate, los Pods de la versión 1 ya fueron eliminados. Si la versión 2.0 falla indefinidamente en el readinessProbe, el clúster quedará con 0 Pods listos (`Ready: 0/1`) y el servicio permanecerá en downtime continuo. En un entorno de producción, este riesgo se mitiga mediante dos mecanismos:
  > 1. Un pipeline de integración continua (CI/CD) previo con pruebas automatizadas que valide la imagen antes del despliegue.
  > 2. Políticas de rollback automatizadas o detección por observabilidad: al activarse la alerta de indisponibilidad prolongada, un operador o pipeline ejecuta `kubectl rollout undo deployment/recreate-app-deployment`, revirtiendo el clúster a la versión 1.0 estable."

### Pregunta 3: "¿Por qué no utilizaron una estrategia Canary o Blue/Green en vez de Recreate?"
- **Respuesta Técnica:**
  > "Tanto Canary como Blue/Green requieren que dos versiones convivan simultáneamente durante un lapso de validación o conmutación. En los casos de uso donde Recreate es obligatorio (como cambios destructivos en bases de datos o volúmenes montados en modo exclusivo ReadWriteOnce), tener dos versiones activas al mismo tiempo provocaría corrupción de datos o fallos de montaje por bloqueo de disco. Si el negocio impone la restricción de que dos versiones jamás deben operar al mismo tiempo, Recreate es la única alternativa arquitectónicamente correcta."

### Pregunta 4: "¿Por qué la NetworkPolicy necesita autorizar explícitamente el puerto 53 en UDP y TCP para Egress?"
- **Respuesta Técnica:**
  > "Porque por defecto, al definir una política de Egress, Kubernetes bloquea todo el tráfico saliente no especificado. El puerto 53 es el puerto estándar del servicio CoreDNS del clúster. Si no se autoriza explícitamente la salida a CoreDNS, el microservicio pierde la capacidad de resolver nombres de dominio internos (como otros servicios del clúster) o externos, degradando la aplicación."

### Pregunta 5: "¿Cómo garantiza el PVC que la información no se borre al destruir los Pods en Recreate?"
- **Respuesta Técnica:**
  > "Porque el ciclo de vida del recurso `PersistentVolumeClaim` (PVC) y del volumen subyacente (`PersistentVolume`) es completamente independiente del ciclo de vida de los Pods. El Pod es efímero; el volumen es duradero. Cuando el Deployment reduce las réplicas a cero, Kubernetes únicamente ejecuta la operación `umount` del sistema de archivos en el contenedor. El disco permanece intacto en el nodo host. Al arrancar el Pod de la versión 2.0, el controlador vuelve a montar el mismo volumen en la ruta `/data`, permitiendo que la nueva versión lea los datos generados por la versión anterior."

### Pregunta 6: "¿Qué impacto financiero registraría Kubecost si el HPA escala a 6 réplicas y se queda allí?"
- **Respuesta Técnica:**
  > "Kubecost calcula el costo financiero en función de los recursos solicitados (`requests`) de CPU y memoria reservados en el nodo. Si la aplicación pasa de 2 a 6 réplicas (triplicando la reserva de recursos de 200m a 600m de CPU y de 256Mi a 768Mi de RAM), el costo por hora proyectado del namespace `recreate-lab` se triplicaría de forma inmediata. Si la carga ya cesó y el clúster no desescala, Kubecost reportaría una caída drástica en el índice de eficiencia (*Cost Efficiency Score*), alertando que la organización está pagando por capacidad ociosa no utilizada."

### Pregunta 7: "¿Por qué se utilizó Prometheus Operator con `ServiceMonitor` en lugar de las anotaciones clásicas `prometheus.io/scrape`?"
- **Respuesta Técnica:**
  > "Las anotaciones clásicas forman parte de un esquema heredado basado en expresiones regulares en la configuración global de Prometheus, lo cual es propenso a errores y poco escalable en clústeres empresariales. El `ServiceMonitor` es un recurso personalizado (CRD) nativo de Kubernetes que desacopla la configuración de scraping: permite que cada equipo declare de forma declarativa cómo, con qué frecuencia y en qué endpoints debe rasparse su servicio, permitiendo que Prometheus Operator regenere dinámicamente la configuración sin reiniciar el servidor de métricas."

