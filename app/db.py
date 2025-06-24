# mcp-postgres/app/db.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Obtenemos la URL de la base de datos de las variables de entorno.
# Si no se encuentra, se usará una base de datos SQLite local.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

engine = create_engine(
    DATABASE_URL,
    # El argumento 'connect_args' es específico de SQLite y solo se aplica si es necesario.
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    # Esta función crea las tablas que están definidas como modelos en el Base.
    # No afectará a las tablas que ya existen.
    Base.metadata.create_all(bind=engine)
