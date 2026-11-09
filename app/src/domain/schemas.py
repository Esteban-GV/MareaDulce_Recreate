from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from src.domain.constants import UserRole, OrderStatus, DeliveryType, PaymentMethod

# ==========================================
# USUARIOS Y AUTENTICACIÓN
# ==========================================
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Contraseña de al menos 6 caracteres")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(UserBase):
    id: int
    role: UserRole
    created_at: str
    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# ==========================================
# CATEGORÍAS
# ==========================================
class CategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    display_order: int = 0

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None

class CategoryOut(CategoryBase):
    id: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# PRODUCTOS
# ==========================================
class ProductBase(BaseModel):
    name: str
    slug: str
    category_id: int
    description: str
    price_cop: int = Field(..., ge=0, description="Precio en enteros de Pesos Colombianos (COP)")
    servings: str
    prep_time_hours: int = 24
    ingredients: str
    allergens: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    badge: Optional[str] = None
    stock: int = Field(default=0, ge=0)
    is_active: bool = True
    is_featured: bool = False

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    price_cop: Optional[int] = Field(None, ge=0)
    servings: Optional[str] = None
    prep_time_hours: Optional[int] = None
    ingredients: Optional[str] = None
    allergens: Optional[List[str]] = None
    image_url: Optional[str] = None
    badge: Optional[str] = None
    stock: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None

class ProductOut(ProductBase):
    id: int
    category_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# PEDIDOS (ÓRDENES)
# ==========================================
class OrderItemCustomization(BaseModel):
    servings: Optional[str] = None
    flavor: Optional[str] = None
    custom_message: Optional[str] = Field(None, max_length=40, description="Dedicatoria personalizada (máximo 40 caracteres)")
    delivery_slot: Optional[str] = None
    notes: Optional[str] = None

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0, description="Cantidad mayor a cero")
    customization: Optional[OrderItemCustomization] = None

class OrderItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    unit_price_cop: int
    quantity: int
    subtotal_cop: int
    servings: Optional[str] = None
    flavor: Optional[str] = None
    custom_message: Optional[str] = None
    delivery_slot: Optional[str] = None
    notes: Optional[str] = None

class OrderCreate(BaseModel):
    customer_name: str
    customer_email: EmailStr
    customer_phone: str
    delivery_type: DeliveryType
    delivery_address: Optional[str] = None
    delivery_date: str = Field(..., description="Fecha requerida AAAA-MM-DD")
    delivery_slot: Optional[str] = Field(None, description="Franja horaria (Mañana / Tarde)")
    items: List[OrderItemCreate] = Field(..., min_length=1, description="Al menos un producto en el pedido")
    notes: Optional[str] = None
    payment_method: PaymentMethod = PaymentMethod.SIMULADO_DEMO

class OrderStatusUpdate(BaseModel):
    new_status: OrderStatus
    reason: Optional[str] = None

class OrderOut(BaseModel):
    id: int
    order_number: str
    user_id: Optional[int] = None
    customer_name: str
    customer_email: str
    customer_phone: str
    delivery_type: DeliveryType
    delivery_address: Optional[str] = None
    delivery_date: str
    delivery_slot: Optional[str] = None
    status: OrderStatus
    payment_method: PaymentMethod
    payment_status: str
    total_cop: int
    notes: Optional[str] = None
    idempotency_key: Optional[str] = None
    created_at: str
    updated_at: str
    items: List[OrderItemOut]
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# PEDIDOS PERSONALIZADOS
# ==========================================
class CustomOrderCreate(BaseModel):
    customer_name: str
    customer_email: EmailStr
    customer_phone: str
    product_type: str = Field(..., description="Torta, Cupcakes temáticos, etc.")
    servings: int = Field(..., gt=0)
    required_date: str
    description: str
    reference_image_url: Optional[str] = None

class CustomOrderOut(CustomOrderCreate):
    id: int
    status: str
    estimated_price_cop: Optional[int] = None
    created_at: str

# ==========================================
# KPI Y ADMINISTRACIÓN
# ==========================================
class KpiSummaryOut(BaseModel):
    today_sales_cop: int
    pending_orders_count: int
    month_orders_count: int
    low_stock_products_count: int
    total_catalog_products: int
