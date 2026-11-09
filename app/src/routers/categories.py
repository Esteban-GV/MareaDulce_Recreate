from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from src.domain.schemas import CategoryOut, CategoryCreate, CategoryUpdate
from src.core.security import require_admin
from src.repositories.category_repo import CategoryRepository

router = APIRouter(prefix="/api/v1/categories", tags=["Categorías"])

@router.get("", response_model=List[CategoryOut], summary="Listado público de categorías")
def list_categories():
    """Retorna todas las categorías activas del catálogo."""
    return [CategoryOut(**c) for c in CategoryRepository.list_all(only_active=True)]

@router.get("/{slug_or_id}", response_model=CategoryOut, summary="Detalle de categoría")
def get_category(slug_or_id: str):
    """Busca una categoría por ID o por slug amigable."""
    if slug_or_id.isdigit():
        cat = CategoryRepository.get_by_id(int(slug_or_id))
    else:
        cat = CategoryRepository.get_by_slug(slug_or_id)
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada.")
    return CategoryOut(**cat)

@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED, summary="Crear categoría (Admin)")
def create_category(cat_in: CategoryCreate, _=Depends(require_admin)):
    """Crea una nueva categoría. Requiere rol de administrador."""
    existing = CategoryRepository.get_by_slug(cat_in.slug)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe una categoría con ese slug.")
    cat = CategoryRepository.create(
        name=cat_in.name,
        slug=cat_in.slug,
        description=cat_in.description,
        display_order=cat_in.display_order
    )
    return CategoryOut(**cat)

@router.put("/{cat_id}", response_model=CategoryOut, summary="Actualizar categoría (Admin)")
def update_category(cat_id: int, cat_in: CategoryUpdate, _=Depends(require_admin)):
    """Actualiza una categoría existente. Requiere rol de administrador."""
    cat = CategoryRepository.update(cat_id, cat_in.model_dump(exclude_unset=True))
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada.")
    return CategoryOut(**cat)

@router.delete("/{cat_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar o desactivar categoría (Admin)")
def delete_category(cat_id: int, _=Depends(require_admin)):
    """Elimina la categoría o la desactiva si tiene productos asociados."""
    ok = CategoryRepository.delete(cat_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada.")
    return None
