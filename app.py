import os
import json
import logging
from io import BytesIO
from datetime import datetime

# Importações de módulos Flask e outros
from flask import Flask, request, jsonify, send_file, make_response, render_template, redirect, url_for, flash, current_app, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient import http
from whitenoise import WhiteNoise
from flask_mail import Mail, Message

# Importa seus Blueprints. Isso significa que as rotas de auth e profile estão em outros arquivos.
from auth import auth_bp
from profile_routes import profile_bp
from drive_integration import listar_arquivos as listar_arquivos_func, download_file

# IMPORTANTE: Garanta que TODOS os seus modelos (User, Company, etc.) estejam importados aqui
# Isso garante que o SQLAlchemy os "conheça" antes de tentar criar as tabelas.
from models import User # Se tiver outras classes de modelo, importe-as também: , Company, Product
from database_utils import load_user
from db import engine, Session, Base # Importar o que você definiu em db.py

# Configuração básica de logging para depuração
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Inicializa o aplicativo Flask
app = Flask(__name__)
# Configura a chave secreta para segurança de sessão e outras funcionalidades
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'gesspwfmikqqizim')

# Configura o WhiteNoise para servir arquivos estáticos de forma eficiente no ambiente de produção (Render)
# Ele encapsula o WSGI app do Flask e serve arquivos da pasta 'static'.
app.wsgi_app = WhiteNoise(app.wsgi_app, root=os.path.join(os.path.dirname(__file__), 'static'), prefix="/static/")

# --- INICIALIZAÇÃO DO GOOGLE DRIVE ---
# Carrega as credenciais do Google Drive de uma variável de ambiente JSON.
# Isso é crucial para a integração do app com o Drive para listar e baixar arquivos.
GOOGLE_CREDENTIALS_JSON = os.environ.get('GOOGLE_CREDENTIALS_JSON')
drive_service = None

