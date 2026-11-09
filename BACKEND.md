# BACKEND.md: Arquitectura e Implementación del Backend de Marea Dulce

> **Módulo:** Backend API Cloud-Native  
> **Framework:** FastAPI con Python 3.11+ / Uvicorn  
> **Persistencia:** SQLite en modo WAL sobre Kubernetes PVC (`ReadWriteOnce`, 1 réplica)  
> **Estrategia de Despliegue:** Kubernetes Recreate  
> **Versión Actual:** 1.0.0  
> **Fecha:** 2026-11-09  

---

## 1. Arquitectura Modular y Hexagonal

El backend ha sido reestructurado siguiendo una arquitectura modular desacoplada que separa el dominio, la infraestructura de persistencia, la lógica de negocio transaccional y los controladores de la API:

```
app/src/
├── main.py                     # Punto de entrada FastAPI con lifespan y middleware de métricas
├── core/
│   ├── config.py               # Configuración declarativa mediante Pydantic Settings y variables de entorno
│   ├── security.py             # Criptografía bcrypt (hashing de contraseñas) y tokens JWT (Bearer)
│   └── metrics.py              # Métricas de telemetría y negocio instrumentadas en Prometheus
├── domain/
│   ├── constants.py            # Enums de estado, máquina de transiciones válidas y alérgenos
│   └── schemas.py              # Modelos Pydantic v2 (Input, Output, ConfigDict)
├── infrastructure/
│   ├── database.py             # Conexión SQLite con pragmas WAL, timeouts y control transaccional
│   ├── migrations.py           # Migraciones versionadas, reversibles, con PRAGMA integrity_check y .backup
│   └── seed.py                 # Siembra del catálogo oficial (6 categorías, 12 productos, admin inicial)
├── repositories/
│   ├── user_repo.py            # Persistencia de usuarios y credenciales
│   ├── category_repo.py        # CRUD y jerarquía de categorías
│   ├── product_repo.py         # Catálogo de productos, filtros, búsqueda y stock
│   ├── order_repo.py           # Creación atómica (BEGIN IMMEDIATE), inventario e idempotencia
│   └── custom_order_repo.py    # Gestión de pedidos y cotizaciones personalizadas
└── routers/
    ├── system.py               # /healthz, /ready, /api/v1/version, /metrics
    ├── auth.py                 # /api/v1/auth (registro, login, me)
    ├── categories.py           # /api/v1/categories (CRUD público y admin)
    ├── products.py             # /api/v1/products (filtros, stock, admin)
    ├── orders.py               # /api/v1/orders (checkout, idempotencia, tracking)
    ├── custom_orders.py        # /api/v1/custom-orders (solicitudes especiales)
    └── admin.py                # /api/v1/admin (KPIs en tiempo real, inventario consolidado)
```

---

## 2. Entidades del Dominio

1. **`User`:** Identificador único, correo electrónico único en minúsculas, nombre completo, teléfono, hash seguro con salt `bcrypt` y rol (`cliente` o `administrador`).
2. **`Category`:** Nombre, slug amigable único, descripción opcional, orden de visualización y estado activo.
3. **`Product`:** Relación con categoría (`ON DELETE RESTRICT`), nombre, slug, descripción de autor, precio en enteros COP (`price_cop`), porciones, tiempo de preparación en horas, ingredientes, lista de alérgenos en JSON, imagen URL, insignia (`badge`), stock en enteros no negativos, estado activo y destacado.
4. **`Order`:** Código legible único (`MD-AAAA-NNNNNN`), relación opcional con `User`, datos del cliente, modalidad de entrega (`domicilio` o `recogida_tienda`), dirección, fecha y franja de entrega, estado del flujo, método de pago (`simulado_demo`), estado del pago, total en COP, notas y clave de idempotencia única (`idempotency_key`).
5. **`OrderItem`:** Relación con `Order` y `Product`, precio unitario capturado al momento de compra, cantidad solicitada, subtotal en COP y atributos de personalización (`servings`, `flavor`, `custom_message` limitado a 40 caracteres, `delivery_slot`, `notes`).
6. **`CustomOrderRequest`:** Solicitud de cotización para tortas temáticas o mesas de postres, porciones, fecha requerida, descripción, URL de imagen de referencia, estado y precio estimado en COP.

---

## 3. Reglas de Negocio Estrictas

### 3.1 Manejo de Dinero en Enteros COP
Toda operación monetaria se almacena y calcula estrictamente como **número entero (`INTEGER`) en Pesos Colombianos (COP)**. No se utilizan números de punto flotante (`float`) en ninguna capa de la aplicación, evitando desajustes por redondeo binario.

### 3.2 Transiciones de Estado del Pedido
La máquina de estados de un pedido valida cada transición contra una matriz permitida:

