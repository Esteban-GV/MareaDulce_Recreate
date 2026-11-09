from enum import Enum
from typing import Set, Dict

class UserRole(str, Enum):
    CLIENTE = "cliente"
    ADMINISTRADOR = "administrador"

class OrderStatus(str, Enum):
    PENDIENTE = "PENDIENTE"
    CONFIRMADO = "CONFIRMADO"
    EN_PREPARACION = "EN_PREPARACION"
    LISTO = "LISTO"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"

# Transiciones de estado permitidas según regla de negocio
VALID_ORDER_TRANSITIONS: Dict[OrderStatus, Set[OrderStatus]] = {
    OrderStatus.PENDIENTE: {OrderStatus.CONFIRMADO, OrderStatus.CANCELADO},
    OrderStatus.CONFIRMADO: {OrderStatus.EN_PREPARACION, OrderStatus.CANCELADO},
    OrderStatus.EN_PREPARACION: {OrderStatus.LISTO, OrderStatus.CANCELADO},
    OrderStatus.LISTO: {OrderStatus.ENTREGADO},
    OrderStatus.ENTREGADO: set(),  # Estado final
    OrderStatus.CANCELADO: set(),  # Estado final
}

class DeliveryType(str, Enum):
    DOMICILIO = "domicilio"
    RECOGIDA_TIENDA = "recogida_tienda"

class PaymentMethod(str, Enum):
    SIMULADO_DEMO = "simulado_demo"
