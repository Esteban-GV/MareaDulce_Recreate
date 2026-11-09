# Guía Completa Paso a Paso: Instalación, Ejecución e Inspección de Servicios — CoreLedger

Este documento es el manual operativo maestro de **CoreLedger Cloud-Native Platform (`k8s-recreate-deployment`)**. Explica desde los requisitos del sistema y qué realiza cada comando de terminal hasta **cómo abrir cada página web en el navegador, qué elementos visuales revisar y qué acciones interactivas ejecutar en cada servicio**.

## Requisitos del Sistema y Prerrequisitos

### Especificaciones de Hardware Recomendadas

| Recurso en el Host | Mínimo Requerido | Asignado a Minikube (`start_minikube.sh`) | Propósito |
| :--- | :---: | :---: | :--- |
| Procesador (CPU) | 8 Hilos | 6 CPUs | Ejecutar simultáneamente CoreLedger (2 a 6 pods), Prometheus, Grafana, Elasticsearch y Kibana. |
| Memoria RAM | 15 a 16 GiB | 10240 MB (10 GiB) | Reservar 10 GiB para el clúster dejando ~5 GiB libres para el sistema operativo y el navegador. |
| Disco Libre | 20 GB SSD | Dinámico (PVC de 1 GiB) | Imágenes Docker, base de datos temporal de Prometheus, índices de Elasticsearch y SQLite. |

### Verificación Automática de Herramientas

Ejecute el script de prerrequisitos para validar las herramientas necesarias en el sistema anfitrión y el parámetro de kernel de memoria mapeada:

```bash
bash scripts/install_prerequisites.sh
```

> **Nota sobre permisos de Docker en Linux:** En sistemas Linux, los scripts de la plataforma (`start-all.sh`, `start_minikube.sh`, `stop-all.sh`, etc.) cuentan con detección y auto-activación automática del grupo `docker` vía `newgrp docker`. Si ejecutas comandos manuales de Docker o Minikube en una terminal recién abierta sin haber reiniciado la sesión de usuario, ejecuta `newgrp docker` una vez en dicha terminal.

## Despliegue Rápido Automatizado

Toda la plataforma se levanta, reconcilia y valida mediante 4 comandos maestros:

```bash
# 1. Iniciar Minikube, compilar imágenes v1 y v2, y desplegar toda la plataforma
bash scripts/start-all.sh

# 2. Abrir los túneles locales en segundo plano hacia todos los servicios y tableros
bash scripts/forward_services.sh start

# 3. Ejecutar la suite automatizada de 16 validaciones E2E
bash scripts/validate.sh

# 4. Ejecutar el benchmark sintético de fiabilidad y latencia HTTP
bash scripts/benchmark.sh
```

## Despliegue Manual Paso a Paso

Si desea ejecutar o explicar el despliegue fase por fase durante la sustentación, siga estos pasos en orden:

### Inicializar el Clúster Minikube y Construir Imágenes

```bash
bash scripts/start_minikube.sh
```
- **Qué hace este comando:**
  1. Inicia el nodo Minikube con 6 CPUs y 10240 MB de memoria utilizando el controlador de Docker.
  2. Habilita los complementos oficiales `ingress`, `metrics-server`, `default-storageclass` y `storage-provisioner`.
  3. Construye dentro del demonio de Minikube las imágenes `recreate-app:v1.0.0` y `recreate-app:v2.0.0`.

### Crear el Espacio de Nombres y el Volumen Persistente

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/pvc.yaml
kubectl get pvc -n recreate-lab
```
- **Qué hace este comando:**
  1. Crea el namespace aislado `recreate-lab`.
  2. Solicita un volumen persistente de 1 GiB en modo `ReadWriteOnce` (`recreate-app-pvc`), donde residirá la base SQLite.
  3. Verifica que la columna de estado muestre `Bound` (enlazado).

### Desplegar la Pila de Observabilidad (Prometheus, Grafana y Alertmanager)

```bash
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring \
  -f monitoring/prometheus/values-kube-prometheus-stack.yaml \
  --wait

kubectl create configmap recreate-app-grafana-dashboard \
  -n monitoring \
  --from-file=grafana-dashboard-recreate.json=monitoring/prometheus/grafana-dashboard-recreate.json \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl label configmap recreate-app-grafana-dashboard -n monitoring grafana_dashboard="1" --overwrite
