import os
import stat
from pathlib import Path

from fastapi import HTTPException, status


MINECRAFT_FIFO = Path(os.getenv("MINECRAFT_FIFO", "/tmp/minecraft.fifo"))


def write_minecraft_command(command: str) -> None:
    """Write one command to an existing FIFO without invoking a shell."""
    try:
        if not stat.S_ISFIFO(MINECRAFT_FIFO.lstat().st_mode):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Canal de comandos do Minecraft não está configurado como FIFO.",
            )

        flags = os.O_WRONLY | os.O_NONBLOCK
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fifo_fd = os.open(MINECRAFT_FIFO, flags)
        try:
            if not stat.S_ISFIFO(os.fstat(fifo_fd).st_mode):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Canal de comandos do Minecraft não está configurado como FIFO.",
                )
            payload = (command + "\n").encode("utf-8")
            written = 0
            while written < len(payload):
                written += os.write(fifo_fd, payload[written:])
        finally:
            os.close(fifo_fd)
    except HTTPException:
        raise
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível enviar o comando: FIFO indisponível ou sem leitor ativo.",
        ) from exc
