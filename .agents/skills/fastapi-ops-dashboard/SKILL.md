---
name: fastapi-ops-dashboard
description: >-
  Especializada na criação, extensão e manutenção de micro-dashboards operacionais em FastAPI + Swagger UI
  para controle e orquestração de serviços Linux (systemd/Docker), gerenciamento de processos em lote
  (ex: Modo Jogo vs Modo Web), autenticação segura com RBAC (Admin vs Amigos) e execução protegida de comandos.
---

# FastAPI Ops Dashboard & Server Orchestrator

Guia para implementar e evoluir painéis de controle REST ultraleves baseados em **FastAPI**, utilizando a documentação interativa automática (**Swagger UI** em `/docs`) como interface visual autenticada para gerenciar serviços Linux (`systemd`), containers e recursos de hardware sem exigir um frontend dedicado.

---

## 🎯 Quando Usar

- Construir endpoints para ligar, desligar ou reiniciar serviços (`gunicorn`, `redis`, `docker`, `minecraft`).
- Implementar **perfis de execução em lote** (ex: *Modo Jogo* que desativa aplicações web pesadas e sobe servidores de jogos).
- Implementar **autenticação com níveis de acesso (RBAC)** para permitir que amigos reiniciem jogos ou adicionem pessoas na allowlist sem acesso ao sistema operacional.
- Prevenir vulnerabilidades críticas de injeção de comandos (*command injection*) em APIs que chamam `subprocess`.
- Configurar segurança de execução de comandos do sistema com regras restritas no `sudoers`.

---

## 🛡️ Pilares de Segurança para APIs Operacionais

### 1. Eliminação Total de `shell=True` (Zero Command Injection)
**Nunca** use `shell=True` interpolando strings vindas de rotas da API. Use vetores de argumentos fixos combinados com validação por lista branca (whitelist):

```python
import subprocess
from fastapi import HTTPException

ALLOWED_SERVICES = {"minecraft-bedrock", "gunicorn", "redis-server"}
ALLOWED_ACTIONS = {"start", "stop", "restart", "is-active"}

def safe_systemctl(action: str, service: str) -> str:
    if action not in ALLOWED_ACTIONS:
        raise HTTPException(status_code=400, detail="Ação não autorizada.")
    if service not in ALLOWED_SERVICES:
        raise HTTPException(status_code=400, detail="Serviço não autorizado.")

    cmd = ["sudo", "systemctl", action, service]
    try:
        res = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Erro: {e.stderr.strip() or e.stdout.strip()}")
```

### 2. Autenticação e RBAC no Swagger UI (Client & Secret)
O Swagger UI (`/docs`) possui integração nativa com `HTTPBasic`, exibindo um botão de **Authorize 🔒**:

```python
import secrets
from enum import Enum
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

class UserRole(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"  # Amigos com acesso restrito

def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)):
    user = USERS_DB.get(credentials.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers={"WWW-Authenticate": "Basic"})
    
    # Previne ataques de timing
    if not secrets.compare_digest(credentials.password.encode(), user["secret"].encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers={"WWW-Authenticate": "Basic"})
    return user

def require_role(roles: list[UserRole]):
    def checker(user = Depends(authenticate_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente.")
        return user
    return checker
```

---

## 🏗️ Padrões de Controle (Individual & Lote)

```python
# Apenas Admin pode disparar modos em lote
@app.post("/batch/gaming-mode", tags=["Perfis em Lote (Admin)"])
def enable_gaming_mode(_ = Depends(require_role([UserRole.ADMIN]))):
    for svc in ["gunicorn", "redis-server"]:
        safe_systemctl("stop", svc)
    safe_systemctl("start", "minecraft-bedrock")
    return {"status": "success", "mode": "gaming"}

# Amigos E Admins podem reiniciar o Minecraft
@app.post("/minecraft/restart", tags=["Minecraft (Amigos & Admin)"])
def restart_minecraft(_ = Depends(require_role([UserRole.ADMIN, UserRole.MODERATOR]))):
    safe_systemctl("restart", "minecraft-bedrock")
    return {"status": "success", "message": "Minecraft reiniciado com sucesso."}
```

---

## 🔒 3. Mínimo Privilégio no `sudoers`

Em vez de liberar comandos genéricos com `*`, limite o `sudoers` explicitamente aos comandos suportados pela API:

`/etc/sudoers.d/dashboard-mc`:
```text
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl start minecraft-bedrock, /bin/systemctl stop minecraft-bedrock, /bin/systemctl restart minecraft-bedrock, /bin/systemctl is-active minecraft-bedrock, /bin/systemctl start gunicorn, /bin/systemctl stop gunicorn, /bin/systemctl restart gunicorn, /bin/systemctl is-active gunicorn, /bin/systemctl start redis-server, /bin/systemctl stop redis-server, /bin/systemctl restart redis-server, /bin/systemctl is-active redis-server
```

---

## 🚀 4. Execução como Serviço `systemd`

`/etc/systemd/system/server-dashboard.service`:
```ini
[Unit]
Description=FastAPI Server Dashboard
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/server-dashboard
ExecStart=/home/ubuntu/server-dashboard/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```
