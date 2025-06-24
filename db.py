# db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

engine = create_engine("postgresql+psycopg2://usuario:password@localhost/mi_db")
SessionLocal = sessionmaker(bind=engine)
