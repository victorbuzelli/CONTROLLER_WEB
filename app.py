import os
import json
import logging
from io import BytesIO

from flask import Flask, request, jsonify, send_file, make_response, render_template, redirect
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient import http

from auth import auth_bp
from models import User

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login' # Atualiza o login_view para o blueprint

engine = create_engine('sqlite:///site.db') # Substitua pela sua URL de banco de dados
Session = sessionmaker(bind=engine)

@login_manager.user_loader
def load_user(user_id):
    with Session() as session:
        user = session.query(User).get(int(user_id))
        return user

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

'''@app.route('/arquivos', methods=['GET'])'''
'''@login_required
def listar_arquivos():
    print(f"Usuário logado ao acessar /arquivos: {current_user.username}")
    print(f"ID da pasta do usuário: {current_user.pasta_id}")
    query = f"'{current_user.pasta_id}' in parents and trashed = false"
    if drive_service:
        try:
            results = drive_service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime)"
            ).execute()
            files = results.get('files', [])
            return render_template('arquivos.html', arquivos=files) # Renderiza o template
        except Exception as e:
            print(f"Ocorreu um erro ao acessar o Google Drive: {e}")
            return render_template('arquivos.html', arquivos=files)
    else:
        return jsonify({'message': 'Serviço do Google Drive não inicializado!'}), 500'''

@app.route('/arquivos', methods=['GET'])
@login_required
def listar_arquivos(folder_id=None):
    print(f"Usuário logado ao acessar /arquivos: {current_user.username}")
    base_folder_id = current_user.pasta_id
    parent_folder_id = request.args.get('folder_id', base_folder_id)

    print(f"ID da pasta atual: {parent_folder_id}")
    query = f"'{parent_folder_id}' in parents and trashed = false"
    print(f"Consulta enviada para o Google Drive: {query}")
    files_and_folders = []

    if drive_service:
        try:
            results = drive_service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType)",
                includeItemsFromAllDrives=True, # ADICIONE ESTE PARÂMETRO
                supportsAllDrives=True       # ADICIONE ESTE PARÂMETRO
            ).execute()
            files_and_folders = results.get('files', [])
            print(f"Número de itens retornados pelo Google Drive: {len(files_and_folders)}")
            print(f"Conteúdo da lista de itens: {files_and_folders}")
            return render_template('arquivos.html', documentos=files_and_folders, current_folder_id=parent_folder_id)
        except Exception as e:
            print(f"Ocorreu um erro ao acessar o Google Drive: {e}")
            return render_template('arquivos.html', documentos=[], current_folder_id=parent_folder_id)
    else:
        return jsonify({'message': 'Serviço do Google Drive não inicializado!'}), 500
    
@app.route('/download/<file_id>', methods=['GET'])
@login_required
def download_file(file_id):
    if not drive_service:
        return jsonify({'message': 'Serviço do Google Drive não inicializado!'}), 500

    try:
        response = None  # Inicialize response DENTRO do try
        # Obter informações sobre o arquivo para definir o nome e tipo MIME
        file_info = drive_service.files().get(fileId=file_id, fields='name, mimeType').execute()
        file_name = file_info.get('name', 'arquivo')
        mime_type = file_info.get('mimeType', 'application/octet-stream')

        # Obter o conteúdo do arquivo do Google Drive
        request = drive_service.files().get_media(fileId=file_id)
        fh = BytesIO()
        downloader = http.MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download progress {int(status.progress() * 100)}%")

        fh.seek(0)

        # Preparar a resposta para download
        response = make_response(send_file(
            fh,
            mimetype=mime_type,
            as_attachment=True,
            download_name=file_name
        ))
        response.headers['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response

    except http.HttpError as e:
        print(f"*** ERRO HTTP CAPTURADO: {e} ***")
        app.logger.error(f"Erro HTTP ao baixar o arquivo {file_id}: {e}")
        if e.resp.status == 404:
            return jsonify({'message': 'Arquivo não encontrado!'}), 404
        elif e.resp.status == 403:
            return jsonify({'message': 'Sem permissão para acessar este arquivo!'}), 403
        else:
            return jsonify({'message': f'Erro ao baixar o arquivo {file_id}'}), 500
    except Exception as e:
        app.logger.error(f"Ocorreu um erro inesperado ao baixar o arquivo {file_id}: {e}")
        return jsonify({'message': f'Erro ao baixar o arquivo {file_id}'}), 500

if __name__ == '__main__':
    app.register_blueprint(auth_bp) # Registra o blueprint
    app.run(debug=True)