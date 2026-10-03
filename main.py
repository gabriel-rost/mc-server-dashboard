import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from controllers.auth import router as auth_router
from controllers.minecraft import router as minecraft_router
from controllers.system import router as system_router

is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"

app = FastAPI(
    title="Oracle VM Admin Dashboard",
    description="Painel de controle com autenticação segura e RBAC (Admin vs Amigos) para gestão de serviços e Minecraft BDS",
    version="2.1.0",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

app.include_router(auth_router)
app.include_router(system_router)
app.include_router(minecraft_router)
app.mount(
    "/ui",
    StaticFiles(directory=Path(__file__).parent / "frontend", html=True),
    name="frontend",
)
