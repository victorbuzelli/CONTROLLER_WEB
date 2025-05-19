from flask import render_template, jsonify, send_file, make_response, request # ADICIONE request AQUI!
from flask_login import login_required, current_user
from datetime import datetime
from io import BytesIO
from googleapiclient import http

@login_required
def listar_arquivos(drive_service, folder_id=None): # Adicione drive_service como argumento
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
                includeItemsFromAllDrives=True,
                supportsAllDrives=True
            ).execute()
            files_and_folders = results.get('files', [])
            print(f"Número de itens retornados pelo Google Drive: {len(files_and_folders)}")
            print(f"Conteúdo da lista de itens: {files_and_folders}")
            return render_template('arquivos.html', documentos=files_and_folders, current_folder_id=parent_folder_id, now=datetime.utcnow())
        except Exception as e:
            print(f"Ocorreu um erro ao acessar o Google Drive: {e}")
            return render_template('arquivos.html', documentos=[], current_folder_id=parent_folder_id, now=datetime.utcnow())
    else:
        return jsonify({'message': 'Serviço do Google Drive não inicializado!'}), 500

@login_required
def download_file(drive_service, file_id): # Adicione drive_service como argumento
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
        if e.resp.status == 404:
            return jsonify({'message': 'Arquivo não encontrado!'}), 404
        elif e.resp.status == 403:
            return jsonify({'message': 'Sem permissão para acessar este arquivo!'}), 403
        else:
            return jsonify({'message': f'Erro ao baixar o arquivo {file_id}'}), 500
    except Exception as e:
        return jsonify({'message': f'Erro ao baixar o arquivo {file_id}'}), 500