import subprocess
from typing import Any

from fastapi import APIRouter, Depends

from auth import (
    User,
    UserRole,
    require_admin,
    require_moderator_or_admin,
)
from services.system import (
    GAME_SERVICES,
    WEB_SERVICES,
    check_service_status,
    safe_systemctl,
)


router = APIRouter()


@router.get(
    "/system/status",
    summary="📊 Status Geral dos Recursos e Serviços",
    tags=["Monitoramento"],
)
def get_system_status(
    user: User = Depends(require_moderator_or_admin),
) -> dict[str, Any]:
    """Return Minecraft status to moderators and full telemetry to admins."""
    minecraft_status = check_service_status("minecraft-bedrock")

    if user.role == UserRole.MODERATOR:
        return {
            "requested_by": user.username,
            "role": user.role,
            "minecraft_status": minecraft_status,
        }

    try:
        memory_process = subprocess.run(
            ["free", "-m"],
            capture_output=True,
            text=True,
            check=True,
        )
        memory_summary = [
            line
            for line in memory_process.stdout.splitlines()
            if "Mem" in line or "Swap" in line
        ]
    except (OSError, subprocess.CalledProcessError):
        memory_summary = ["Não foi possível obter telemetria de memória."]

    return {
        "requested_by": user.username,
        "role": user.role,
        "memory_summary": memory_summary,
        "services": {
            "minecraft": minecraft_status,
            "web_services": {
                service: check_service_status(service) for service in WEB_SERVICES
            },
        },
    }


@router.post(
    "/service/{service_name}/{action}",
    summary="⚙️ Ação Individual em um Serviço",
    tags=["Controle Individual (Admin)"],
)
def control_single_service(
    service_name: str,
    action: str,
    _: User = Depends(require_admin),
) -> dict[str, str]:
    """Control one allowlisted service as an administrator."""
    if action == "status":
        return {
            "service": service_name,
            "status": check_service_status(service_name),
        }

    safe_systemctl(action, service_name)
    return {
        "status": "success",
        "message": f"Ação '{action}' aplicada com sucesso em '{service_name}'.",
    }


@router.post(
    "/batch/gaming-mode",
    summary="🎮 Ativar Modo Jogo (Para Web + Inicia Minecraft)",
    tags=["Perfis em Lote (Admin)"],
)
def enable_gaming_mode(
    _: User = Depends(require_admin),
) -> dict[str, Any]:
    """Stop application services and start Minecraft."""
    stopped = []
    for service in WEB_SERVICES:
        try:
            safe_systemctl("stop", service)
            stopped.append(service)
        except Exception:
            pass

    safe_systemctl("start", "minecraft-bedrock")
    return {
        "status": "success",
        "message": "Modo Jogo Ativado! Memória liberada para a jogatina.",
        "stopped_services": stopped,
        "started_services": GAME_SERVICES,
    }


@router.post(
    "/batch/web-mode",
    summary="🌐 Ativar Modo Web (Para Minecraft + Inicia Web)",
    tags=["Perfis em Lote (Admin)"],
)
def enable_web_mode(
    _: User = Depends(require_admin),
) -> dict[str, Any]:
    """Stop Minecraft and start the application services."""
    try:
        safe_systemctl("stop", "minecraft-bedrock")
    except Exception:
        pass

    started = []
    for service in WEB_SERVICES:
        try:
            safe_systemctl("start", service)
            started.append(service)
        except Exception:
            pass

    return {
        "status": "success",
        "message": "Modo Web Ativado! Minecraft pausado e stack web online.",
        "stopped_services": GAME_SERVICES,
        "started_services": started,
    }


@router.post(
    "/batch/stop-all",
    summary="🛑 Parar Tudo (Manutenção / Máxima Memória)",
    tags=["Perfis em Lote (Admin)"],
)
def stop_all_services(
    _: User = Depends(require_admin),
) -> dict[str, Any]:
    """Stop all managed services."""
    all_services = WEB_SERVICES + GAME_SERVICES
    for service in all_services:
        try:
            safe_systemctl("stop", service)
        except Exception:
            pass
    return {
        "status": "success",
        "message": "Todos os serviços foram parados.",
        "stopped_services": all_services,
    }
