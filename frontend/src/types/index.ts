export type UserRole = 'cliente' | 'administrador';

export interface User {
  id: number;
  email: string;
  full_name: string;
  phone?: string;
  role: UserRole;
  created_at: string;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  description?: string;
  display_order: number;
  is_active: boolean;
}

export interface Product {
  id: number;
  category_id: number;
  category_name?: string;
  name: string;
  slug: string;
  description: string;
  price_cop: number;
  servings: string;
  prep_time_hours: number;
  ingredients: string;
  allergens: string[];
  image_url?: string;
  badge?: string;
  stock: number;
  is_active: boolean;
  is_featured: boolean;
}

export interface CartItemCustomization {
  servings?: string;
  flavor?: string;
  custom_message?: string;
  delivery_slot?: string;
  notes?: string;
}

export interface CartItem {
  product: Product;
  quantity: number;
  customization?: CartItemCustomization;
}

export type OrderStatus = 'PENDIENTE' | 'CONFIRMADO' | 'EN_PREPARACION' | 'LISTO' | 'ENTREGADO' | 'CANCELADO';
export type DeliveryType = 'domicilio' | 'recogida_tienda';

export interface OrderItem {
  id: number;
  product_id: number;
  product_name: string;
  unit_price_cop: number;
  quantity: number;
  subtotal_cop: number;
  servings?: string;
  flavor?: string;
  custom_message?: string;
  delivery_slot?: string;
  notes?: string;
}

export interface Order {
  id: number;
  order_number: string;
  user_id?: number;
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  delivery_type: DeliveryType;
  delivery_address?: string;
  delivery_date: string;
  delivery_slot?: string;
  status: OrderStatus;
  payment_method: string;
  payment_status: string;
  total_cop: number;
  notes?: string;
  idempotency_key?: string;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
}

export interface KpiSummary {
  today_sales_cop: number;
  pending_orders_count: number;
  month_orders_count: number;
  low_stock_products_count: number;
  total_catalog_products: number;
}
