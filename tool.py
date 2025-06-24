from mcp_instance import mcp
from db import SessionLocal
from models import Registro

@mcp.tool()
def agregar(texto: str) -> str:
    with SessionLocal() as session:
        reg = Registro(texto=texto)
        session.add(reg)
        session.commit()
        return f"Registro {reg.id} agregado"

@mcp.tool()
def obtener(id: int) -> str:
    with SessionLocal() as session:
        reg = session.get(Registro, id)
        return reg.texto if reg else "No encontrado"

@mcp.tool()
def eliminar(id: int) -> str:
    with SessionLocal() as session:
        reg = session.get(Registro, id)
        if reg:
            session.delete(reg)
            session.commit()
            return "Eliminado"
        return "No encontrado"
