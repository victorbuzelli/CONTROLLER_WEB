# profile_routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import login_required, current_user
from models import User
from db import Session
from werkzeug.security import check_password_hash, generate_password_hash
import re
import secrets
import os
from werkzeug.utils import secure_filename # Para segurança ao salvar nomes de arquivos

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

# Configuração para upload de arquivos
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'profile_pics')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Garante que a pasta de uploads exista
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@profile_bp.route('/')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@profile_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    local_session = Session()
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        user = local_session.query(User).get(current_user.id)

        if not user:
            flash('Usuário não encontrado.', 'error')
            return redirect(url_for('profile.profile'))

        if check_password_hash(user.senha_hash, current_password): # Usando check_password_hash
            if new_password == confirm_password:
                if len(new_password) >= 6:
                    user.senha_hash = generate_password_hash(new_password) # Gerar hash para a nova senha
                    local_session.commit()
                    flash('Senha alterada com sucesso!', 'success')
                    return redirect(url_for('profile.profile'))
                else:
                    flash('A nova senha deve ter pelo menos 6 caracteres.', 'error')
            else:
                flash('A nova senha e a confirmação não coincidem.', 'error')
        else:
            flash('Senha atual incorreta.', 'error')
    finally:
        local_session.close()

    return redirect(url_for('profile.profile'))

@profile_bp.route('/change_email', methods=['POST'])
@login_required
def change_email():
    local_session = Session()
    try:
        new_email = request.form.get('new_email')
        confirm_new_email = request.form.get('confirm_new_email')

        user = local_session.query(User).get(current_user.id)

        if not user:
            flash('Usuário não encontrado.', 'error')
            return redirect(url_for('profile.profile'))

        if new_email == confirm_new_email:
            if re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
                existing_user = local_session.query(User).filter(User.email == new_email, User.id != user.id).first()
                if existing_user:
                    flash('Este e-mail já está cadastrado por outro usuário.', 'error')
                else:
                    token = secrets.token_urlsafe(32)
                    user.new_email = new_email
                    user.email_token = token
                    local_session.commit()

                    current_app.send_verification_email(user, token, new_email)

                    flash('Um link de verificação foi enviado para o seu novo e-mail.', 'info')
                    return redirect(url_for('profile.profile'))
            else:
                flash('Formato de e-mail inválido.', 'error')
        else:
            flash('O novo e-mail e a confirmação não coincidem.', 'error')
    finally:
        local_session.close()

    return redirect(url_for('profile.profile'))

# NOVA ROTA: Atualizar Nome de Usuário
@profile_bp.route('/change_username', methods=['POST'])
@login_required
def change_username():
    local_session = Session()
    try:
        new_username = request.form.get('new_username')

        user = local_session.query(User).get(current_user.id)

        if not user:
            flash('Usuário não encontrado.', 'error')
            return redirect(url_for('profile.profile'))

        if new_username and new_username != user.username:
            existing_user = local_session.query(User).filter_by(username=new_username).first()
            if existing_user:
                flash('Este nome de usuário já está em uso.', 'error')
            else:
                user.username = new_username
                local_session.commit()
                flash('Nome de usuário alterado com sucesso!', 'success')
        else:
            flash('O novo nome de usuário não pode ser vazio ou igual ao atual.', 'error')
    finally:
        local_session.close()

    return redirect(url_for('profile.profile'))

# NOVA ROTA: Upload de Foto de Perfil
@profile_bp.route('/upload_profile_pic', methods=['POST'])
@login_required
def upload_profile_pic():
    local_session = Session()
    try:
        # Verifica se o request.files tem a parte 'profile_pic'
        if 'profile_pic' not in request.files:
            flash('Nenhuma parte de arquivo na requisição.', 'error')
            return redirect(url_for('profile.profile'))

        file = request.files['profile_pic']

        # Se o usuário não selecionar um arquivo, o navegador envia um arquivo vazio
        if file.filename == '':
            flash('Nenhum arquivo selecionado.', 'error')
            return redirect(url_for('profile.profile'))

        if file and allowed_file(file.filename):
            filename = secure_filename(f"{current_user.id}_{file.filename}") # Garante nome único por usuário
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            user = local_session.query(User).get(current_user.id)
            if user:
                # Remove a imagem antiga se existir e não for a padrão
                if user.profile_image and user.profile_image != 'default_profile.png':
                    old_filepath = os.path.join(UPLOAD_FOLDER, user.profile_image)
                    if os.path.exists(old_filepath):
                        os.remove(old_filepath)

                user.profile_image = filename # Salva apenas o nome do arquivo no BD
                local_session.commit()
                flash('Foto de perfil atualizada com sucesso!', 'success')
            else:
                flash('Usuário não encontrado.', 'error')
        else:
            flash('Tipo de arquivo não permitido. Apenas PNG, JPG, JPEG, GIF são aceitos.', 'error')
    finally:
        local_session.close()

    return redirect(url_for('profile.profile'))

# Rota para servir imagens de perfil (necessário para exibir a imagem)
# Isso permite que você acesse a imagem via /profile/profile_pics/nome_da_imagem.png
@profile_bp.route('/profile_pics/<filename>')
def serve_profile_pic(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)