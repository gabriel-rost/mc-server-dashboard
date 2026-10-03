import json
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from auth import User, require_admin, require_moderator_or_admin
from services.minecraft import write_minecraft_command
from services.system import safe_systemctl


router = APIRouter()
MINECRAFT_DIR = Path(os.getenv("MINECRAFT_DIR", "/home/ubuntu/minecraft"))


class AllowlistPlayerModel(BaseModel):
    gamertag: str = Field(
        ...,
        min_length=3,
        max_length=16,
        pattern=r"^[a-zA-Z0-9_ ]+$",
        description="Nick oficial da Xbox Live (apenas letras, números, espaços e _)",
    )


class OperatorModel(BaseModel):
    xuid: str = Field(
        ...,
        pattern=r"^\d{16}$",
        description="XUID numérico com exatamente 16 dígitos obtido nos logs",
    )


@router.post(
    "/minecraft/restart",
    summary="🔄 Reiniciar Servidor de Minecraft",
    tags=["Minecraft (Amigos & Admin)"],
)
def restart_minecraft_server(
    user: User = Depends(require_moderator_or_admin),
) -> dict[str, str]:
    """Allow moderators and admins to restart Minecraft."""
    safe_systemctl("restart", "minecraft-bedrock")
    return {
        "status": "success",
        "message": (
            "Servidor de Minecraft Bedrock reiniciado "
            f"a pedido de '{user.username}'."
        ),
    }


@router.post(
    "/minecraft/command",
    summary="💻 Enviar comando ao console do Minecraft",
    tags=["Minecraft Gestão (Admin Only)"],
)
def send_minecraft_command(
    command: str = Query(
        ...,
        min_length=1,
        max_length=256,
        description="Um único comando de console, sem quebra de linha.",
    ),
    _: User = Depends(require_admin),
) -> dict[str, str]:
    """Send one console command to the Minecraft FIFO as an administrator."""
    if not command.strip() or any(char in command for char in ("\n", "\r", "\0")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe um único comando válido, sem quebras de linha ou caracteres nulos.",
        )

    write_minecraft_command(command)
    return {"status": "success", "command_sent": command}


@router.post(
    "/minecraft/allowlist/add",
    summary="➕ Adicionar Jogador na Allowlist",
    tags=["Minecraft (Amigos & Admin)"],
)
def add_to_allowlist(
    player: AllowlistPlayerModel,
    user: User = Depends(require_moderator_or_admin),
) -> dict[str, str]:
    """Add a player to the allowlist and restart Minecraft."""
    allowlist_path = MINECRAFT_DIR / "allowlist.json"
    data = []
    if allowlist_path.exists():
        try:
            with allowlist_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            data = []

    if not any(entry.get("name") == player.gamertag for entry in data):
        data.append({"ignoresPlayerLimit": False, "name": player.gamertag})
        with allowlist_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

        safe_systemctl("restart", "minecraft-bedrock")
        return {
            "status": "success",
            "message": (
                f"Jogador '{player.gamertag}' adicionado à allowlist por "
                f"'{user.username}'! Servidor recarregado."
            ),
        }

    return {
        "status": "info",
        "message": f"Jogador '{player.gamertag}' já está cadastrado na allowlist.",
    }


@router.post(
    "/minecraft/op/add",
    summary="👑 Dar Permissão de Operador (OP)",
    tags=["Minecraft Gestão (Admin Only)"],
)
def add_op(
    player: OperatorModel,
    _: User = Depends(require_admin),
) -> dict[str, str]:
    """Grant Minecraft operator permission to a player."""
    permission_path = MINECRAFT_DIR / "permissions.json"
    data = []
    if permission_path.exists():
        try:
            with permission_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            data = []

    data = [entry for entry in data if entry.get("xuid") != player.xuid]
    data.append({"permission": "operator", "xuid": player.xuid})

    with permission_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    safe_systemctl("restart", "minecraft-bedrock")
    return {
        "status": "success",
        "message": f"Jogador com XUID '{player.xuid}' promovido a Operador!",
    }
