# Guía de Pruebas, Verificación y Medición de Downtime

---

## 1. Verificación Inicial del Entorno

1. **Confirmar estado del clúster y complementos:**
   ```bash
   minikube status
   kubectl get nodes -o wide
   kubectl get pods -n ingress-nginx
   ```

2. **Aplicar los manifiestos base del espacio de nombres `recreate-lab`:**
   ```bash
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/pvc.yaml
   kubectl apply -f k8s/networkpolicy.yaml
   kubectl apply -f k8s/deployment-v1.yaml
   kubectl apply -f k8s/service.yaml
   kubectl apply -f k8s/ingress.yaml
   kubectl apply -f k8s/hpa.yaml
   ```

---

## 2. Prueba de la Estrategia Recreate y Medición de Downtime

Esta prueba mide el tiempo exacto en que la aplicación permanece inaccesible durante la actualización de versión:

1. **Iniciar el generador de tráfico sintético continuo (en una terminal dedicada):**
   ```bash
   python3 scripts/traffic_generator.py --url http://recreate.local --interval 0.1
   ```
2. **Aplicar la actualización a la versión 2.0 (en una segunda terminal):**
   ```bash
   kubectl apply -f k8s/deployment-v2.yaml
   ```
3. **Monitorear en paralelo la transición de Pods:**
   ```bash
   kubectl get pods -n recreate-lab -w
   ```
4. **Resultados esperados en el generador de tráfico:**
   - Registro inmediato de errores HTTP 502/503 o caídas de conexión cuando los Pods v1 entran en `Terminating`.
   - Mensaje de restablecimiento automático con el tiempo exacto de indisponibilidad calculado en segundos (e.g., `Downtime registrado: 6.840 segundos`).
   - Verificación de la versión activa cambiando a `v2.0.0` y contador persistido intacto.

---

## 3. Prueba de Estrés y Validación de Autoescalado (HPA)

Esta prueba valida la reacción del escalador ante saturación de cómputo:

1. **Monitorear el estado del HPA en tiempo real:**
   ```bash
   kubectl get hpa -n recreate-lab -w
   ```
2. **Ejecutar el script de carga concurrente de CPU:**
   ```bash
   python3 scripts/test_hpa_scaling.py --url http://recreate.local --concurrency 20 --duration 60
   ```
3. **Comportamiento esperado:**
   - La utilización de CPU supera el umbral del 70%.
   - El HPA incrementa dinámicamente las réplicas de 2 hasta alcanzar 4, 5 o 6 réplicas.
   - Tras concluir los 60 segundos, el tráfico cesa y el HPA estabiliza y desescala a 2 réplicas tras el periodo de gracia.

---

## 4. Prueba y Activación de Alarmas

Esta prueba fuerza condiciones anómalas para validar la reactividad de Prometheus y Grafana:

1. **Disparar ráfaga de errores 500 (Alarma de Tasa de Error):**
   ```bash
   python3 scripts/test_alerts.py --url http://recreate.local --type errors --errors-count 60
   ```
2. **Disparar solicitudes lentas (Alarma de Latencia Elevada):**
   ```bash
   python3 scripts/test_alerts.py --url http://recreate.local --type latency --latency-count 10 --latency-delay 2.0
   ```
3. **Verificación:**
   - Confirmar en la consola web de Prometheus (`Alerts`) la transición de estado: `Inactive` $\rightarrow$ `Pending` $\rightarrow$ `Firing`.
   - Comprobar en Grafana el panel de alertas visuales.

