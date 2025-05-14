from flask_login import UserMixin
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base, UserMixin):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False)
    username = Column(String(80), unique=True, nullable=False) # Adicionamos o campo username
    senha_hash = Column(String(128), nullable=False)
    pasta_id = Column(String(80), nullable=False)

    def __init__(self, email, username, senha_hash, pasta_id): # Atualizamos o __init__
        self.email = email
        self.username = username
        self.senha_hash = senha_hash
        self.pasta_id = pasta_id

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

engine = create_engine('sqlite:///site.db')
Session = sessionmaker(bind=engine)
session = Session()
Base.metadata.create_all(engine)