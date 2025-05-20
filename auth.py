from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user
from models import User
from db import Session
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('listar_arquivos_route')) # CORRIGIDO AQUI

    local_session = Session()
    try:
        if request.method == 'POST':
            print("Função de login (POST) foi chamada!")
            email = request.form.get('username')
            password = request.form.get('password')
            print(f"Tentativa de login para o usuário: {email}")
            user = local_session.query(User).filter_by(email=email).first()
            if user:
                print(f"Usuário encontrado no banco de dados: {user.email}, ID={user.id}")
                print(f"Senha Hashed no Banco: {user.senha_hash}")
                if check_password_hash(user.senha_hash, password):
                    login_user(user)
                    print(f"Login bem-sucedido para: {email}")
                    return redirect(url_for('listar_arquivos_route')) # CORRIGIDO AQUI
                elif user.senha_hash == password:
                    print(f"Login bem-sucedido (senha texto puro) para: {email}")
                    user.senha_hash = generate_password_hash(password)
                    local_session.commit()
                    login_user(user)
                    return redirect(url_for('listar_arquivos_route')) # CORRIGIDO AQUI
                else:
                    print(f"Falha na verificação da senha para: {email}")
                    return render_template('login.html', error='Credenciais inválidas!')
            else:
                print(f"Usuário NÃO encontrado no banco de dados com o email: {email}")
                return render_template('login.html', error='Credenciais inválidas!')
    finally:
        local_session.close()

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    local_session = Session()
    try:
        if request.method == 'POST':
            email = request.form.get('username')
            username = request.form.get('username')
            password = request.form.get('password')
            google_drive_folder_id = request.form['google_drive_folder_id']
            print(f"Email recebido do formulário: {email}")
            existing_user = local_session.query(User).filter_by(email=email).first()
            if existing_user:
                flash('Este email já está cadastrado.', 'error')
                return render_template('register.html')

            pasta_id = google_drive_folder_id
            hashed_password = generate_password_hash(password)
            new_user = User(email=email, username=username, senha_hash=hashed_password, pasta_id=pasta_id)
            local_session.add(new_user)
            local_session.commit()
            flash('Usuário cadastrado com sucesso! Faça o login.', 'success')
            return redirect(url_for('auth.login'))
    finally:
        local_session.close()

    return render_template('register.html')