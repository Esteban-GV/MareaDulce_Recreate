from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field
from src.domain.schemas import ProductOut, ProductCreate, ProductUpdate
from src.core.security import require_admin
from src.repositories.product_repo import ProductRepository

router = APIRouter(prefix="/api/v1/products", tags=["Productos"])

class StockUpdate(BaseModel):
    stock: int = Field(..., ge=0, description="Nueva cantidad de unidades en inventario")

@router.get("", response_model=List[ProductOut], summary="Listado y filtrado de productos")
def list_products(
    category: Optional[str] = Query(None, description="Filtrar por slug de categoría"),
    search: Optional[str] = Query(None, description="Búsqueda por texto en nombre o descripción"),
    only_in_stock: bool = Query(False, description="Mostrar solo productos con stock > 0"),
    featured: bool = Query(False, description="Mostrar solo productos destacados"),
    all_status: bool = Query(False, description="Incluir inactivos (solo administración)")
):
    """Retorna productos del catálogo con opciones de filtro."""
    products = ProductRepository.list_products(
        category_slug=category,
        search=search,
        only_active=not all_status,
        only_in_stock=only_in_stock,
        featured_only=featured
    )
    return [ProductOut(**p) for p in products]

@router.get("/{id_or_slug}", response_model=ProductOut, summary="Detalle de producto")
def get_product(id_or_slug: str):
    """Busca un producto por su identificador numérico o slug amigable."""
    if id_or_slug.isdigit():
        prod = ProductRepository.get_by_id(int(id_or_slug))
    else:
        prod = ProductRepository.get_by_slug(id_or_slug)
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado en el catálogo.")
    return ProductOut(**prod)

@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED, summary="Crear producto (Admin)")
def create_product(prod_in: ProductCreate, _=Depends(require_admin)):
    """Crea un nuevo producto en el catálogo. Requiere rol de administrador."""
    existing = ProductRepository.get_by_slug(prod_in.slug)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un producto con ese slug.")
    prod = ProductRepository.create(prod_in.model_dump())
    return ProductOut(**prod)

@router.put("/{prod_id}", response_model=ProductOut, summary="Actualizar producto (Admin)")
def update_product(prod_id: int, prod_in: ProductUpdate, _=Depends(require_admin)):
    """Actualiza datos del producto. Requiere rol de administrador."""
    prod = ProductRepository.update(prod_id, prod_in.model_dump(exclude_unset=True))
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado.")
    return ProductOut(**prod)

@router.patch("/{prod_id}/stock", response_model=ProductOut, summary="Edición rápida de inventario (Admin)")
def update_stock(prod_id: int, stock_in: StockUpdate, _=Depends(require_admin)):
    """Ajusta directamente las existencias de un producto."""
    prod = ProductRepository.update_stock(prod_id, stock_in.stock)
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado.")
    return ProductOut(**prod)

@router.delete("/{prod_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Desactivar producto (Admin)")
def delete_product(prod_id: int, _=Depends(require_admin)):
    """Desactiva un producto del catálogo (soft-delete)."""
    prod = ProductRepository.update(prod_id, {"is_active": 0})
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado.")
    return None
