# Crear
@mcp.tool(title="Agregar registro")
def agregar(texto: str) -> str:
    with SessionLocal() as session:
        reg = Registro(texto=texto)
        session.add(reg)
        session.commit()
        return f"Registro {reg.id} agregado"

# Consultar
@mcp.tool(title="Obtener registro")
def obtener(id: int) -> str:
    with SessionLocal() as session:
        reg = session.get(Registro, id)
        if reg:
            return reg.texto
        return "No encontrado"

# Eliminar
@mcp.tool(title="Eliminar registro")
def eliminar(id: int) -> str:
    with SessionLocal() as session:
        reg = session.get(Registro, id)
        if reg:
            session.delete(reg)
            session.commit()
            return "Eliminado"
        return "No encontrado"
