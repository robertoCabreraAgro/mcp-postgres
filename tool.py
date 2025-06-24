# Tools for interacting with the ``registros`` table.

from server import mcp
from db import SessionLocal
from models import Registro


@mcp.tool(title="Agregar registro")
def agregar(texto: str) -> str:
    """Insert a new row into the database."""
    with SessionLocal() as session:
        reg = Registro(texto=texto)
        session.add(reg)
        session.commit()
        return f"Registro {reg.id} agregado"

@mcp.tool(title="Obtener registro")
def obtener(id: int) -> str:
    """Return the text for a stored record by ID."""
    with SessionLocal() as session:
        reg = session.get(Registro, id)
        if reg:
            return reg.texto
        return "No encontrado"

@mcp.tool(title="Eliminar registro")
def eliminar(id: int) -> str:
    """Delete a record by its ID."""
    with SessionLocal() as session:
        reg = session.get(Registro, id)
        if reg:
            session.delete(reg)
            session.commit()
            return "Eliminado"
        return "No encontrado"