```
- **Qué hace este comando:**
  1. Instala el operador de Prometheus, Alertmanager, Grafana, exportadores de métricas de nodos y estado del clúster en `monitoring`.
  2. Inyecta el archivo JSON con los 12 paneles en un mapa de configuración con la etiqueta que activa la importación automática en Grafana.

### Desplegar la Pila de Registros Centralizados ELK

```bash
kubectl apply -f monitoring/elk/values-elk.yaml
kubectl get pods -n monitoring -w
```
- **Qué hace este comando:**
  1. Despliega la instancia de Elasticsearch con memoria ajustada a 512 MiB, el agente recolector Filebeat con metadatos de Kubernetes y la interfaz Kibana.

### Desplegar el Microservicio, Red, Autoescalado y Alertas

```bash
kubectl apply -f k8s/deployment-v1.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/networkpolicy.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/servicemonitor.yaml
kubectl apply -f k8s/prometheusrule.yaml
```
- **Qué hace este comando:**
  1. Despliega la versión `v1.0.0` de CoreLedger con estrategia `Recreate`.
  2. Configura el servicio interno, la ruta de Ingress `recreate.local`, las políticas de seguridad de red y el autoescalador HPA.
  3. Registra el recurso de recolección de métricas cada 5 segundos y las 5 reglas de alarma operativas.

## Apertura de Túneles Locales y Tabla de Acceso Rápido

Para acceder a las interfaces desde su navegador local, ejecute:

```bash
bash scripts/forward_services.sh start
```

| Servicio / Plataforma | URL Directa en el Navegador | Credenciales | Propósito Principal |
| :--- | :--- | :---: | :--- |
| **Interfaz Web de CoreLedger** | `http://localhost:8080` | Sin credenciales | Panel interactivo de transacciones SQLite en PVC, SSO/MFA y simulador de carga/errores. |
| **Documentación OpenAPI (Swagger)** | `http://localhost:8080/docs` | Sin credenciales | Documentación interactiva para probar los endpoints de la API. |
| **Tablero de Grafana (12 Paneles)** | `http://localhost:3000/d/coreledger-recreate-red-use` | `admin` / `admin123` | Tablero unificado de estrategia Recreate, modelos RED y USE, operaciones en PVC y FinOps. |
| **Servidor Prometheus** | `http://localhost:9090/alerts` | Sin credenciales | Estado de las 5 reglas de alarma operativas y objetivos de recolección (`/targets`). |
| **Gestor de Alarmas Alertmanager** | `http://localhost:9093` | Sin credenciales | Bandeja central de alarmas activadas en estado de disparo (*FIRING*). |
| **Kibana (Pila ELK)** | `http://localhost:5601/app/discover` | Sin credenciales | Explorador centralizado de registros de contenedores con metadatos de Kubernetes. |

## Guía Página por Página: Qué Ver y Qué Hacer en Cada Servicio

### Interfaz Web de CoreLedger (`http://localhost:8080`)

Al abrir `http://localhost:8080` verá el panel de control operativo:

- **Barra de Navegación Superior:** Accesos directos para abrir en nuevas pestañas Grafana, Prometheus, Alertmanager, Kibana, Swagger y las métricas crudas.
- **Insignia de Versión y Monitoreo en Tiempo Real:** Identifica la versión activa (**Azul** para `v1.0.0` o **Verde Esmeralda** para `v2.0.0`). Incluye actualización automática en segundo plano cada 3 segundos sin recargar la página.
- **Seis Tarjetas de Estado:**
  - *Pod Activo y Topología:* Nombre del pod que atiende la solicitud, nodo, dirección IP y tiempo de actividad.
  - *Estado del Despliegue:* Confirmación de estado `READY` bajo estrategia `Recreate` y rango del HPA (2 a 6 réplicas).
  - *Base de Datos en PVC:* Estado de conexión, tamaño del archivo en disco y modo `WAL`.
  - *Control de Concurrencia:* Mecanismo `BEGIN IMMEDIATE` con bloqueo exclusivo verificado.
  - *Registros Persistidos:* Conteo total de transacciones, volumen financiero acumulado en dólares y contador de peticiones.
  - *Esquema Activo:* Indicación de la estructura de base de datos activa (8 columnas en v1 vs 11 columnas en v2).
- **Acciones Interactivas y Pruebas en Vivo:**
  - *Nueva Transacción en PVC:* Despliega una ventana modal donde puede ingresar un concepto contable y monto personalizado para insertarlo de inmediato en SQLite.
  - *Transacción Rápida:* Genera un asiento financiero aleatorio con un solo clic y muestra el resultado en la consola inferior.
  - *Probar SSO / MFA:* Ejecuta en vivo la solicitud de token OIDC con código de segundo factor y valida su firma digital.
  - *Simular Carga de CPU:* Ejecuta un ciclo de estrés de cálculo en el pod para elevar el consumo y verificar la gráfica de utilización en Grafana.
  - *Simular Error HTTP 500:* Dispara una respuesta de error intencional para probar el panel de errores y la alarma correspondiente en Alertmanager.

