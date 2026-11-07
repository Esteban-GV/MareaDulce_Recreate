# Seguridad, Políticas de Red y Control de Acceso

---

## 1. Políticas de Red (Network Policies)

En conformidad con las mejores prácticas de seguridad en Kubernetes, el tráfico entre Pods y espacios de nombres se restringe de forma declarativa mediante [`k8s/networkpolicy.yaml`](file:///home/guarinve/Documentos/k8s-recreate-deployment/k8s/networkpolicy.yaml).

### Reglas de Aislamiento Ingress (Entrada)
1. **Tráfico Externo y de Aplicación:** Se permite la entrada únicamente hacia el puerto TCP 8000 desde el Ingress Controller.
2. **Scraping de Observabilidad:** Se autoriza la conexión en el puerto TCP 8000 exclusivamente desde el espacio de nombres `monitoring` donde opera el operador de Prometheus.
3. **Tráfico no Autorizado:** Cualquier intento de comunicación no explícito queda bloqueado por defecto.

### Reglas de Aislamiento Egress (Salida)
1. **Resolución DNS:** Se autorizan consultas DNS sobre el puerto UDP/TCP 53 hacia el servicio CoreDNS del clúster.
2. **Aislamiento de Red:** Se bloquea la comunicación saliente arbitraria a Internet o a componentes internos que no participen en el ciclo transaccional.

---

## 2. Enrutamiento con Ingress Controller

El archivo [`k8s/ingress.yaml`](file:///home/guarinve/Documentos/k8s-recreate-deployment/k8s/ingress.yaml) define el enrutamiento HTTP sobre el dominio `recreate.local`:
- Enrutamiento basado en prefijo `/` hacia el servicio `recreate-app-service` en el puerto 80.
- Reescritura de cabeceras compatible con `ingress-nginx`.

---

## 3. Autenticación Robusta y Simulación de SSO

El microservicio en Python expone el endpoint `/api/auth/verify` para validar identidad mediante Single-Sign-On (SSO):
- Supera esquemas convencionales de usuario y contraseña en texto plano.
- Requiere cabecera `Authorization: Bearer <token>` simulando validación de tokens OAuth2 / OpenID Connect.
- Devuelve el contexto del usuario autenticado y su rol de ingeniería de plataformas.

