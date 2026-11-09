# FRONTEND.md: Implementación y Fidelidad Visual del Frontend de Marea Dulce

> **Módulo:** Frontend SPA  
> **Tecnologías:** React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons  
> **Servidor Web:** NGINX 1.25 Alpine (Contenedor decoupled)  
> **Integración:** Sistema de tokens de diseño (`design-tokens.json`) y API REST FastAPI  
> **Versión:** 1.0.0  
> **Fecha de Publicación:** 2026-11-09  

---

## 1. Método de Fidelidad y Vinculación con Figma

La interfaz web ha sido implementada tomando como fuente estricta de verdad el archivo maestro de Figma [Marea Dulce - E-Commerce Cloud-Native](https://www.figma.com/design/D9N07FzaQb1pJznIeVtxiM/Marea-Dulce---E-Commerce-Cloud-Native?node-id=0-1) y los tokens exportados en `design-tokens.json`:

1. **Tokens Semánticos Directos:** Las clases de Tailwind CSS (`bg-crema-100`, `text-petroleo-500`, `bg-aguamarina-500`, `text-carbon-500`, `bg-coral-500`, etc.) derivan exactamente de las variables de Figma sin colores "hardcodeados" en hexadecimal.
2. **Tipografía Dual:** Encabezados editoriales renderizados con **Fraunces** (pesos 500 y 600) e interfaz/precios con **DM Sans** (tabular-nums para precios exactos sin decimales).
3. **Consistencia de Radios y Sombras:** Tarjetas de producto con radio `lg` (20px), botones y campos con `md` (12px), badges con `pill` (9999px) y sombras teñidas con Verde Petróleo (`rgba(36, 91, 89, 0.08)`).

---

## 2. Vistas y Alcance Funcional Implementado

### 2.1 Storefront Público
* **Landing / Home (`/`):**
  * **Hero Section:** Titular *"Pequeños antojos, grandes momentos."*, subtítulo con propuesta de valor, botones *"Ver el catálogo"* y *"Pedir una torta personalizada"*, y fotografía principal con tarjeta flotante de producto.
  * **Categorías:** 6 accesos directos con isotipo vectorial (`Tortas`, `Cupcakes`, `Galletas`, `Postres individuales`, `De temporada`, `Personalizados`).
  * **Destacados:** Grilla de 4 tarjetas de productos más vendidos.
  * **Banda Promocional:** Franja en Coral suave (`#ED978C`) con texto Carbón (`#303A3A`) cumpliendo contraste AA (5.3:1).
  * **Nuestra Historia:** Sección con ilustración de ondas marinas en menta suave y 3 pilares de valor (100% Artesanal, Ingredientes Puros, Frescura Diaria).
  * **Testimonios:** 3 reseñas de clientes reales.
  * **Pie de Página:** Enlaces, horarios, redes y aviso legal: *"Tienda de demostración. Los pagos son simulados."*

* **Catálogo Completo (`/catalogo`):**
  * Búsqueda en tiempo real por texto en nombre y descripción.
  * Píldoras de filtrado por categoría y checkbox para "Solo disponibles".
  * Selector de ordenamiento (Destacados, Precio: menor a mayor, Precio: mayor a menor).
  * Grilla adaptable: 4 columnas en escritorio (1440px), 3 columnas en tableta (768px) y 2 columnas en móvil (390px).

* **Detalle de Producto (`/producto/:slug`):**
  * Galería con fotografía en encuadre 4:5 y badge de estado.
  * Rendimiento en porciones y tiempo de horneado en horas.
  * Chips de alérgenos declarados (gluten, lácteos, huevo, frutos secos).
  * **Personalización en vivo:** Campo de dedicatoria en chocolate con límite interactivo estricto de **40 caracteres**.
  * Selector de cantidad con tope máximo según existencias en inventario.
  * Consejos de conservación y almacenamiento.

* **Canasta / Carrito (Slide-over Drawer y Página):**
  * Desplegable lateral derecho en escritorio y hoja inferior en móvil.
  * Lista de ítems con imagen, subtotal en COP y dedicatoria personalizada.
  * Controles de cantidad (+ / -) y eliminación rápida.
  * Persistencia automática en el almacenamiento local del navegador (`localStorage`).

* **Checkout en 3 Pasos (`/checkout`):**
  * **Paso 1 (Tus Datos):** Nombre, correo electrónico y teléfono de contacto.
  * **Paso 2 (Entrega):** Selección entre *Envío a Domicilio* (con dirección) o *Recogida en Tienda*, fecha programada y franja horaria.
  * **Paso 3 (Confirmación y Pago):** Etiqueta destacada **"Pago Simulado (Modo Demostración)"**, sin solicitar datos de tarjeta bancaria real.
  * Resumen lateral con desglose de ítems, subtotal y total siempre visible.

* **Confirmación de Compra (`/confirmacion/:orderNumber`):**
  * Mensaje de agradecimiento y código de pedido legible `MD-AAAA-NNNNNN`.
  * Detalle de productos y entrega.
  * Botón directo hacia el seguimiento en vivo.

* **Seguimiento de Pedido en Vivo (`/seguimiento`):**
  * Consulta por código alfanumérico.
  * Línea de tiempo interactiva con los 5 estados progresivos (`PENDIENTE` $\rightarrow$ `CONFIRMADO` $\rightarrow$ `EN_PREPARACION` $\rightarrow$ `LISTO` $\rightarrow$ `ENTREGADO`) o alerta roja si fue cancelado.

* **Tortas Personalizadas (`/personalizados`):** Formulario de cotización con porciones, fecha requerida y descripción temática.
* **Autenticación (`/login`):** Interfaz en dos columnas con ilustración de olas en escritorio y formulario con pestañas para Iniciar Sesión y Crear Cuenta.

---

### 2.2 Panel Administrativo (`/admin`)
* **Barra Lateral en Verde Petróleo (`#245B59`):** Acceso rápido con íconos Lucide.
* **Barra Superior con Telemetría en Vivo:** Indicador en tiempo real del estado de conexión del backend: *"Backend Conectado"* (verde menta) o *"Recreate Rollout en Curso"* (aviso naranja con animación).
* **Resumen y KPIs:** Ventas del día en COP, pedidos pendientes, pedidos del mes y alertas de stock bajo.
* **Gestión de Pedidos (`/admin/pedidos`):** Filtro por estado y selector que restringe los cambios de estado **únicamente a las transiciones válidas de negocio**.
* **Control de Inventario (`/admin/inventario`):** Tabla con edición rápida en línea de existencias para evitar bloqueos y prevenir sobreventas.
* **Catálogo Administrativo (`/admin/productos`):** Vista de productos con badges e indicadores de publicación.

---

## 3. Modo Resiliencia Recreate (Sección 1.8)

Durante el corte temporal de servicio provocado por el despliegue `Recreate` en Kubernetes (ventana donde el pod v1 muere y el pod v2 inicializa la migración de SQLite), la tienda opera en modo alta disponibilidad en cliente:

1. **Detección Automática:** Sondeo en segundo plano a `/healthz` cada 4 segundos sin congelar la interfaz.
2. **Banner Informativo Tranquilo:** Se despliega un aviso no intrusivo en tono vainilla cálido:  
   > *«Estamos actualizando la tienda. Tu carrito está guardado en tu dispositivo. (Reintentando en 3s...) [Reintentar ahora]»*  
   Nunca se despliegan mensajes de error crudos como `Failed to fetch`, `502 Bad Gateway` ni trazas de excepción.
3. **Catálogo desde Caché Local:** Si la API no responde, los productos y categorías se sirven desde la copia sincronizada en `localStorage` con el distintivo: *"Mostrando catálogo guardado en tu dispositivo"*.
4. **Checkout Protegido con Idempotencia:**
   * El botón principal pasa a estado de espera con cuenta regresiva.
   * La solicitud viaja con la cabecera `Idempotency-Key: UUIDv4`.
   * Mientras se envía, el botón se bloquea con el mensaje: *"Enviando tu pedido. No cierres esta página..."* para evitar duplicidades ante demoras de red.
5. **Restauración Transparente:** En cuanto el backend v2 responde `200 OK`, el banner se torna verde menta (*"¡Listo, ya estamos de vuelta!"*) y procesa automáticamente la transacción pendiente.

---

## 4. Adaptabilidad Responsiva (Breakpoints)

| Vista / Componente | Escritorio (1440px) | Tableta (768px) | Móvil (390px) |
|---|---|---|---|
| **Navegación** | Menú horizontal completo + perfil | Menú horizontal compacto | Menú hamburguesa colapsable táctil |
| **Grilla de Catálogo** | 4 columnas con espaciado 24px | 3 columnas | 2 columnas con tipografía ajustada |
| **Canasta / Carrito** | Drawer lateral derecho (420px) | Drawer lateral derecho | Bottom Sheet táctil deslizable |
| **Checkout** | 2 columnas (Formulario + Resumen Sticky) | 1 columna con resumen plegable | 1 columna paso a paso |
| **Autenticación** | 2 columnas (Ilustración olas + Formulario) | 1 columna centrada | 1 columna optimizada para teclado |
| **Panel Admin** | Sidebar fija de 256px + Contenido | Sidebar colapsable superior | Navegación vertical compacta |

---

## 5. Accesibilidad y Cumplimiento WCAG AA

* **Contraste de Color Verificado:**
  * Texto carbón suave (`#303A3A`) sobre botón aguamarina (`#56C7B6`): **5.7:1** (Cumple AA).
  * Títulos y enlaces verde petróleo (`#245B59`) sobre fondo crema (`#FFF9F0`): **7.4:1** (Cumple AAA).
  * Texto secundario gris-700 (`#5F625E`) sobre fondo crema: **5.9:1** (Cumple AA).
  * Prohibición absoluta de texto blanco o crema sobre aguamarina.
* **Objetivos Táctiles:** Todos los botones, enlaces interactivos y selectores tienen dimensiones mínimas de **44 × 44 px**.
* **Navegación por Teclado:** Anillos de foco visibles (`focus:ring-2 focus:ring-petroleo-500`) en todos los campos, enlaces y botones.

---

## 6. Checklist de Definición de Terminado (DoD) de la Fase 3

- [x] **Todas las pantallas implementadas a partir de Figma:** Landing, Catálogo, Detalle, Canasta, Checkout 3 pasos, Confirmación, Seguimiento, Login y Dashboard Admin.
- [x] **Tokens tomados de `design-tokens.json`:** Paleta semántica, tipografía Fraunces/DM Sans, radios y sombras teñidas en petróleo.
- [x] **Conexión real con el Backend FastAPI:** Catálogo, detalle, filtros, checkout transaccional, órdenes y panel admin consumen endpoints vivos.
- [x] **Autenticación y rutas protegidas funcionando:** JWT Bearer almacenado de forma segura y validación de rol `administrador`.
- [x] **Dashboard administrativo funcional:** KPIs en tiempo real, cambio de estado de órdenes y control rápido de inventario.
- [x] **Modo mantenimiento y resiliencia Recreate implementado:** Banner amigable, reintentos exponenciales, catálogo en caché y carrito persistente.
- [x] **Idempotencia y prevención de pedidos duplicados:** Clave `Idempotency-Key: UUIDv4` en checkout y bloqueo durante el envío.
- [x] **Diseño responsivo validado en 390px, 768px y 1440px:** Layouts fluidos y sin desbordes horizontales.
- [x] **Compilación y verificación sin errores de TypeScript:** `npm run build` ejecutado exitosamente con Vite (cero errores).
- [x] **Empaquetado para contenedor NGINX:** `frontend/Dockerfile` multi-stage y `frontend/nginx.conf` listos para la Fase 4.
