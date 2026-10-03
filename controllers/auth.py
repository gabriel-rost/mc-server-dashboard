from fastapi import APIRouter, Depends

from auth import User, authenticate_user


router = APIRouter()


@router.get("/auth/me", summary="👤 Dados da Sessão Atual", tags=["Autenticação"])
def get_current_user_profile(user: User = Depends(authenticate_user)):
    """Return the authenticated user's profile."""
    return {
        "username": user.username,
        "role": user.role,
        "description": user.description,
    }
