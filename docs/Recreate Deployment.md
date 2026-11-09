# Apuntes y Requerimientos Consolidados: Entrega Plataformas II

**Integrantes:**
- Esteban Guarín Valencia
- Juan José Arias Gallego

---

## 1. Alcance General de la Entrega
- Realizar un despliegue en Kubernetes implementando la estrategia **Recreate**.
- Integrar una **Observabilidad Completa** con las métricas correctas, logs, trazas, eventos y alertas.
- Sustentación en vivo: Demostración técnica y de negocio de ~5 minutos.

---

## 2. Subtareas y Componentes Técnicos Mandatorios

1. **Montaje de la Aplicación en el Clúster de Kubernetes:**
   - Aplicación base desacoplada y funcional.
   - Definición de políticas de red (**Network Policies**) para control estricto de tráfico Ingress/Egress.
   - Persistencia de datos mediante **PersistentVolumeClaim (PVC)** y StorageClass correspondiente.
   - Estrategia de despliegue configurada explícitamente en `spec.strategy.type: Recreate`.

2. **Autoescalado Horizontal de Pods (HPA):**
   - Reglas de HPA concisas y sustentables basadas en métricas de consumo (CPU/Memoria/Custom Metrics).
   - Justificación técnica basada en el perfil de uso de la aplicación y picos estacionales/fechas clave de negocio.

3. **Gestión de Costos con Kubecost:**
   - Implementación de **Kubecost** en el clúster.
   - Visualización y correlación de consumo de recursos frente a costos monetarios estimados mediante su dashboard respectivo.

4. **Pila de Centralización de Logs (ELK / EFK):**
   - Recopilación, procesamiento, almacenamiento y visualización de grandes volúmenes de registros en tiempo real.
   - Correlación de logs de acceso y errores con el ciclo de terminación y recreación de Pods.

5. **Seguridad y Control de Acceso (Autenticación Avanzada / SSO):**
   - Implementación de inicio de sesión único (**SSO**) o mecanismo de autenticación robusto con validación integral (multifactor o tokens verificados), superando esquemas básicos de usuario y contraseña simple.

6. **Observabilidad Integral en Dashboards:**
   - Consolidación unificada de los pilares de observabilidad: **Métricas, Logs, Traces, Eventos y Alertas**.
   - Definición de reglas de alerta operativas (ej. umbral de saturación >80%, incremento de latencia, tasa de error 5xx durante la ventana de downtime).

7. **Orientación y Presentación para el Negocio:**
   - Estructuración del dashboard para responder a expectativas del negocio (evaluación de impacto al cliente final, determinación del modelo B2B o B2C).
   - Medición cuantitativa del tiempo de interrupción del servicio (*downtime*) y afectación transaccional.

8. **Diapositivas y Caso de Negocio:**
   - Elaboración de material de apoyo visual con la formulación integral del caso de negocio y justificación técnica.

9. **Documentación Técnica y Guion de Presentación:**
   - Redacción de la documentación formal del proyecto.
   - Preparación del guion sincronizado para la sustentación oral en vivo.

---

## 3. Marco de Métricas y Modelos de Telemetría

### Modelos de Monitoreo
- **Modelo RED:**
  - *Rate:* Tasa de peticiones atendidas por segundo.
  - *Errors:* Tasa de solicitudes fallidas (502, 503, caídas de conexión durante Recreate).
  - *Duration:* Latencia en el procesamiento de transacciones.
- **Modelo USE:**
  - *Utilization:* Porcentaje de uso de CPU, memoria y almacenamiento.
  - *Saturation:* Estrangulamiento de cómputo y encolamiento.
  - *Errors:* Fallos a nivel de red, almacenamiento o nodos.

### Pirámide de Observabilidad en Kubernetes
1. **Recursos de Infraestructura:** Consumo físico/virtual de nodos, interfaces de red (Ingress/Egress), capacidad total vs. utilizada.
2. **Componentes del Clúster:** Salud del API Server, ETCD, Scheduler y controladores.
3. **Cargas de Trabajo y Pods:** Estado de réplicas (`Running`, `Terminating`), tasa de reinicios, tiempo de vida y Pods no programados.
4. **Aplicación y Servicios:** Sondas de salud (`livenessProbe`, `readinessProbe`), tiempos de respuesta y transacciones de negocio.

### Requisitos de Calidad de las Métricas
Las métricas recolectadas deben ser:
- Específicas
- Accionables
- Relevantes
- Oportunas
- Medibles

---

## 4. Herramientas Auxiliares y Tecnologías Clave

- **Orquestador:** Kubernetes (Minikube / clúster de laboratorio).
- **Herramientas de Operación:** Lens (Kubernetes IDE), Terraform (por confirmar).
- **Pila de Observabilidad y Telemetría:** Prometheus, Grafana, Alertmanager, Kubecost.
- **Gestión de Logs:** Pila ELK (Elasticsearch, Logstash/Fluentbit, Kibana).
