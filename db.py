from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
engine = create_engine('sqlite:///site.db')  # Substitua pela sua URL de banco de dados
Session = sessionmaker(bind=engine)