import os
import json
import logging
from io import BytesIO
from datetime import datetime

# Garanta que todas as importações necessárias do Flask estejam aqui
from flask import Flask, request, jsonify, send_file, make_response, render_template, redirect, url_for, flash, current_app
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient import http

from flask_mail import Mail, Message

from auth import auth_bp
from profile_routes import profile_bp
from drive_integration import listar_arquivos as listar_arquivos_func, download_file
from database_utils import load_user
from models import User
from db import engine, Session, Base

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sua_chave_secreta_de_fallback_para_desenvolvimento_local')
# A parte ', 'sua_chave_secreta_de_fallback_para_desenvolvimento_local'' é OPCIONAL
# e serve APENAS para quando você roda o app LOCALMENTE e não tem a variável de ambiente definida.
# Em produção no Render, ele usará a variável de ambiente que você definiu.
GOOGLE_CREDENTIALS_JSON = os.environ.get('GOOGLE_CREDENTIALS_JSON')
drive_service = None

if GOOGLE_CREDENTIALS_JSON:
    try:
        creds_info = json.loads(GOOGLE_CREDENTIALS_JSON)
        credentials = service_account.Credentials.from_service_account_info(
            creds_info,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        drive_service = build('drive', 'v3', credentials=credentials)
    except json.JSONDecodeError:
        print(f"Erro: Falha ao decodificar a variável de ambiente GOOGLE_CREDENTIALS_JSON.")
    except Exception as e:
        print(f"Erro ao carregar as credenciais do Google Drive: {e}")
else:
    print("Erro: Variável de ambiente GOOGLE_CREDENTIALS_JSON não encontrada.")

# Configurações do Flask-Mail
# Configurações do Flask-Mail
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT')) # Converte para int
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS').lower() == 'true' # Converte para booleano
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL').lower() == 'true' # Converte para booleano
# -> Adicione estas duas linhas abaixo <-
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER') # Esta já estava lá, mas mantenha-a

mail = Mail(app) # Inicialize o Flask-Mail aqui

# Função de envio de e-mail
# Remova 'global mail'
def send_verification_email(user, token, new_email):
    # Usamos 'app.config.get' pois 'app' é globalmente acessível neste escopo do módulo
    msg = Message('Verifique seu novo endereço de e-mail',
                  sender=app.config.get('MAIL_DEFAULT_SENDER'), # Use 'app.config', não 'current_app.config'
                  recipients=[new_email])
    link = url_for('verify_email', token=token, _external=True)
    msg.body = f'Por favor, clique no link abaixo para verificar seu novo endereço de e-mail:\n\n{link}\n\nSe você não solicitou esta alteração, ignore este e-mail.'
    try:
        # A instância 'mail' já está disponível globalmente no módulo app.py
        mail.send(msg) # Use a variável 'mail' diretamente
    except Exception as e:
        flash(f'Erro ao enviar e-mail de verificação: {e}', 'error')
        print(f"Erro ao enviar e-mail de verificação: {e}")

# Anexa a função send_verification_email ao objeto 'app'
app.send_verification_email = send_verification_email


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.user_loader(load_user)

USUARIO_LOGADO = None

@app.route('/')
def index():
    return "Servidor Flask funcionando!"

@app.route('/arquivos', methods=['GET'])
@login_required
def listar_arquivos_route():
    return listar_arquivos_func(drive_service)

@app.route('/download/<file_id>', methods=['GET'])
@login_required
def download_route(file_id):
    return download_file(drive_service, file_id)

@app.route('/verify_email/<token>')
def verify_email(token):
    local_session = Session()
    try:
        user = local_session.query(User).filter_by(email_token=token).first()

        if user:
            if user.email_token == token:
                user.email = user.new_email
                user.new_email = None
                user.email_token = None
                local_session.commit()
                flash('Seu e-mail foi verificado e alterado com sucesso!', 'success')
            else:
                flash('Link de verificação inválido.', 'error')
        else:
            flash('Link de verificação inválido ou usuário não encontrado.', 'error')
    finally:
        local_session.close()

    return redirect(url_for('profile.profile'))

# Bloco principal de execução (com identação e sem duplicação)
if __name__ == '__main__':
    # Cria as tabelas se não existirem
    Base.metadata.create_all(engine)

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)

    # Bloco de teste de e-mail (opcional)
    '''with app.app_context():
        try:
            msg = Message("Teste de Envio de E-mail (Inicialização)",
                          sender=app.config['MAIL_DEFAULT_SENDER'],
                          recipients=['victorcontroller8@gmail.com'])
            msg.body = "Este é um e-mail de teste enviado durante a inicialização do app.py."
            mail.send(msg)
            print("E-mail de teste de inicialização enviado com sucesso!")
        except Exception as e:
            print(f"Erro ao enviar e-mail de teste de inicialização: {e}")'''

    app.run(debug=True, port=5000)