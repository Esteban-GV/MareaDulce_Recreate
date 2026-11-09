# Autenticación SSO / OIDC y Verificación MFA — Documentación Técnica

El módulo de **Identidad y Control de Acceso de Marea Dulce** implementa un flujo de autenticación inspirado en los estándares **OpenID Connect (OIDC)** con validación obligatoria de **Factor Múltiple de Autenticación (`MFA / TOTP` de 6 dígitos)**, emisión de credenciales de sesión tipo **Bearer Token (`marea_sso_<sha256>`)** y exportación de telemetría de eventos de seguridad hacia Prometheus.

## Para qué sirve

Sirve para autenticar a los administradores de la pastelería y clientes autorizados antes de permitir operaciones sobre el catálogo, inventario y despacho de pedidos, verificando la identidad del usuario (`username`) y el código temporal de segundo factor (`mfa_code`).

**En qué se utilizó en el proyecto:**
- **Control de Acceso Administrativo a la Tienda:** Se utilizó para proteger los endpoints administrativos y de gestión de catálogo de Marea Dulce mediante la emisión de tokens en `POST /api/v1/auth/token` (o `/api/auth/token`) y su posterior validación en `/api/auth/verify`.
- **Validación de Segundo Factor (MFA):** Se utilizó para exigir un código numérico de 6 dígitos (por ejemplo `482910`), simulando el flujo de una aplicación de autenticación TOTP antes de otorgar el nivel de acceso `aal2_mfa`.
- **Acción Interactiva y Pruebas en Vivo:** Se utilizó para validar en tiempo real los flujos de seguridad tanto en la interfaz web como mediante scripts de validación, observando las peticiones y respuestas JSON.
- **Auditoría y Detección de Intentos Fallidos:** Se utilizó la métrica `app_auth_events_total` etiquetada por operación (`token_issue`, `token_verify`) y resultado (`success`, `valid`, `invalid`) para monitorear intentos de acceso no autorizado en Prometheus y Grafana.

## Arquitectura

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Administrador / UI Marea Dulce
    participant TokenAPI as POST /api/auth/token
    participant VerifyAPI as POST /api/auth/verify
    participant Metrics as Contador Prometheus (app_auth_events_total)

    Admin->>TokenAPI: {"username": "admin@mareadulce.com", "mfa_code": "482910"}
    TokenAPI->>TokenAPI: Valida formato MFA (6 dígitos numéricos)
    TokenAPI->>TokenAPI: Genera firma SHA-256 (marea_sso_<digest>)
    TokenAPI->>Metrics: Incrementa {operation="token_issue", result="success"}
    TokenAPI-->>Admin: 200 OK (access_token, token_type="Bearer", mfa_verified=true)
    Admin->>VerifyAPI: Cabecera Authorization: Bearer marea_sso_<digest>
    VerifyAPI->>VerifyAPI: Verifica prefijo, estructura y longitud de firma
    VerifyAPI->>Metrics: Incrementa {operation="token_verify", result="valid"}
    VerifyAPI-->>Admin: 200 OK (valid=true, auth_level="aal2_mfa")
```

## Configuración

La implementación del módulo de identidad se encuentra en:

- **Controladores y Modelos de Datos:** `app/src/main.py` y módulos en `app/src/routers/auth.py`
- **Pruebas Automatizadas de Emisión y Rechazo:** `scripts/validate.sh`

## Parámetros usados

| Parámetro / Endpoint | Valor Configurado | Descripción |
| :--- | :--- | :--- |
| `POST /api/auth/token` | `username` + `mfa_code` (6 dígitos) | Emite un token Bearer firmado con SHA-256 si el segundo factor MFA es válido. |
| `POST /api/auth/verify` | Cabecera `Authorization: Bearer <token>` | Valida la autenticidad e integridad del token emitido. |
| Nivel de Autenticación (`auth_level`) | `aal2_mfa` | Nivel de aseguramiento de autenticación multi-factor verificado. |
| Tiempo de Expiración (`expires_in`) | `3600` (1 hora) | Ventana de validez declarada para el token de sesión. |
| Métrica de Seguridad | `app_auth_events_total` | Contador Prometheus que audita intentos válidos, expirados o rechazados. |

## Beneficios

- **Seguridad reforzada con segundo factor (MFA):** Rechaza inmediatamente con código `HTTP 401 Unauthorized` cualquier solicitud cuyo código de segundo factor no cumpla la validación requerida.
- **Visibilidad de seguridad en tiempo real:** Todos los eventos de emisión y verificación quedan expuestos en `/metrics` para detección de intentos de fuerza bruta.

## Riesgos

- **Reutilización de tokens interceptados en tránsito sin cifrado:** Si el tráfico viaja en texto plano, un tercero podría capturar la cabecera `Bearer`; se mitiga en entornos productivos habilitando terminación TLS en el controlador Ingress NGINX.

## Buenas prácticas

- Exigir siempre el esquema `Bearer` en la cabecera `Authorization` y rechazar tokens truncados o con longitud de hash inválida.
- Auditar en Prometheus la relación entre intentos fallidos y exitosos en la métrica `app_auth_events_total`.
