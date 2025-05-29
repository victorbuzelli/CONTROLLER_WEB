# db.py (VERSÃO NOVA AJUSTADA)
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Obtém a URL do banco de dados da variável de ambiente SQLALCHEMY_DATABASE_URI
# Use essa variável específica se é o que você tem no Render.
DATABASE_URL = os.environ.get('SQLALCHEMY_DATABASE_URI') # AGORA LÊ SQLALCHEMY_DATABASE_URI

if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    print("AVISO: SQLALCHEMY_DATABASE_URI não definida. Usando SQLite local. ISSO NÃO SERÁ PERSISTENTE NO RENDER!")
    # Apenas para desenvolvimento local. Certifique-se de que essa URL esteja definida no Render.
    engine = create_engine('sqlite:///site.db') 

Session = sessionmaker(bind=engine)
Base = declarative_base()