### Interfaz Swagger y Documentación OpenAPI (`http://localhost:8080/docs`)

1. Abra `http://localhost:8080/docs`.
2. Explore los endpoints interactivos (`/api/info`, `/api/transactions`, `/api/schema-status`, `/api/auth/token`, `/api/auth/verify`).
3. Presione el botón **Try it out** y luego **Execute** para enviar peticiones directamente y revisar respuestas y esquemas JSON validados.

### Tablero de Control en Grafana (`http://localhost:3000/d/coreledger-recreate-red-use`)

1. Ingrese con usuario `admin` y contraseña `admin123`.
2. Abra el enlace directo o busque el tablero `CoreLedger - Estrategia Recreate & Observabilidad RED/USE`.
3. **Qué inspeccionar en los 12 paneles:**
   - *Panel 1 (Réplicas Disponibles):* Muestra 2 réplicas en régimen normal y cae a 0 durante la transición de Recreate.
   - *Panel 2 (Estado de Ventana de Interrupción):* Indicador que conmuta a rojo mientras la disponibilidad es nula.
   - *Panel 3 (Transición de Versión):* Serie temporal que muestra cómo la curva de `v1.0.0` cae a cero antes del nacimiento de `v2.0.0`.
   - *Paneles 4, 5 y 6 (Modelo RED):* Peticiones por segundo, tasa de errores 5xx y percentil 95 de latencia.
   - *Paneles 7 y 8 (Modelo USE):* Uso de CPU respecto al límite de 300m y consumo de memoria RAM de los contenedores.
   - *Panel 9 (Operaciones en PVC):* Tasa de inserciones y lecturas sobre `/data/recreate_platform.db`.
   - *Paneles 10, 11 y 12 (FinOps):* Costo mensual proyectado de cómputo, volumen PVC y costo total estimado en dólares.

### Servidor de Métricas Prometheus (`http://localhost:9090`)

1. Ingrese a la sección de objetivos (`/targets`) y verifique que `recreate-app-servicemonitor` se encuentre en estado `UP`.
2. Ingrese a la sección de alertas (`/alerts`) y confirme que las 5 reglas del grupo `recreate.deployment.rules` se encuentren activas y en evaluación.

### Gestor de Alarmas Alertmanager (`http://localhost:9093`)

1. Abra `http://localhost:9093`.
2. Ejecute el script de prueba de alertas para generar anomalías controladas:
   ```bash
   python3 scripts/test_alerts.py --url http://localhost:8080
   ```
3. Observe cómo las alarmas de error HTTP y latencia pasan al estado de disparo (*FIRING*) en la bandeja principal.

### Exploración de Registros en Kibana (`http://localhost:5601/app/discover`)

1. Abra `http://localhost:5601/app/discover` con la vista de datos `filebeat-*`.
2. Aplique el filtro `kubernetes.namespace : "recreate-lab"`.
3. Observe en tiempo real las líneas de registro emitidas por los pods, incluyendo la captura de señales `SIGTERM` y las migraciones de base de datos.

## Demostración en Vivo de la Estrategia Recreate

Para ejecutar la demostración completa del relevo de versión y medir el tiempo exacto de indisponibilidad:

1. **Terminal 1 — Monitoreo de pods en tiempo real:**
   ```bash
   kubectl get pods -n recreate-lab -l app=recreate-app -w
   ```
2. **Terminal 2 — Generador de tráfico continuo y cronómetro:**
   ```bash
   python3 scripts/traffic_generator.py --url http://localhost:8080/api/info --interval 0.2
   ```
3. **Terminal 3 — Aplicar la actualización a la versión v2.0.0:**
   ```bash
   kubectl apply -f k8s/deployment-v2.yaml
   ```
4. **Comprobaciones durante y después de la transición:**
   - En la Terminal 1, observe que los pods de `v1.0.0` se detienen por completo antes de que se inicien los de `v2.0.0`.
   - En la Terminal 2, el generador reporta la duración exacta de la interrupción (~6 a 9 segundos) y confirma el cambio de versión.
   - En el navegador (`http://localhost:8080`), la interfaz cambia de color a verde esmeralda y el esquema muestra 11 columnas con todas las transacciones históricas conservadas.
5. **Restaurar al estado inicial (Rollback a v1.0.0):**
   ```bash
   bash scripts/status.sh --reset-v1
   ```
