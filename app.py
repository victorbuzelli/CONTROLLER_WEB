import json
from flask import Flask, request, jsonify, send_file, make_response
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient import http


app = Flask(__name__)

@app.route('/')
def index():
    return "Servidor Flask funcionando!"

# Definição das suas variáveis globais
USUARIOS = {
    'comercialuiza@gmail.com': {'senha': '33241990', 'pasta_id': '17BhKhWYRF45ygQevd-tv5AdSSztGD9yO'},
    'andersonbuzelli01@gmail.com': {'senha': '33241990', 'pasta_id': '1wjDMahSNCtCFhk6f5Z1LQEE-_7CkVjQV'}
    # Adicione mais clientes de teste conforme necessário
}

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

# Definição das suas rotas e funções
@app.route('/login', methods=['POST'])
def login():
    global USUARIO_LOGADO
    print("Função de login foi chamada!")
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    print(f"Tentativa de login para o usuário: {username}")
    if username in USUARIOS and USUARIOS[username]['senha'] == password:
        USUARIO_LOGADO = username
        print(f"Login bem-sucedido para: {username}")
        return jsonify({'message': 'Login bem-sucedido!', 'username': username}), 200
    else:
        print(f"Falha no login para: {username}")
        return jsonify({'message': 'Credenciais inválidas!'}), 401

@app.route('/arquivos', methods=['GET'])
def listar_arquivos():
    print(f"Usuário logado ao acessar /arquivos: {USUARIO_LOGADO}")
    print(f"Valor de USUARIO_LOGADO: '{USUARIO_LOGADO}'")
    print(f"Conteúdo de USUARIOS: {USUARIOS}")
    if not USUARIO_LOGADO:
        return jsonify({'message': 'Usuário não autenticado!'}), 401
    user_info = USUARIOS.get(USUARIO_LOGADO)
    if not user_info or 'pasta_id' not in user_info:
        return jsonify({'message': 'Pasta do usuário não encontrada!'}), 404
    pasta_id = user_info['pasta_id']
    print(f"ID da pasta do usuário: {pasta_id}")  # Adicione esta linha
    query = f"'{pasta_id}' in parents and trashed = false"
    print(f"Query para o Google Drive: {query}")  # Adicione esta linha
    if drive_service:
        try:
            results = drive_service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime)"
            ).execute()
            files = results.get('files', [])
            return jsonify({'arquivos': files}), 200
        except Exception as e:
            print(f"Ocorreu um erro ao acessar o Google Drive: {e}")
            return jsonify({'message': 'Erro ao acessar o Google Drive!'}), 500
    else:
        return jsonify({'message': 'Serviço do Google Drive não inicializado!'}), 500
    
@app.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    if not USUARIO_LOGADO:
        return jsonify({'message': 'Usuário não autenticado!'}), 401

    if not drive_service:
        return jsonify({'message': 'Serviço do Google Drive não inicializado!'}), 500

    try:
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

    except Exception as e:
        print(f"Ocorreu um erro ao baixar o arquivo {file_id}: {e}")
        return jsonify({'message': f'Erro ao baixar o arquivo {file_id}'}), 500
    
if __name__ == '__main__':
    app.run(debug=True)