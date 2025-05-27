import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

    # Use a variável de ambiente DATABASE_URL
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///site.db')

    # Cria o engine do SQLAlchemy.
    # Adicionamos 'connect_args' para definir o 'search_path' para 'public'.
    # Isso garante que o SQLAlchemy crie e procure tabelas no esquema 'public'.
engine = create_engine(
    DATABASE_URL,
    connect_args={
            "options": "-c search_path=public"
        }
)

    # Cria a sessão
Session = sessionmaker(bind=engine)

    # Base para seus modelos declarativos
Base = declarative_base()

    # Lembrete: As classes de modelo (ex: User, Company) NÃO devem ser importadas neste arquivo (db.py).
    # Elas devem ser definidas em 'models.py' e importadas apenas no 'app.py' ou onde forem usadas