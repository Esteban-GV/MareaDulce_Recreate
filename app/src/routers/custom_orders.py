from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from src.domain.schemas import CustomOrderCreate, CustomOrderOut
from src.core.security import require_admin
from src.repositories.custom_order_repo import CustomOrderRepository

router = APIRouter(prefix="/api/v1/custom-orders", tags=["Pedidos Personalizados"])

class CustomOrderStatusUpdate(BaseModel):
    status: str
    estimated_price_cop: Optional[int] = None

@router.post("", response_model=CustomOrderOut, status_code=status.HTTP_201_CREATED, summary="Solicitud de pedido personalizado")
def create_custom_order(order_in: CustomOrderCreate):
    """Permite al cliente solicitar una cotización de torta o postre personalizado."""
    order = CustomOrderRepository.create(order_in.model_dump())
    return CustomOrderOut(**order)

@router.get("", response_model=List[CustomOrderOut], summary="Listado de solicitudes personalizadas (Admin)")
def list_custom_orders(_=Depends(require_admin)):
    """Lista solicitudes personalizadas para revisión administrativa."""
    orders = CustomOrderRepository.list_all()
    return [CustomOrderOut(**o) for o in orders]

@router.patch("/{req_id}/status", response_model=CustomOrderOut, summary="Actualizar estado y cotización (Admin)")
def update_custom_order_status(req_id: int, status_in: CustomOrderStatusUpdate, _=Depends(require_admin)):
    """Actualiza el estado de la cotización y define el precio estimado en COP."""
    order = CustomOrderRepository.update_status(req_id, status_in.status, status_in.estimated_price_cop)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada.")
    return CustomOrderOut(**order)
