# db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
engine = create_engine('sqlite:///site.db') # Substitua pela sua URL de banco de dados
Session = sessionmaker(bind=engine)

# NÃO crie uma instância de 'session' aqui.
# Em vez disso, cada rota ou função que precisar de uma sessão
# criará uma usando 'local_session = Session()' e a fechará com 'local_session.close()'.
# Isso evita problemas de thread safety e gerenciamento de conexão.