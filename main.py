# mcp-postgres/main.py

from dotenv import load_dotenv
# Cargar las variables de entorno ANTES que cualquier otra importación de la app
load_dotenv()

from fastapi import FastAPI
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from app.db import init_db
# --- CAMBIO CRÍTICO ---
# Importamos los modelos aquí para que SQLAlchemy los "conozca"
# antes de que se llame a init_db().
from app import models

# Creamos una instancia de FastAPI
mcp = FastAPI(title="Postgres GPT Server")

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Context manager para manejar eventos de inicio y apagado de la aplicación.
    """
    print("Iniciando la aplicación...")
    # Ahora, cuando se llame a init_db(), ya conocerá el modelo ProductProduct
    init_db()
    print("Base de datos inicializada.")
    yield
    print("Apagando la aplicación...")

# Asignamos el lifespan a nuestra aplicación FastAPI
mcp.router.lifespan_context = lifespan

# Este es un endpoint de ejemplo para verificar que el servidor está funcionando.
@mcp.get("/")
def read_root():
    return {"message": "Servidor Postgres GPT listo. Usa la consola interactiva para chatear."}
