from fastapi import APIRouter, HTTPException, status, Depends
from src.domain.schemas import UserCreate, UserLogin, UserOut, TokenResponse
from src.core.security import verify_password, create_access_token, get_current_user_payload
from src.repositories.user_repo import UserRepository

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, summary="Registro de cliente")
def register(user_in: UserCreate):
    """Registra un nuevo usuario cliente en la plataforma."""
    existing = UserRepository.get_by_email(user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cuenta registrada con este correo electrónico."
        )
    user = UserRepository.create_user(
        email=user_in.email,
        full_name=user_in.full_name,
        password=user_in.password,
        phone=user_in.phone,
        role="cliente"
    )
    token = create_access_token({"sub": str(user["id"]), "email": user["email"], "role": user["role"]})
    return TokenResponse(access_token=token, user=UserOut(**user))

@router.post("/login", response_model=TokenResponse, summary="Inicio de sesión")
def login(credentials: UserLogin):
    """Valida credenciales y genera un token JWT Bearer."""
    user = UserRepository.get_by_email(credentials.email)
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas. Verifica tu correo y contraseña."
        )
    token = create_access_token({"sub": str(user["id"]), "email": user["email"], "role": user["role"]})
    return TokenResponse(access_token=token, user=UserOut(**user))

@router.get("/me", response_model=UserOut, summary="Perfil del usuario autenticado")
def get_me(payload: dict = Depends(get_current_user_payload)):
    """Obtiene los datos del usuario en sesión."""
    user = UserRepository.get_by_id(int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    return UserOut(**user)
