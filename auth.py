import json
import os
import secrets
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel


class UserRole(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"


class User(BaseModel):
    username: str
    role: UserRole
    description: str


security = HTTPBasic()
users_file = Path(os.getenv("USERS_FILE", str(Path(__file__).with_name("users.json"))))


def load_users_db() -> dict[str, dict[str, Any]]:
    """Load and validate users from the external credentials file."""
    try:
        with users_file.open("r", encoding="utf-8") as file:
            users_db = json.load(file)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Autenticação indisponível: configure um USERS_FILE JSON válido e acessível.",
        ) from exc

    if not isinstance(users_db, dict) or not users_db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Autenticação indisponível: USERS_FILE deve conter ao menos um usuário.",
        )

    valid_roles = {role.value for role in UserRole}
    for username, user_record in users_db.items():
        if (
            not isinstance(username, str)
            or not username
            or not isinstance(user_record, dict)
            or not isinstance(user_record.get("secret"), str)
            or not user_record["secret"]
            or not isinstance(user_record.get("role"), str)
            or user_record["role"] not in valid_roles
            or not isinstance(user_record.get("description", ""), str)
        ):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Autenticação indisponível: USERS_FILE contém usuário com configuração inválida.",
            )

    return users_db


def authenticate_user(
    credentials: HTTPBasicCredentials = Depends(security),
) -> User:
    """Validate HTTP Basic credentials using a timing-safe comparison."""
    user_record = load_users_db().get(credentials.username)

    if user_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas ou usuário inexistente.",
            headers={"WWW-Authenticate": "Basic"},
        )

    if not secrets.compare_digest(
        credentials.password.encode("utf-8"),
        user_record["secret"].encode("utf-8"),
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Basic"},
        )

    return User(
        username=credentials.username,
        role=UserRole(user_record["role"]),
        description=user_record.get("description", ""),
    )


def require_role(allowed_roles: list[UserRole]):
    def role_checker(
        current_user: User = Depends(authenticate_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Acesso negado: Perfil '{current_user.role.value}' "
                    "não possui permissão para esta ação."
                ),
            )
        return current_user

    return role_checker


require_admin = require_role([UserRole.ADMIN])
require_moderator_or_admin = require_role([UserRole.ADMIN, UserRole.MODERATOR])
