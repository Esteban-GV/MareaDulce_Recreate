import { Product, Category, Order, KpiSummary } from '../types';

const API_BASE = '/api/v1';

// Generador de clave de idempotencia UUID v4
export function generateIdempotencyKey(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'idem-' + Math.random().toString(36).substring(2, 15) + '-' + Date.now();
}

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('marea_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ==============================================================================
// Control de Caché Local para Resiliencia Recreate
// ==============================================================================
const CATALOG_CACHE_KEY = 'marea_catalog_cache';
const CATEGORIES_CACHE_KEY = 'marea_categories_cache';

export function getCachedProducts(): Product[] {
  try {
    const raw = localStorage.getItem(CATALOG_CACHE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveCachedProducts(products: Product[]): void {
  try {
    localStorage.setItem(CATALOG_CACHE_KEY, JSON.stringify(products));
  } catch (e) {
    console.warn('No se pudo guardar catálogo en caché:', e);
  }
}

export function getCachedCategories(): Category[] {
  try {
    const raw = localStorage.getItem(CATEGORIES_CACHE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveCachedCategories(cats: Category[]): void {
  try {
    localStorage.setItem(CATEGORIES_CACHE_KEY, JSON.stringify(cats));
  } catch (e) {
    console.warn('No se pudo guardar categorías en caché:', e);
  }
}

// ==============================================================================
// Métodos del Catálogo y Categorías
// ==============================================================================
export async function fetchCategories(): Promise<{ data: Category[]; isCached: boolean }> {
  try {
    const res = await fetch(`${API_BASE}/categories`, { signal: AbortSignal.timeout(4000) });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    saveCachedCategories(data);
    return { data, isCached: false };
  } catch {
    // Si el backend está en Recreate o inaccesible, servir desde caché local
    const cached = getCachedCategories();
    return { data: cached, isCached: true };
  }
}

export async function fetchProducts(params?: {
  category?: string;
  search?: string;
  only_in_stock?: boolean;
  featured?: boolean;
  all_status?: boolean;
}): Promise<{ data: Product[]; isCached: boolean }> {
  try {
    const query = new URLSearchParams();
    if (params?.category) query.set('category', params.category);
    if (params?.search) query.set('search', params.search);
    if (params?.only_in_stock) query.set('only_in_stock', 'true');
    if (params?.featured) query.set('featured', 'true');
    if (params?.all_status) query.set('all_status', 'true');

    const res = await fetch(`${API_BASE}/products?${query.toString()}`, { signal: AbortSignal.timeout(4000) });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    saveCachedProducts(data);
    return { data, isCached: false };
  } catch {
    // Retornar copia local filtrada si el backend está en corte
    let list = getCachedProducts();
    if (params?.category) {
      list = list.filter(p => p.category_name?.toLowerCase().includes(params.category!.toLowerCase()));
    }
    if (params?.search) {
      const q = params.search.toLowerCase();
      list = list.filter(p => p.name.toLowerCase().includes(q) || p.description.toLowerCase().includes(q));
    }
    if (params?.only_in_stock) {
      list = list.filter(p => p.stock > 0);
    }
    if (params?.featured) {
      list = list.filter(p => p.is_featured);
    }
    return { data: list, isCached: true };
  }
}

export async function fetchProductDetail(idOrSlug: string): Promise<Product> {
  try {
    const res = await fetch(`${API_BASE}/products/${idOrSlug}`, { signal: AbortSignal.timeout(4000) });
    if (!res.ok) throw new Error('Producto no encontrado');
    return await res.json();
  } catch (err) {
    const cached = getCachedProducts();
    const found = cached.find(p => String(p.id) === idOrSlug || p.slug === idOrSlug);
    if (found) return found;
    throw err;
  }
}

// ==============================================================================
// Métodos de Pedidos (Órdenes)
// ==============================================================================
export async function createOrder(orderPayload: any, idempotencyKey: string): Promise<Order> {
  const res = await fetch(`${API_BASE}/orders`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Idempotency-Key': idempotencyKey,
      ...getAuthHeader(),
    },
    body: JSON.stringify(orderPayload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Error de servidor' }));
    throw new Error(err.detail || 'No se pudo crear el pedido');
  }

  return await res.json();
}

export async function fetchOrderTracking(orderNumber: string): Promise<Order> {
  const res = await fetch(`${API_BASE}/orders/${orderNumber}`, { signal: AbortSignal.timeout(5000) });
  if (!res.ok) {
    throw new Error('No se encontró el pedido ingresado.');
  }
  return await res.json();
}

export async function fetchOrders(statusFilter?: string): Promise<Order[]> {
  const query = statusFilter ? `?status=${statusFilter}` : '';
  const res = await fetch(`${API_BASE}/orders${query}`, {
    headers: getAuthHeader(),
  });
  if (!res.ok) throw new Error('Error al consultar historial de órdenes');
  return await res.json();
}

export async function updateOrderStatus(orderId: number, newStatus: string): Promise<Order> {
  const res = await fetch(`${API_BASE}/orders/${orderId}/status`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
    body: JSON.stringify({ new_status: newStatus }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Error al cambiar estado' }));
    throw new Error(err.detail);
  }
  return await res.json();
}

// ==============================================================================
// Métodos Administrativos
// ==============================================================================
export async function fetchAdminKpis(): Promise<KpiSummary> {
  const res = await fetch(`${API_BASE}/admin/kpis`, { headers: getAuthHeader() });
  if (!res.ok) throw new Error('Error al cargar KPIs');
  return await res.json();
}

export async function fetchAdminInventory(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/admin/inventory`, { headers: getAuthHeader() });
  if (!res.ok) throw new Error('Error al cargar inventario');
  return await res.json();
}

export async function updateProductStock(productId: number, stock: number): Promise<void> {
  const res = await fetch(`${API_BASE}/products/${productId}/stock`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
    body: JSON.stringify({ stock }),
  });
  if (!res.ok) throw new Error('Error al actualizar existencias');
}

// Sonda de Salud del Backend
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch('/healthz', { signal: AbortSignal.timeout(2000) });
    return res.ok;
  } catch {
    return false;
  }
}
