from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Header, Query
from src.domain.schemas import OrderCreate, OrderOut, OrderStatusUpdate
from src.domain.constants import OrderStatus
from src.core.config import settings
from src.core.security import security_scheme, decode_access_token, require_admin
from src.core.metrics import MAREA_ORDERS_TOTAL, MAREA_REVENUE_COP_TOTAL
from src.repositories.order_repo import OrderRepository

router = APIRouter(prefix="/api/v1/orders", tags=["Pedidos"])

def get_optional_user(credentials=Depends(security_scheme)) -> Optional[dict]:
    if not credentials:
        return None
    try:
        return decode_access_token(credentials.credentials)
    except Exception:
        return None

@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED, summary="Crear pedido con Idempotencia y Control de Stock")
def create_order(
    order_in: OrderCreate,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key", description="Clave de idempotencia única UUIDv4"),
    user_payload: Optional[dict] = Depends(get_optional_user)
):
    """
    Crea un pedido validando stock en tiempo real mediante una transacción atómica exclusiva.
    Soporta Idempotency-Key para evitar pedidos duplicados ante reintentos de red.
    """
    user_id = int(user_payload["sub"]) if user_payload and "sub" in user_payload else None
    
    order_dict = order_in.model_dump(exclude={"items"})
    items_list = [item.model_dump() for item in order_in.items]

    try:
        order = OrderRepository.create_order(
            order_data=order_dict,
            items_data=items_list,
            idempotency_key=idempotency_key,
            user_id=user_id
        )
        # Registrar métricas en Prometheus
        schema_ver = "v2" if settings.VERSION.startswith("2") else "v1"
        MAREA_ORDERS_TOTAL.labels(status="PENDIENTE", schema_version=schema_ver).inc()
        MAREA_REVENUE_COP_TOTAL.inc(order["total_cop"])
        
        return OrderOut(**order)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al procesar el pedido: {str(e)}")

@router.get("/{order_number_or_id}", response_model=OrderOut, summary="Seguimiento y detalle de pedido")
def get_order_tracking(order_number_or_id: str):
    """Permite al cliente consultar el estado y la línea de tiempo de su pedido."""
    if order_number_or_id.isdigit():
        order = OrderRepository.get_by_id(int(order_number_or_id))
    else:
        order = OrderRepository.get_by_order_number(order_number_or_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado.")
    return OrderOut(**order)

@router.get("", response_model=List[OrderOut], summary="Listado de pedidos")
def list_orders(
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_payload: Optional[dict] = Depends(get_optional_user)
):
    """
    Retorna el historial de pedidos. Si es cliente autenticado, lista sus propios pedidos.
    Si es administrador, permite ver la totalidad con filtros.
    """
    if not user_payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Se requiere autenticación para listar pedidos.")

    user_role = user_payload.get("role")
    user_id = int(user_payload["sub"])

    if user_role == "administrador":
        orders = OrderRepository.list_orders(user_id=None, status=status, limit=limit, offset=offset)
    else:
        orders = OrderRepository.list_orders(user_id=user_id, status=status, limit=limit, offset=offset)

    return [OrderOut(**o) for o in orders]

@router.patch("/{order_id}/status", response_model=OrderOut, summary="Transición de estado de pedido (Admin)")
def update_order_status(order_id: int, status_in: OrderStatusUpdate, _=Depends(require_admin)):
    """Aplica un cambio de estado en el flujo del pedido validando las transiciones de negocio permitidas."""
    try:
        updated = OrderRepository.update_status(order_id, status_in.new_status)
        schema_ver = "v2" if settings.VERSION.startswith("2") else "v1"
        MAREA_ORDERS_TOTAL.labels(status=status_in.new_status.value, schema_version=schema_ver).inc()
        return OrderOut(**updated)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
