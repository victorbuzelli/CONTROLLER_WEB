# db.py (VERSÃO SIMPLIFICADA)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# O engine não será mais criado aqui diretamente.
# Ele será configurado via app.config no app.py.
# Esta linha será definida MAIS TARDE no app.py
engine = None # Inicializamos como None ou removemos, será setado globalmente pelo app.py

Session = sessionmaker() # A sessão será bindada ao engine mais tarde
Base = declarative_base()