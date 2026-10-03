import subprocess

from fastapi import HTTPException


ALLOWED_SERVICES = {
    "minecraft-bedrock",
    "church",
    "dispatcher",
    "flaskapp",
    "flood",
}
ALLOWED_ACTIONS = {"start", "stop", "restart", "is-active"}
WEB_SERVICES = ["church", "dispatcher", "flaskapp", "flood"]
GAME_SERVICES = ["minecraft-bedrock"]


def safe_systemctl(action: str, service_name: str) -> str:
    """Run systemctl with a strict service/action allowlist and no shell."""
    if action not in ALLOWED_ACTIONS:
        raise HTTPException(status_code=400, detail=f"Ação não permitida: {action}")
    if service_name not in ALLOWED_SERVICES:
        raise HTTPException(
            status_code=400,
            detail=f"Serviço não autorizado: {service_name}",
        )

    command = ["sudo", "systemctl", action, service_name]
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as exc:
        error = exc.stderr.strip() or exc.stdout.strip() or "Erro de execução no systemctl."
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao executar '{' '.join(command)}': {error}",
        ) from exc


def check_service_status(service_name: str) -> str:
    """Return the status for an allowlisted service."""
    if service_name not in ALLOWED_SERVICES:
        return "unauthorized"
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() or "inactive"
    except OSError:
        return "error"
