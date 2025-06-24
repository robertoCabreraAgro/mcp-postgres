# mcp-postgres/app/models.py

from sqlalchemy import Column, Integer, String, JSON
from app.db import Base

class Registro(Base):
    __tablename__ = "registro"

    id = Column(Integer, primary_key=True, index=True)
    texto = Column(String)

class ProductTemplate(Base):
    __tablename__ = "product_template"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(JSON)  # Mapeo correcto para jsonb en Postgres
