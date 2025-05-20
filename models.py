# models.py

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin

Base = declarative_base()

class User(Base, UserMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False)
    username = Column(String(80), unique=True, nullable=False) # Adicionei nullable=False se ainda não tiver
    senha_hash = Column(String(128), nullable=False)
    pasta_id = Column(String(255), nullable=True) # ID da pasta do Google Drive
    new_email = Column(String(120), nullable=True)
    email_token = Column(String(255), nullable=True)
    # Novo campo para a foto de perfil
    profile_image = Column(String(255), nullable=True, default='default_profile.png') # Valor padrão para novas contas

    def __repr__(self):
        return f'<User {self.username}>'

    # get_id() é necessário para Flask-Login, retorna o ID do usuário como string
    def get_id(self):
        return str(self.id)