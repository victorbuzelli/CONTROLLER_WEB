import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use a variável de ambiente DATABASE_URL
# Esta linha define qual banco de dados será usado.
# No Render, ela pegará o valor de sua variável de ambiente DATABASE_URL.
# Localmente, se a variável não estiver definida, usará 'sqlite:///site.db'.
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///site.db')

# Cria o engine do SQLAlchemy.
# O engine é a interface principal para interagir com o banco de dados.
engine = create_engine(DATABASE_URL)

# Cria a sessão.
# A sessão é o "palco" onde você interage com seus objetos de banco de dados (usuários, empresas, etc.).
Session = sessionmaker(bind=engine)

# Base para seus modelos declarativos.
# Todas as suas classes de modelo (como User, Company) devem herdar desta Base.
# É através desta Base que o SQLAlchemy "descobre" as tabelas a serem criadas.
Base = declarative_base()

# IMPORTANTE:
# As classes de modelo (ex: User, Company) NÃO devem ser importadas neste arquivo (db.py).
# Elas devem ser definidas em 'models.py' e importadas no 'app.py' (ou em outro arquivo principal)
# ANTES da chamada 'Base.metadata.create_all(engine)'.
# A linha 'from .models import User, Company' que causou o erro ANTERIORMENTE
# NÃO DEVE ESTAR AQUI.
