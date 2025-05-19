from flask_login import UserMixin
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    senha_hash = Column(String(128), nullable=False)
    pasta_id = Column(String(255))
    email_token = Column(String(255), unique=True) # Nova coluna para o token
    new_email = Column(String(100)) # Nova coluna para o novo e-mail

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"

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