$$\text{PENDIENTE} \longrightarrow \text{CONFIRMADO} \longrightarrow \text{EN\_PREPARACION} \longrightarrow \text{LISTO} \longrightarrow \text{ENTREGADO}$$

* **Cancelación:** Permitida desde `PENDIENTE`, `CONFIRMADO` y `EN_PREPARACION`. Al cancelar una orden, el backend **reintegra automáticamente el stock reservado** a la tabla de productos dentro de la misma transacción.
* **Transiciones prohibidas:** Cualquier salto no permitido (ej. `PENDIENTE -> ENTREGADO` o modificar una orden `ENTREGADA`) retorna `400 Bad Request` indicando la violación de la regla de negocio.

### 3.3 Control de Inventario Atómico y Concurrencia
* La creación de órdenes ejecuta un bloqueo transaccional inmediato con `BEGIN IMMEDIATE;` en SQLite.
* Antes de descontar, se verifica que cada producto cuente con `stock >= cantidad_solicitada`.
* Si algún producto no tiene suficientes unidades, la transacción se aborta (`ROLLBACK;`) y se emite un error `400 Bad Request: Stock insuficiente para [Producto]. Disponible: X, solicitado: Y`.
* Ninguna venta concurrente puede vender la misma última unidad.

### 3.4 Idempotencia Estricta en Creación de Pedidos (`Idempotency-Key`)
* El cliente web envía la cabecera HTTP `Idempotency-Key: <UUIDv4>`.
* Si ocurre un corte de red o el cliente reenvía la petición, el backend detecta la clave existente y retorna la orden creada previamente sin duplicar el registro ni volver a descontar el inventario.

### 3.5 Código de Pedido Legible
Formato estandarizado: `MD-AAAA-NNNNNN` (ejemplo: `MD-2026-000001`), donde `AAAA` es el año en curso y `NNNNNN` es un correlativo secuencial de 6 dígitos con relleno de ceros.

### 3.6 Pagos Simulados (Sandbox Seguro)
La plataforma no solicita, procesa ni almacena números de tarjeta de crédito reales. Todas las transacciones operan bajo el método `simulado_demo` con estado automático `PAGADO_DEMO`, ideal para entornos académicos y demostraciones técnicas.

---

## 4. Persistencia, Modo WAL y Migraciones

### 4.1 Configuración de SQLite
La base de datos se aloja en `/data/marea_dulce.db` (enlazado al PersistentVolumeClaim de Kubernetes). Se aplican los siguientes pragmas en cada conexión:
* `PRAGMA journal_mode = WAL;`: Escrituras continuas concurrentes con lecturas sin bloqueo.
* `PRAGMA synchronous = NORMAL;`: Balance óptimo de integridad y latencia en volúmenes montados.
* `PRAGMA foreign_keys = ON;`: Integridad referencial estricta.
* `PRAGMA busy_timeout = 10000;`: Espera de hasta 10 segundos ante bloqueos de escritura antes de emitir error `busy`.

### 4.2 Respaldo Nativo e Integridad
* Se implementó `backup_database(backup_dir)` utilizando la API nativa `source_conn.backup(dest_conn)`, garantizando copias en caliente consistentes sin interrumpir lectores.
* Toda migración o inicio de servicio verifica el estado físico del archivo ejecutando `PRAGMA integrity_check;`. Si el resultado no es `ok`, el sistema bloquea el arranque protegiendo los datos.

---

## 5. Datos Iniciales del Catálogo Oficial (Seed)

El script `src/infrastructure/seed.py` carga automáticamente en el primer arranque:
* **Usuario Administrador:** `admin@mareadulce.com` (o el especificado en `ADMIN_EMAIL`) con rol `administrador`.
* **6 Categorías:** `Tortas y pasteles`, `Cupcakes`, `Galletas artesanales`, `Postres individuales`, `De temporada`, `Pedidos personalizados`.
* **12 Productos Oficiales:** Con descripciones artesanales, alérgenos declarados, porciones, stock inicial y precios exactos en COP:
  1. Torta de vainilla y frutos rojos (12 porciones) — `$ 98.000` (Destacado)
  2. Torta tres leches artesanal (12 porciones) — `$ 85.000` (Popular)
  3. Torta de chocolate intenso (12 porciones) — `$ 92.000`
  4. Cheesecake de maracuyá (10 porciones) — `$ 78.000` (Nuevo)
  5. Caja de 6 cupcakes surtidos — `$ 36.000` (Popular)
  6. Cupcake red velvet individual — `$ 7.500`
  7. Galletas de mantequilla decoradas (12) — `$ 42.000`
  8. Galletas con chips de chocolate (6) — `$ 24.000` (Bajo stock: 3 unidades)
  9. Brownie con arequipe artesanal — `$ 9.500`
  10. Tartaleta de limón merengada — `$ 11.000` (Agotado: 0 unidades)
  11. Vaso de tiramisú tradicional — `$ 12.500`
  12. Torta navideña de frutos secos — `$ 110.000` (De temporada)