print(f"--- DEBUG: Verificando GOOGLE_CREDENTIALS_JSON (Início do app.py) ---")
if GOOGLE_CREDENTIALS_JSON:
    print(f"DEBUG: GOOGLE_CREDENTIALS_JSON foi encontrada. Início: {GOOGLE_CREDENTIALS_JSON[:100]}...")
    try:
        # Tenta decodificar a string JSON das credenciais
        creds_info = json.loads(GOOGLE_CREDENTIALS_JSON)
        print("DEBUG: JSON de credenciais do Google decodificado com sucesso.")
        # Cria credenciais de serviço a partir das informações e define os escopos de acesso ao Drive (somente leitura)
        credentials = service_account.Credentials.from_service_account_info(
            creds_info,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        # Constrói o serviço do Google Drive API v3
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

# --- ROTAS DE ARQUIVOS ESPECÍFICOS (SERVICE WORKER, MANIFEST) ---
# Estas rotas servem arquivos essenciais para o funcionamento do PWA.
# Elas devem vir antes da rota principal '/' para garantir que sejam encontradas primeiro.
@app.route('/service-worker.js')
def serve_sw():
    # Serve o arquivo service-worker.js, que está na raiz do projeto (app.root_path)
    return send_from_directory(app.root_path, 'service-worker.js', mimetype='application/javascript')

@app.route('/manifest.json')
def serve_manifest():
    # Serve o arquivo manifest.json, que está na pasta 'static/'
    return send_from_directory(os.path.join(app.root_path, 'static'), 'manifest.json', mimetype='application/manifest+json')

@app.route('/.well-known/assetlinks.json')
def serve_assetlinks():
    # Serve o arquivo assetlinks.json, necessário para Trusted Web Activities (TWAs)
    return send_from_directory(os.path.join(app.root_path, '.well-known'), 'assetlinks.json', mimetype='application/json')

# --- ROTA PRINCIPAL ---
@app.route('/')
def index():
    # Renderiza o template 'index.html' para a página inicial do aplicativo
    return render_template('index.html')

# --- ROTAS DE POLÍTICAS ---
@app.route('/delete-account-policy')
def delete_account_policy():
    # Renderiza o template para a política de exclusão de conta
    return render_template('delete_account_policy.html')

@app.route('/privacy-policy')
def privacy_policy():
    # Renderiza o template para a política de privacidade
    return render_template('privacy_policy.html')

# --- Configurações do Flask-Mail ---
# Carrega as configurações de e-mail de variáveis de ambiente para envio de e-mails de verificação
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

# Função para enviar e-mail de verificação (usada no fluxo de alteração de e-mail)
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
# Inicializa o Flask-Login para gerenciar sessões de usuário.
login_manager = LoginManager()
login_manager.init_app(app)
# Define a rota para a qual o usuário será redirecionado se tentar acessar uma página protegida sem estar logado.
# 'auth.login' significa a função 'login' dentro do Blueprint 'auth'.
login_manager.login_view = 'auth.login'
# Define a função para recarregar o usuário a partir do ID na sessão.
login_manager.user_loader(load_user)

USUARIO_LOGADO = None # Esta variável global pode não ser necessária se você usar current_user do Flask-Login.

# --- REGISTRO DOS BLUEPRINTS ---
# ESTE É O PONTO CRÍTICO. Estas linhas DEVEM estar fora do if __name__ == '__main__':
# para garantir que os Blueprints sejam registrados quando o Gunicorn (ou outro servidor WSGI)
# importa o aplicativo no ambiente de produção (Render).
print("--- DEBUG: Antes de registrar auth_bp em app.py ---")
app.register_blueprint(auth_bp)
print("--- DEBUG: auth_bp registrado com sucesso em app.py ---")

print("--- DEBUG: Antes de registrar profile_bp em app.py ---")
app.register_blueprint(profile_bp)
print("--- DEBUG: profile_bp registrado com sucesso em app.py ---")


# --- INICIALIZAÇÃO DO BANCO DE DADOS E CRIAÇÃO DE TABELAS ---
# MOVIDO PARA DENTRO DE app.app_context() e com tratamento de erro
# para garantir que seja executado no contexto correto e logue falhas.
with app.app_context():
    try:
        logging.info("--- DEBUG: Tentando criar tabelas do banco de dados (Base.metadata.create_all) ---")
        Base.metadata.create_all(engine) # Aqui as tabelas são criadas
        logging.info("--- DEBUG: Tabelas do banco de dados criadas com sucesso ou já existentes. ---")
    except Exception as e:
        logging.error(f"--- ERRO: Falha ao criar tabelas do banco de dados: {e} ---")
        # Dependendo da severidade, você pode querer que o app falhe se as tabelas não forem criadas
        # raise # Descomente esta linha se quiser que o deploy falhe em caso de erro na criação das tabelas


# --- Rotas que exigem login (Protegidas por @login_required) ---
@app.route('/arquivos', methods=['GET'])
@login_required # Esta rota só pode ser acessada por usuários logados.
def listar_arquivos_route():
    if drive_service:
        return listar_arquivos_func(drive_service)
    else:
        flash('Erro: Serviço do Google Drive não disponível.', 'error')
        return redirect(url_for('profile.profile')) # Redireciona para o perfil se o Drive não estiver disponível

@app.route('/download/<file_id>', methods=['GET'])
@login_required # Esta rota só pode ser acessada por usuários logados.
def download_route(file_id):
    if drive_service:
        return download_file(drive_service, file_id)
    else:
        flash('Erro: Serviço do Google Drive não disponível para download.', 'error')
        return redirect(url_for('profile.profile')) # Redireciona para o perfil se o Drive não estiver disponível

@app.route('/verify_email/<token>')
def verify_email(token):
    # Rota para verificar e-mail (usada no fluxo de alteração de e-mail)
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

# --- Bloco principal de execução (apenas para execução local) ---
if __name__ == '__main__':
    # A linha Base.metadata.create_all(engine) FOI REMOVIDA DAQUI.
    # Ela foi movida para o topo do script (fora do if __name__) para ser executada sempre.
    
    # Esta linha app.run() é usada apenas para testes locais.
    # No ambiente de produção (Render), o servidor WSGI (como Gunicorn) gerencia a execução do aplicativo.
    # Certifique-se que seu 'Procfile' no Render está configurado corretamente (ex: web: gunicorn app:app)
    app.run(debug=True, port=5000)