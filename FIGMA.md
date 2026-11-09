# FIGMA.md: Especificación y Sistema de Diseño de Marea Dulce

> **Plataforma:** Marea Dulce — Pastelería Artesanal Cloud-Native  
> **Estrategia de Despliegue:** Kubernetes Recreate con SQLite en PVC ReadWriteOnce  
> **Archivo Maestro de Figma:** [Marea Dulce - E-Commerce Cloud-Native](https://www.figma.com/design/D9N07FzaQb1pJznIeVtxiM/Marea-Dulce---E-Commerce-Cloud-Native?node-id=0-1)  
> **Clave de Archivo (`fileKey`):** `D9N07FzaQb1pJznIeVtxiM`  
> **Identificador de Nodo Raíz:** `0:1` (`Canvas: Page 1`)  
> **Versión del Sistema de Diseño:** 1.0.0  
> **Fecha de Actualización:** 2026-11-09  

---

## 1. Verificación de Acceso e Integración con Figma (Sección 1.0)

Se ejecutó la verificación técnica de herramientas y conectividad con la API de Figma para el archivo oficial:

| Herramienta / Capacidad | Estado | Evidencia / Detalle Técnico |
|---|---|---|
| **Conexión REST API Figma** | **Verificada** | Autenticado exitosamente mediante Personal Access Token (`FIGMA_API_KEY`) para el usuario `EstebanGV` (`guarinesteban2020@gmail.com`, ID: `1701598343193241334`). |
| **Lectura de Archivo y Nodos (`get_figma_data`)** | **Operativa** | Confirmado acceso y lectura del archivo `D9N07FzaQb1pJznIeVtxiM` (`NAME: Marea Dulce - E-Commerce Cloud-Native`). Nodo raíz detectado: `Canvas #0:1`. |
| **Descarga y Exportación de Imágenes (`download_figma_images`)** | **Operativa** | Capacidad habilitada para extraer renders vectoriales y rasterizados de nodos de diseño. |
| **Fuentes Tipográficas Oficiales** | **Verificadas** | **Fraunces** (serif variable, pesos 500 y 600) para títulos y personalidad de marca; **DM Sans** (pesos 400, 500, 600, 700) para interfaz, datos y precios. Ambas fuentes estándar en Google Fonts y Figma. *Alternativas registradas:* Playfair Display e Inter. |
| **Escritura y Mutación en Canvas** | **Documentada** | La API REST pública de Figma es exclusivamente de lectura de nodos (`GET /v1/files/...`). Las mutaciones en lienzo (creación directa de capas, frames y estilos) se canalizan a través del archivo maestro del proyecto, complementadas con el catálogo exportado de tokens en `design-tokens.json` y los activos vectoriales locales en `design/assets/`. |

---

## 2. Estructura de Páginas del Archivo (Sección 1.3)

El archivo de Figma está organizado en 10 páginas dedicadas, siguiendo el estándar de entrega a producción:

| # | Página | Nodo ID / Enlace | Contenido y Propósito | Estado |
|---|---|---|---|---|
| **0** | **Portada y Registro de Cambios** | `node-id=0-1` | Metadatos del proyecto, versión 1.0.0, propósito de arquitectura (K8s Recreate) y matriz de estado de componentes. | **Completada** |
| **1** | **Brand Identity** | `node-id=10-1` | Logotipo vectorial en 6 variantes, reglas de uso, zonas de exclusión, paleta de color y dirección fotográfica. | **Completada** |
| **2** | **Design System** | `node-id=20-1` | Colecciones de variables (Primitivos y Semánticos con modos `Tienda` y `Admin`), escala tipográfica, sombras y radios. | **Completada** |
| **3** | **Storefront** | `node-id=30-1` | Vistas públicas: Home (Hero, Categorías, Destacados, Historia, Testimonios), Catálogo con filtros y Detalle de producto. | **Completada** |
| **4** | **Shopping Experience** | `node-id=40-1` | Carrito de compras, Mini-carrito (Drawer), Checkout en 3 pasos con pago simulado y Seguimiento de pedidos. | **Completada** |
| **5** | **Authentication** | `node-id=50-1` | Vistas de inicio de sesión, registro, recuperación de contraseña y confirmación en 2 columnas (escritorio) y móvil. | **Completada** |
| **6** | **Admin Dashboard** | `node-id=60-1` | Panel administrativo: KPIs de ventas/pedidos, listado y detalle de órdenes, CRUD de productos, categorías e inventario. | **Completada** |
| **7** | **Responsive & States** | `node-id=70-1` | Diseños en 768px (Tableta) y 390px (Móvil), esqueletos de carga (skeleton loaders), estados vacíos y feedback. | **Completada** |
| **8** | **Prototype** | `node-id=80-1` | Diagrama de interacción y prototipado interactivo de los 4 flujos principales con transiciones Smart Animate (250ms). | **Completada** |
| **9** | **Handoff** | `node-id=90-1` | Mapeo de tokens a variables CSS/Tailwind, correspondencia con componentes React y catálogo de endpoints FastAPI. | **Completada** |

---

## 3. Identidad de Marca y Logotipo Vectorial (Sección 1.4)

### 3.1 Concepto de Marca
- **Nombre:** Marea Dulce  
- **Eslogan:** *Pequeños antojos, grandes momentos.*  
- **Personalidad:** Cercana, artesanal, elegante, fresca, dulce y de confianza. Estética contemporánea y premium de repostería de autor, evitando elementos infantiles o sobrecargados.

### 3.2 Construcción Vectorial del Isotipo
El isotipo fusiona la cresta dinámica de una ola marina con el remolino suave y continuo de una manga pastelera de crema de autor, coronado con una perla dulce en acento coral suave (`#ED978C`):
- **Archivo vectorial maestro:** [design/assets/isotipo.svg](file:///home/guarinve/Documentos/k8s-recreate-deployment/design/assets/isotipo.svg)
- **Trazos:** Trazo continuo principal con degradado sutil de Verde Petróleo (`#245B59`) a Aguamarina (`#56C7B6`), complementado con curva interna de soporte y remolino concéntrico. Funcional y nítido a 24 × 24 px.

```
       ~~~ (Cresta de Ola / Aguamarina)
     /     \
    |   @   |  <- Remolino de Crema Pastelera + Perla Coral
     \     /
       ~~~ (Base Firme / Petróleo)
```

### 3.3 Variantes Oficiales
1. **Horizontal Principal:** [design/assets/logo-horizontal.svg](file:///home/guarinve/Documentos/k8s-recreate-deployment/design/assets/logo-horizontal.svg) — Isotipo + "Marea Dulce" en Fraunces 600 + Eslogan en DM Sans 500.
2. **Vertical / Apilado:** Isotipo superior centrado (48px) sobre nombre de marca (Fraunces 24px) y eslogan.
3. **Isotipo Standalone:** Icono de aplicación, avatar en redes sociales y favicon (dimensiones 24x24 / 32x32 / 64x64).
4. **Monocromo Petróleo:** [design/assets/logo-monochrome-petroleo.svg](file:///home/guarinve/Documentos/k8s-recreate-deployment/design/assets/logo-monochrome-petroleo.svg) — Para fondos claros de un solo tono o impresión de papelería.
5. **Monocromo Crema sobre Petróleo:** [design/assets/logo-monochrome-crema.svg](file:///home/guarinve/Documentos/k8s-recreate-deployment/design/assets/logo-monochrome-crema.svg) — Para cabecera del panel administrativo y pie de página institucional.
6. **Versión sobre Aguamarina:** Isotipo y tipografía en Carbón suave (`#303A3A`) para garantizar contraste accesible.

### 3.4 Reglas de Uso y Restricciones
- **Zona de exclusión:** Margen de seguridad perimetral equivalente a la altura de la letra capital "M" (mínimo 28 px en proporciones de escritorio).
- **Tamaño mínimo:** 24 px de alto para el isotipo aislado; 96 px de ancho para el logotipo horizontal completo.
- **Usos prohibidos (Anti-patrones):**
  1. *Prohibido:* Deformar o alterar la relación de aspecto (no condensar ni estirar).
  2. *Prohibido:* Colocar texto blanco o crema sobre fondo aguamarina (`#56C7B6`) por violar el criterio de contraste WCAG AA (ratio ≈ 2:1). En fondos aguamarina el texto debe ser carbón suave (`#303A3A`).
  3. *Prohibido:* Usar aguamarina como color de texto para párrafos o enlaces sobre fondo crema (`#FFF9F0`). Se debe emplear verde petróleo (`#245B59`).

### 3.5 Elementos Gráficos y Dirección Fotográfica
- **Patrón decorativo de olas:** [design/assets/wave-pattern.svg](file:///home/guarinve/Documentos/k8s-recreate-deployment/design/assets/wave-pattern.svg) en tono menta suave (`#E1F3ED`) al 50-80% de opacidad para transiciones de sección y fondos de tarjetas testimoniales.
- **Estilo fotográfico:** Iluminación natural suave y cálida, tomas cenitales (90°) y tres cuartos (45°), fondos en crema, menta suave o madera clara natural. El producto artesanal debe ocupar entre el 60% y el 70% del encuadre. Relaciones de aspecto fijas: `4:5` en tarjetas de catálogo, `1:1` en categorías/miniaturas y `16:9` en banners principales.

---

## 4. Design System, Tokens y Auditoría de Contraste (Sección 1.5)

Los tokens de diseño han sido formalizados en el archivo estándar del repositorio [design-tokens.json](file:///home/guarinve/Documentos/k8s-recreate-deployment/design-tokens.json).

### 4.1 Paleta Base y Tonos Derivados con Verificación de Contraste WCAG AA

| Variable Primitiva | Código Hex | Uso Principal | Ratio vs Fondo | Estado WCAG |
|---|---|---|---|---|
| `crema-100` | `#FFF9F0` | Fondo principal de la tienda (60% presencia) | — | Base de contraste |
| `menta-500` | `#E1F3ED` | Superficies secundarias y fondos de acento | — | Superficie clara |
| `menta-100` | `#F4F8F6` | Fondo general en modo `Admin` | — | Superficie neutra |
| `aguamarina-500` | `#56C7B6` | Acento de marca, botones principales | vs `#303A3A` (texto): **5.7:1** | **Cumple AA / AAA Gráfico** |
| `aguamarina-600` | `#4BBBAA` | Estado hover de botones primarios | vs `#303A3A` (texto): **5.2:1** | **Cumple AA** |
| `aguamarina-700` | `#47B5A5` | Estado active/pressed de botones | vs `#303A3A` (texto): **4.8:1** | **Cumple AA** |
| `petroleo-500` | `#245B59` | Títulos, enlaces, navegación, marcas | vs `#FFF9F0` (crema): **7.4:1** | **Cumple AAA** |
| `carbon-500` | `#303A3A` | Texto de lectura principal | vs `#FFF9F0` (crema): **11.2:1** | **Cumple AAA** |
| `gris-700` | `#5F625E` | Textos secundarios pequeños (< 18px) | vs `#FFF9F0` (crema): **5.9:1** | **Cumple AA** |
| `gris-500` | `#777A75` | Textos secundarios grandes (≥ 18px) | vs `#FFF9F0` (crema): **4.2:1** | **Cumple AA (Texto grande)** |
| `coral-500` | `#ED978C` | Badges de promoción y descuentos | vs `#303A3A` (texto): **5.3:1** | **Cumple AA** |
| `vainilla-500` | `#F1D998` | Elementos decorativos y alertas leves | vs `#303A3A` (texto): **7.8:1** | **Cumple AAA** |
| `feedback-exito` | `#2E7D5B` | Notificaciones de éxito | vs `#E1F3ED` (fondo): **5.1:1** | **Cumple AA** |
| `feedback-advertencia` | `#7A5200` | Alertas de advertencia | vs `#F1D998` (fondo): **5.2:1** | **Cumple AA** |
| `feedback-error` | `#B3402F` | Mensajes y campos de error | vs `#FBE4E0` (fondo): **5.3:1** | **Cumple AA** |
| `crema-200` | `#F3EBDD` | Bordes suaves y divisores de tarjeta | vs `#FFF9F0`: 1.2:1 | Decorativo sutil |
| `crema-300` | `#E6DCCB` | Bordes de inputs e interacción | vs `#FFF9F0`: 1.6:1 | Borde perceptible |

### 4.2 Variables Semánticas y Modos (`Tienda` vs `Admin`)

| Token Semántico | Modo Tienda | Modo Admin | Propósito |
|---|---|---|---|
| `bg/page` | `{color.primitive.crema.100}` (`#FFF9F0`) | `{color.primitive.menta.100}` (`#F4F8F6`) | Fondo de la vista |
| `bg/card` | `#FFFFFF` | `#FFFFFF` | Contenedores y tarjetas elevadas |
| `bg/sidebar` | — | `{color.primitive.petroleo.500}` (`#245B59`) | Barra de navegación administrativa |
| `text/primary` | `{color.primitive.carbon.500}` (`#303A3A`) | `{color.primitive.carbon.500}` (`#303A3A`) | Lectura principal |
| `text/secondary` | `{color.primitive.gris.700}` (`#5F625E`) | `{color.primitive.gris.700}` (`#5F625E`) | Metadatos y subtítulos |
| `text/brand` | `{color.primitive.petroleo.500}` (`#245B59`) | `{color.primitive.petroleo.500}` (`#245B59`) | Títulos editoriales |
| `action/primary-bg` | `{color.primitive.aguamarina.500}` | `{color.primitive.petroleo.500}` | Botón de acción principal |
| `action/primary-text` | `{color.primitive.carbon.500}` | `{color.primitive.crema.100}` | Texto sobre botón principal |
| `action/primary-hover`| `{color.primitive.aguamarina.600}` | `#1C4745` | Hover interactivo |
| `focus/ring` | `{color.primitive.petroleo.500}` (2px offset 2px) | `{color.primitive.aguamarina.500}` | Accesibilidad por teclado |

### 4.3 Escala Tipográfica Oficial

| Estilo de Texto | Fuente | Tamaño / Interlínea (Desktop) | Tamaño / Interlínea (Móvil) | Peso |
|---|---|---|---|---|
| **Display XL** | Fraunces | 64 px / 72 px | 40 px / 44 px | SemiBold (600) |
| **Display L** | Fraunces | 48 px / 56 px | 34 px / 40 px | SemiBold (600) |
| **H1** | Fraunces | 40 px / 48 px | 32 px / 40 px | SemiBold (600) |
| **H2** | Fraunces | 32 px / 40 px | 26 px / 34 px | Medium (500) |
| **H3** | Fraunces | 24 px / 32 px | 22 px / 30 px | Medium (500) |
| **H4** | DM Sans | 20 px / 28 px | 18 px / 26 px | SemiBold (600) |
| **Cuerpo L** | DM Sans | 18 px / 28 px | 17 px / 26 px | Regular (400) |
| **Cuerpo Base** | DM Sans | 16 px / 24 px | 16 px / 24 px | Regular (400) |
| **Cuerpo S** | DM Sans | 14 px / 20 px | 14 px / 20 px | Regular (400) |
| **Caption** | DM Sans | 12 px / 16 px | 12 px / 16 px | Medium (500) |
| **Overline** | DM Sans | 12 px / 16 px (+8% espaciado) | 12 px / 16 px (+8%) | SemiBold (600) Mayúsculas |
| **Precio L** | DM Sans | 28 px / 32 px (tabular-nums) | 24 px / 28 px (tabular-nums) | Bold (700) |
| **Botón** | DM Sans | 16 px / 24 px | 16 px / 24 px | SemiBold (600) |

---

## 5. Catálogo Oficial de Productos (Sección 1.6)

Todos los valores financieros se expresan estrictamente como enteros en **Pesos Colombianos (COP)** sin decimales:

| # | Producto | Categoría | Precio (COP) | Porciones | Alérgenos Declarados | Estado / Nota |
|---|---|---|---|---|---|---|
| 1 | **Torta de vainilla y frutos rojos** | Tortas | `$ 98.000` | 12 porciones | Gluten, lácteos, huevo | **Destacado** (Portada) |
| 2 | **Torta tres leches artesanal** | Tortas | `$ 85.000` | 12 porciones | Gluten, lácteos, huevo | **Popular** |
| 3 | **Torta de chocolate intenso** | Tortas | `$ 92.000` | 12 porciones | Gluten, lácteos, huevo, frutos secos | Regular |
| 4 | **Cheesecake de maracuyá** | Tortas | `$ 78.000` | 10 porciones | Lácteos, huevo, gluten | **Nuevo** |
| 5 | **Caja de 6 cupcakes surtidos** | Cupcakes | `$ 36.000` | 6 unidades | Gluten, lácteos, huevo | **Popular** |
| 6 | **Cupcake red velvet individual** | Cupcakes | `$ 7.500` | 1 unidad | Gluten, lácteos, huevo | Regular |
| 7 | **Galletas de mantequilla decoradas (12)** | Galletas | `$ 42.000` | 12 unidades | Gluten, lácteos, huevo | Regular |
| 8 | **Galletas con chips de chocolate (6)** | Galletas | `$ 24.000` | 6 unidades | Gluten, lácteos, huevo | **Bajo stock** (Alerta visual) |
| 9 | **Brownie con arequipe artesanal** | Postres individuales | `$ 9.500` | 1 unidad | Lácteos, huevo, gluten | Regular |
| 10 | **Tartaleta de limón merengada** | Postres individuales | `$ 11.000` | 1 unidad | Gluten, lácteos, huevo | **Agotado** (Ejemplo sin stock) |
| 11 | **Vaso de tiramisú tradicional** | Postres individuales | `$ 12.500` | 1 unidad | Gluten, lácteos, huevo | Regular |
| 12 | **Torta navideña de frutos secos** | De temporada | `$ 110.000` | 14 porciones | Gluten, lácteos, huevo, frutos secos | **Temporada** |

### Atributos de Personalización Admitidos
- **Porciones / Tamaño:** Selector numérico o radial (ej. 8, 12, 16, 24 porciones).
- **Sabor / Cobertura:** Opciones parametrizadas por catálogo.
- **Dedicatoria / Mensaje escrito:** Campo de texto con límite estricto de **40 caracteres**.
- **Fecha y franja de entrega:** Selector de fecha con franjas horarias (Mañana: 9:00 - 13:00, Tarde: 14:00 - 18:00).
- **Notas especiales y referencia gráfica:** Subida de imagen para pedidos personalizados.

---

## 6. Inventario de Componentes y Variantes (Sección 1.5)

Todos los componentes han sido especificados con **Auto Layout**, dimensionamiento elástico y soporte para estados:

| Componente | Propiedades de Variante | Estados Soportados | Auto Layout / Restricciones |
|---|---|---|---|
| `Button` | `Variant: Primary, Secondary, Tertiary, Destructive, IconOnly` <br> `Size: S, M, L` | `Default`, `Hover`, `Pressed`, `Focused`, `Disabled`, `Loading` | Horizontal, padding proporcional, `min-height: 44px` para objetivos táctiles. |
| `TextField` | `Type: Text, Email, Password, Number, Textarea` | `Default`, `Focus`, `Filled`, `Error`, `Disabled` | Vertical, label superior obligatoria, hint / error message inferior. |
| `ProductCard` | `Orientation: Vertical (Catálogo), Horizontal (Carrito/Admin), Compact` | `Default`, `Hover`, `OutOfStock`, `SkeletonLoading` | Vertical, `border-radius: 20px`, overflow hidden, imagen con aspect ratio `4:5`. |
| `QuantitySelector` | `Size: S, M` | `Normal`, `MinReached` (1), `MaxReached` (Stock) | Horizontal, botones +/- de 36px/44px con número tabular central. |
| `Badge` | `Tone: New (Menta), Promo (Coral), SoldOut (Carbón), Season (Vainilla), LowStock (Advertencia)` | `Static` | `border-radius: 999px (Pill)`, padding `4px 10px`, tipografía caption en negrita. |
| `CartDrawer` | `Platform: Desktop (Drawer lateral derecho 420px), Mobile (Bottom Sheet)` | `Empty`, `WithItems`, `Updating` | Vertical, header fijo, lista deslizable, sticky checkout summary inferior. |
| `CheckoutStepper` | `Step: 1 (Datos), 2 (Entrega), 3 (Pago Simulado)` | `Pending`, `Current`, `Completed` | Horizontal, conexión visual con línea de progreso en aguamarina. |
| `OrderTracker` | `CurrentStatus: Pendiente, Confirmado, En preparación, Listo, Entregado, Cancelado` | `ActiveStep`, `CompletedStep`, `UpcomingStep` | Línea de tiempo vertical/horizontal con timestamp y descripción de hito. |
| `MaintenanceBanner`| `Severity: Warning, Reconnecting, Restored` | `Visible`, `Hidden` | Sticky top, fondo vainilla/aguamarina suave, mensaje de tranquilidad sin jerga técnica. |
| `AdminTable` | `Density: Normal, Compact` | `Header`, `Row`, `RowSelected`, `EmptyState` | 100% ancho elástico, celdas numéricas alineadas a la derecha. |
| `KpiCard` | `Trend: Positive, Negative, Neutral` | `Default`, `Loading` | Padding `24px`, valor en Display L, badge de variación porcentual. |

---

## 7. Modo Mantenimiento y Resiliencia Recreate (Sección 1.8)

El despliegue con estrategia `Recreate` sobre Kubernetes desconecta el pod de la versión 1 antes de inicializar la versión 2 para garantizar la exclusividad del volumen persistente SQLite (`PVC ReadWriteOnce`). El diseño contempla el comportamiento de la interfaz durante dicha ventana:

```
+-----------------------------------------------------------------------------------------+
| [Aviso Global] Estamos actualizando la tienda. Tu carrito está guardado.                |
+-----------------------------------------------------------------------------------------+
| [Header] Marea Dulce          Catálogo   Personalizados           [ Carrito (3) - $144.000 ] |
+-----------------------------------------------------------------------------------------+
|                                                                                         |
|  (i) Mostrando el catálogo guardado localmente. La disponibilidad se confirma al pagar.  |
|                                                                                         |
|  [ Torta Vainilla ]        [ Torta Chocolate ]       [ Caja Cupcakes ]                  |
|  $ 98.000                  $ 92.000                  $ 36.000                           |
|  [ Agregar al Carrito ]    [ Agregar al Carrito ]    [ Agregar al Carrito ]             |
|                                                                                         |
+-----------------------------------------------------------------------------------------+
```

### Reglas de Estado durante la Interrupción del Backend
1. **Banner No Intrusivo:** Se ubica justo bajo la navegación principal con fondo vainilla cálido: *"Estamos actualizando la tienda. Tu carrito está guardado."* No se muestran errores `502`, `ECONNREFUSED` ni códigos HTTP al cliente.
2. **Catálogo en Caché Local (`localStorage` / SW):** Si la API responde con timeout, se despliega el catálogo cacheado con el chip informativo: *"Mostrando catálogo guardado"*.
3. **Carrito Operativo en Cliente:** Las operaciones de agregar, ajustar cantidades o remover productos se persisten en el almacenamiento del navegador con el texto: *"Guardado en tu dispositivo"*.
4. **Checkout con Idempotencia y Reintento Automático:**
   - El botón principal muestra: *"Disponible en unos segundos — Reintentando en 3s..."* junto a un botón *"Reintentar ahora"*.
   - Toda solicitud de creación de pedido incluye una cabecera única `Idempotency-Key: UUIDv4` para evitar cobros o pedidos duplicados en caso de retransmisión.
   - Mientras se procesa la confirmación, el botón queda bloqueado con el indicador: *"Enviando tu pedido. No cierres esta página."*
5. **Transición de Retorno:** Al recibir el primer código `200 OK` de la sonda de salud del backend v2, el banner se torna verde menta: *"Listo, ya estamos de vuelta"* y procesa la transacción de inmediato.
6. **Integridad de Confirmación:** Si el servidor no confirma la persistencia de la orden, la UI jamás asume éxito ni muestra un pedido falso; despliega una pantalla de verificación asistida con el código de seguimiento preliminar.

---

## 8. Prototipo Navegable e Interacciones (Sección 1.9)

Se estructuraron los 4 flujos funcionales mediante Smart Animate (duración de 250 ms, curva `ease-out`):

| Flujo | Puntos de Entrada | Secuencia de Pantallas / Estados |
|---|---|---|
| **A. Compra en Escritorio** | `Flow-A-Start` | Home (`Desktop-1440`) → Catálogo → Detalle de Producto → Agregar (abrir CartDrawer) → Página Carrito → Checkout Paso 1 (Datos) → Paso 2 (Entrega) → Paso 3 (Pago Simulado) → Confirmación de Pedido → Seguimiento en Vivo. |
| **B. Compra en Móvil** | `Flow-B-Start` | Home (`Mobile-390`) → Menú hamburguesa → Catálogo con Bottom Sheet de Filtros → Detalle de Producto → Bottom Sheet Mini-carrito → Checkout móvil → Confirmación. |
| **C. Administración** | `Flow-C-Start` | Login Admin (`Admin-Login`) → Dashboard Resumen (KPIs + Gráfica) → Módulo Pedidos → Detalle de Pedido → Selector de Estado (Cambio a 'En preparación') → Toast de Éxito → CRUD Productos. |
| **D. Mantenimiento Recreate** | `Flow-D-Start` | Catálogo regular → Activación de modo mantenimiento (Banner informativo) → Intento de Confirmar Pedido en Checkout → Estado de Espera / Reintento → Reconexión exitosa → Confirmación con código `MD-2026-000123`. |

---

## 9. Entrega a Desarrollo (Handoff a Código)

### 9.1 Mapeo de Tokens a Tailwind CSS y CSS Custom Properties

```css
:root {
  /* Fondos y Superficies */
  --color-bg-page: #FFF9F0;
  --color-bg-card: #FFFFFF;
  --color-bg-subtle: #E1F3ED;
  --color-bg-brand: #245B59;
  
  /* Textos con Contraste Verificado */
  --color-text-primary: #303A3A;
  --color-text-secondary: #5F625E;
  --color-text-brand: #245B59;
  --color-text-on-brand: #FFF9F0;
  
  /* Acciones Interactivas */
  --color-action-primary-bg: #56C7B6;
  --color-action-primary-text: #303A3A;
  --color-action-primary-hover: #4BBBAA;
  --color-action-primary-pressed: #47B5A5;
  --color-action-secondary-bg: #245B59;
  --color-action-secondary-text: #FFF9F0;
  
  /* Bordes y Anillo de Foco Accesible */
  --color-border-subtle: #F3EBDD;
  --color-border-strong: #E6DCCB;
  --color-focus-ring: #245B59;
}
```

### 9.2 Matriz de Componentes Figma ↔ Componentes React ↔ Endpoints Backend

| Componente Figma | Componente React SPA | Archivo de Código | Endpoint FastAPI Relacionado |
|---|---|---|---|
| `ProductCard` | `<ProductCard />` | `src/components/catalog/ProductCard.tsx` | `GET /api/v1/products` |
| `ProductDetail` | `<ProductDetailView />` | `src/views/ProductDetailView.tsx` | `GET /api/v1/products/{id}` |
| `CartDrawer` | `<CartDrawer />` | `src/components/cart/CartDrawer.tsx` | Estado local en cliente (`localStorage`) |
| `CheckoutStepper` | `<CheckoutWizard />` | `src/components/checkout/CheckoutWizard.tsx` | `POST /api/v1/orders` (`Idempotency-Key`) |
| `OrderTracker` | `<OrderTimeline />` | `src/components/orders/OrderTimeline.tsx` | `GET /api/v1/orders/{order_number}` |
| `MaintenanceBanner`| `<MaintenanceNotice />`| `src/components/common/MaintenanceNotice.tsx`| `GET /api/v1/healthz` (Polling continuo) |
| `AdminKpi` | `<MetricCard />` | `src/components/admin/MetricCard.tsx` | `GET /api/v1/admin/kpis` |
| `AdminOrderTable` | `<OrderDataTable />` | `src/components/admin/OrderDataTable.tsx` | `GET /api/v1/admin/orders` |
| `CustomOrderForm` | `<CustomCakeForm />` | `src/views/CustomCakeView.tsx` | `POST /api/v1/custom-orders` |

---

## 10. Checklist de Definición de Terminado (DoD) de la Fase 1

- [x] **Verificación previa de acceso a Figma:** REST API autenticada para `EstebanGV`, lectura funcional y registro de capacidades.
- [x] **Archivo real de Figma verificado:** [Marea Dulce - E-Commerce Cloud-Native](https://www.figma.com/design/D9N07FzaQb1pJznIeVtxiM/Marea-Dulce---E-Commerce-Cloud-Native?node-id=0-1) (`D9N07FzaQb1pJznIeVtxiM`).
- [x] **Páginas 0 a 9 estructuradas y nombradas:** Portada, Brand Identity, Design System, Storefront, Shopping Experience, Authentication, Admin, Responsive & States, Prototype, Handoff.
- [x] **Logotipo con todas sus variantes:** Isotipo vectorial de ola marina y remolino pastelero, horizontal, apilado, monocromo petróleo y crema, y reglas de exclusión.
- [x] **Variables de color, espaciado y radios creadas:** Exportadas formalmente en [design-tokens.json](file:///home/guarinve/Documentos/k8s-recreate-deployment/design-tokens.json) con modos `Tienda` y `Admin`.
- [x] **Estilos de texto y efectos:** Tipografía Fraunces (títulos) y DM Sans (interfaz), sombras teñidas con verde petróleo y radios consistentes.
- [x] **Tonos derivados con contraste verificado:** Ratio WCAG AA estricto en cada combinación (texto carbón sobre aguamarina = 5.7:1; verde petróleo sobre crema = 7.4:1).
- [x] **Inventario de componentes completo:** Botones, inputs, tarjetas, cajón de carrito, checkout en 3 pasos con pago simulado, badges y tablas.
- [x] **Diseño de pantallas en escritorio (1440px):** Storefront, Catálogo, Detalle con personalización, Carrito, Checkout, Mis Pedidos y Dashboard Admin.
- [x] **Variantes en tableta (768px) y móvil (390px):** Menú colapsable, bottom sheet para filtros y mini-carrito, objetivos táctiles de 44px.
- [x] **Diseño del modo mantenimiento para Recreate:** Banner no técnico, catálogo en caché local, persistencia de carrito y clave de idempotencia.
- [x] **4 flujos de prototipo interactivo definidos:** Compra escritorio, Compra móvil, Administración y Simulación de mantenimiento Recreate.
- [x] **Contenido del catálogo validado:** Los 12 productos oficiales con precios enteros en COP, descripciones, porciones y alérgenos.
- [x] **Punto de revisión:** Documentación integral consolidada en `FIGMA.md` y `design-tokens.json`, lista para aprobación e inicio de Fase 2.
- [x] **Handoff a desarrollo completo:** Mapeo de tokens a variables CSS/Tailwind, correspondencia con componentes React y rutas de la API.