---

## 6. Endpoints de la API y Sondas de Kubernetes

| Método | Ruta | Autenticación | Propósito |
|---|---|---|---|
| `GET` | `/healthz` | Pública | Liveness Probe de Kubernetes. |
| `GET` | `/ready` | Pública | Readiness Probe (valida conexión activa a SQLite). |
| `GET` | `/api/v1/version` | Pública | Metadatos de versión y estrategia `Recreate`. |
| `GET` | `/metrics` | Pública | Scrape de Prometheus (tráfico, latencia y métricas de negocio). |
| `POST`| `/api/v1/auth/register`| Pública | Registro de nuevos clientes. |
| `POST`| `/api/v1/auth/login` | Pública | Autenticación y emisión de token JWT Bearer. |
| `GET` | `/api/v1/auth/me` | Bearer Token | Perfil del usuario autenticado. |
| `GET` | `/api/v1/categories` | Pública | Listado de categorías activas. |
| `POST`| `/api/v1/categories` | Admin | Creación de categorías. |
| `GET` | `/api/v1/products` | Pública | Catálogo con filtros de búsqueda, categoría y stock. |
| `GET` | `/api/v1/products/{id}`| Pública | Detalle completo de producto con alérgenos. |
| `POST`| `/api/v1/products` | Admin | Creación de productos en catálogo. |
| `PATCH`|`/api/v1/products/{id}/stock`| Admin | Ajuste rápido de inventario. |
| `POST`| `/api/v1/orders` | Opcional | Creación de pedido con `Idempotency-Key` y reserva de stock. |
| `GET` | `/api/v1/orders/{order_number}`| Pública | Consulta y seguimiento de pedido en vivo. |
| `GET` | `/api/v1/orders` | Bearer Token | Historial del cliente o listado total para Admin. |
| `PATCH`|`/api/v1/orders/{id}/status`| Admin | Cambio de estado de pedido validando transiciones. |
| `POST`| `/api/v1/custom-orders`| Pública | Envío de solicitud de torta personalizada. |
| `GET` | `/api/v1/admin/kpis` | Admin | KPIs de ventas del día, pedidos del mes y alertas. |
| `GET` | `/api/v1/admin/inventory`| Admin | Vista consolidada de inventario y estados de stock. |

---

## 7. Verificación de Calidad y Resultados de Pruebas (DoD)

Se ejecutó la suite de pruebas automatizadas en `app/tests/test_backend.py` validando la totalidad de los flujos:

```text
app/tests/test_backend.py::test_health_and_probes PASSED                 [ 12%]
app/tests/test_backend.py::test_metrics_endpoint PASSED                  [ 25%]
app/tests/test_backend.py::test_catalog_seeded_data PASSED               [ 37%]
app/tests/test_backend.py::test_auth_and_roles PASSED                    [ 50%]
app/tests/test_backend.py::test_order_creation_stock_deduction_and_idempotency PASSED [ 62%]
app/tests/test_backend.py::test_order_status_transitions_and_cancellation PASSED [ 75%]
app/tests/test_backend.py::test_insufficient_stock_error PASSED          [ 87%]
app/tests/test_backend.py::test_database_backup_and_integrity PASSED     [100%]

======================== 8 passed in 2.22s =========================
```

### Checklist de Definición de Terminado (DoD)
- [x] **Arquitectura implementada y entidades completas:** Módulos separados en `core`, `domain`, `infrastructure`, `repositories` y `routers`.
- [x] **CRUD de productos y categorías funcional:** Listado, búsqueda, creación, actualización y control de stock.
- [x] **Registro, inicio de sesión, roles y rutas protegidas:** Autenticación con `bcrypt` y JWT; rol `cliente` y `administrador`.
- [x] **Carrito y pedidos funcionando con transiciones válidas:** Máquina de estados estricta y reincorporación de stock al cancelar.
- [x] **Idempotencia de pedidos y control de inventario comprobados:** Cabecera `Idempotency-Key` y transacción atómica `BEGIN IMMEDIATE`.
- [x] **Persistencia y migraciones verificadas:** SQLite en modo WAL, verificación con `PRAGMA integrity_check` y respaldos automáticos con `.backup`.
- [x] **Seed del catálogo cargado:** 6 categorías y los 12 productos oficiales con precios enteros en COP.
- [x] **OpenAPI accesible; `/healthz`, `/ready` y `/metrics` funcionando:** Documentación interactiva en `/docs` e instrumentación en Prometheus.
- [x] **Pruebas unitarias, de integración y de procesos comerciales ejecutadas:** 8/8 pruebas automatizadas aprobadas sin fallos.
- [x] **Sin errores críticos conocidos:** Código verificado y libre de excepciones no controladas.
