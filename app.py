import os
import json
import logging
from io import BytesIO
from datetime import datetime

from flask import Flask, request, jsonify, send_file, make_response, render_template, redirect, url_for, flash, current_app, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient import http
from whitenoise import WhiteNoise
from flask_mail import Mail, Message

# Importe seus Blueprints
from auth import auth_bp
from profile_routes import profile_bp
from drive_integration import listar_arquivos as listar_arquivos_func, download_file
from database_utils import load_user
from models import User
from db import engine, Session, Base

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'gesspwfmikqqizim')
# A ordem aqui também é importante: WhiteNoise deve encapsular o app.wsgi_app
app.wsgi_app = WhiteNoise(app.wsgi_app, root=os.path.join(os.path.dirname(__file__), 'static'), prefix="/static/")

# --- INICIALIZAÇÃO DO GOOGLE DRIVE (mantido no topo, antes das rotas) ---
GOOGLE_CREDENTIALS_JSON = os.environ.get('GOOGLE_CREDENTIALS_JSON')
drive_service = None

print(f"--- DEBUG: Verificando GOOGLE_CREDENTIALS_JSON (Início do app.py) ---")
if GOOGLE_CREDENTIALS_JSON:
    print(f"DEBUG: GOOGLE_CREDENTIALS_JSON foi encontrada. Início: {GOOGLE_CREDENTIALS_JSON[:100]}...")
    try:
        creds_info = json.loads(GOOGLE_CREDENTIALS_JSON) # Corrigi para GOOGLE_CREDENTIALS_JSON, se foi um erro de cópia
        print("DEBUG: JSON de credenciais do Google decodificado com sucesso.")
        credentials = service_account.Credentials.from_service_account_info(
            creds_info,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        drive_service = build('drive', 'v3', credentials=credentials)
        print("DEBUG: Serviço do Google Drive construído com sucesso.")
    except json.JSONDecodeError as e:
        print(f"DEBUG: Erro ao decodificar GOOGLE_CREDENTIALS_JSON. O valor não é um JSON válido: {e}")
        print(f"Erro: Falha ao decodificar a variável de ambiente GOOGLE_CREDENTIALS_JSON.")
        drive_service = None
    except Exception as e:
        print(f"DEBUG: Erro geral ao carregar credenciais (fora de JSONDecodeError): {e}")
        print(f"Erro ao carregar as credenciais do Google Drive: {e}")
        drive_service = None
else:
    print("DEBUG: GOOGLE_CREDENTIALS_JSON não foi encontrada (valor é None ou vazio).")
    print("Erro: Variável de ambiente GOOGLE_CREDENTIALS_JSON não encontrada.")
    drive_service = None
print(f"--- FIM DO BLOCO DE DEBUG (Início do app.py) ---")

# --- ROTAS DE ARQUIVOS ESPECÍFICOS (SERVICE WORKER, MANIFEST) DEVEM VIR ANTES DA ROTA '/' ---
# ESTAS DUAS ROTAS SÃO CRÍTICAS PARA O PWA E DEVEM VIR O MAIS CEDO POSSÍVEL APÓS A INSTANCIAÇÃO DO APP!
@app.route('/service-worker.js')
def serve_sw():
    # app.root_path é o diretório onde app.py está.
    # Certifique-se que service-worker.js ESTÁ NESTA PASTA (raiz do projeto)
    return send_from_directory(app.root_path, 'service-worker.js', mimetype='application/javascript')

@app.route('/manifest.json')
def serve_manifest():
    # Assumindo que manifest.json ainda está em 'static/'
    return send_from_directory(os.path.join(app.root_path, 'static'), 'manifest.json', mimetype='application/manifest+json')

@app.route('/.well-known/assetlinks.json') # <--- ROTA ORIGINAL
def serve_assetlinks():
    return send_from_directory(os.path.join(app.root_path, '.well-known'), 'assetlinks.json', mimetype='application/json')


# --- AGORA A ROTA PRINCIPAL '/' PODE VIR ---
@app.route('/')
def index():
    # render_template espera que o arquivo esteja na pasta 'templates/'
    return render_template('index.html') 

# --- O RESTO DO SEU CÓDIGO DO app.py CONTINUA AQUI (sem mudanças de ordem drásticas) ---

@app.route('/delete-account-policy')
def delete_account_policy():
    return render_template('delete_account_policy.html')

# Rota para a Política de Privacidade
@app.route('/privacy-policy')
def privacy_policy():
    """
    Exibe a página da política de privacidade.
    Esta página deve conter o texto gerado por um gerador de políticas de privacidade.
    """
    return render_template('privacy_policy.html')

# --- Configurações do Flask-Mail ---
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
mail_port_str = os.environ.get('MAIL_PORT', '587')
try:
    app.config['MAIL_PORT'] = int(mail_port_str)
except ValueError:
    print(f"DEBUG: MAIL_PORT '{mail_port_str}' não é um número válido. Usando 587 como padrão.")
    app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
mail = Mail(app)

def send_verification_email(user, token, new_email):
    msg = Message('Verifique seu novo endereço de e-mail',
                  sender=app.config.get('MAIL_DEFAULT_SENDER'),
                  recipients=[new_email])
    link = url_for('verify_email', token=token, _external=True)
    msg.body = f'Por favor, clique no link abaixo para verificar seu novo endereço de e-mail:\n\n{link}\n\nSe você não solicitou esta alteração, ignore este e-mail.'
    try:
        mail.send(msg)
        print(f"E-mail de verificação enviado com sucesso para {new_email}")
    except Exception as e:
        flash(f'Erro ao enviar e-mail de verificação: {e}', 'error')
        print(f"Erro ao enviar e-mail de verificação: {e}")
app.send_verification_email = send_verification_email

# --- Configuração do Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.user_loader(load_user)

USUARIO_LOGADO = None

# --- Rotas que exigem login (mantido aqui) ---
@app.route('/arquivos', methods=['GET'])
@login_required
def listar_arquivos_route():
    if drive_service:
        return listar_arquivos_func(drive_service)
    else:
        flash('Erro: Serviço do Google Drive não disponível.', 'error')
        return redirect(url_for('profile.profile'))

@app.route('/download/<file_id>', methods=['GET'])
@login_required
def download_route(file_id):
    if drive_service:
        return download_file(drive_service, file_id)
    else:
        flash('Erro: Serviço do Google Drive não disponível para download.', 'error')
        return redirect(url_for('profile.profile'))

@app.route('/verify_email/<token>')
def verify_email(token):
    local_session = Session()
    try:
        user = local_session.query(User).filter_by(email_token=token).first()
        if user:
            user.email = user.new_email
            user.new_email = None
            user.email_token = None
            local_session.commit()
            flash('Seu e-mail foi verificado e alterado com sucesso!', 'success')
        else:
            flash('Link de verificação inválido ou usuário não encontrado.', 'error')
    except Exception as e:
        local_session.rollback()
        print(f"Erro ao verificar e-mail: {e}")
        flash(f'Ocorreu um erro ao verificar seu e-mail: {e}', 'error')
    finally:
        local_session.close()
    return redirect(url_for('profile.profile'))

# --- Bloco principal de execução (CORREÇÃO FINAL e SINTAXE) ---
if __name__ == '__main__':
    # Inicialize o banco de dados e registre os Blueprints APENAS UMA VEZ
    # e ANTES da chamada app.run()
    Base.metadata.create_all(engine)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    
    # Esta linha app.run() é apenas para testes locais.
    # No Render, ele usa gunicorn ou um servidor WSGI similar.
    # Certifique-se que seu 'Procfile' no Render está configurado corretamente (ex: web: gunicorn app:app)
    app.run(debug=True, port=5000)