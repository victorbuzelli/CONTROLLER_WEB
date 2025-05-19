import os
import json
import logging
from io import BytesIO
from datetime import datetime

from flask import Blueprint
from flask import Flask, request, jsonify, send_file, make_response, render_template, redirect
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient import http
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from drive_integration import listar_arquivos as listar_arquivos_func, download_file
from flask_mail import Mail, Message # Importe Mail e Message

from auth import auth_bp
from models import User, Base # IMPORTANTE IMPORTAR Base
from profile_routes import profile_bp
from drive_integration import listar_arquivos, download_file
from database_utils import load_user
from db import engine, Session # IMPORTAR DO db.py

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret'
app.config['GOOGLE_CREDENTIALS_FILE'] = 'D:\\\\Documentos\\Desktop\\CONTROLLER WEB\\controller-web-879acc97b4a7.json' # Defina o caminho aqui

# Configurações do Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # SEU SERVIDOR SMTP
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'victorcontroller8@gmail.com'  # SEU E-MAIL
app.config['MAIL_PASSWORD'] = 'Vic@5466'  # SUA SENHA
app.config['MAIL_DEFAULT_SENDER'] = 'victorcontroller8@gmail.com'

mail = Mail(app) # Inicialize o Flask-Mail aqui

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login' # Atualiza o login_view para o blueprint
login_manager.user_loader(load_user) # ALTERE PARA USAR A FUNÇÃO IMPORTADA

# Inicialização do Banco de Dados (já deve existir)
engine = create_engine('sqlite:///site.db')
Session = sessionmaker(bind=engine)
session = Session()
Base.metadata.create_all(engine)

CREDENTIALS_FILE = 'D:\\\\Documentos\\Desktop\\CONTROLLER WEB\\controller-web-879acc97b4a7.json'
drive_service = None
try:
    with open(CREDENTIALS_FILE, 'r') as f:
        creds_info = json.load(f)
    credentials = service_account.Credentials.from_service_account_info(
        creds_info,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    drive_service = build('drive', 'v3', credentials=credentials)
except FileNotFoundError:
    print(f"Erro: Arquivo de credenciais não encontrado em: {CREDENTIALS_FILE}")
except json.JSONDecodeError:
    print(f"Erro: Falha ao decodificar o arquivo JSON de credenciais.")
except Exception as e:
    print(f"Erro ao carregar as credenciais: {e}")

USUARIO_LOGADO = None

@app.route('/')
def index():
    return "Servidor Flask funcionando!"

@app.route('/arquivos', methods=['GET'])
@login_required
def listar_arquivos(folder_id=None):
    return listar_arquivos_func(drive_service, folder_id)

@app.route('/download/<file_id>', methods=['GET'])
@login_required
def download_route(drive_service, file_id): # Passe drive_service
    return download_file(drive_service, file_id) # Passe drive_service

if __name__ == '__main__':
    app.register_blueprint(auth_bp) # Registra o blueprint de autenticação
    app.register_blueprint(profile_bp) # REGISTRA O BLUEPRINT DO PERFIL AQUI!

    with app.app_context():
        try:
            msg = Message("Teste de Envio de E-mail",
                          sender=app.config['MAIL_DEFAULT_SENDER'],
                          recipients=['SEU_ENDERECO_DE_EMAIL@gmail.com']) # Substitua pelo SEU e-mail
            msg.body = "Este é um e-mail de teste enviado diretamente do app.py."
            mail.send(msg)
            print("E-mail de teste enviado com sucesso!")
        except Exception as e:
            print(f"Erro ao enviar e-mail de teste: {e}")

    app.run(debug=True)