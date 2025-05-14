from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user
from models import User, session
from flask import flash

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('listar_arquivos')) #redireciona para LISTAR ARQUIVOS

    if request.method == 'POST':
        print("Função de login (POST) foi chamada!")
        email = request.form.get('username') # Agora usamos o email como nome de usuário
        password = request.form.get('password')
        print(f"Tentativa de login para o usuário: {email}")
        user = session.query(User).filter_by(email=email).first()
        if user and user.senha_hash == password: # Temporariamente comparando senha em texto puro
            login_user(user)  # Registra o usuário na sessão
            print(f"Login bem-sucedido para: {email}")
            return redirect(url_for('listar_arquivos'))
        else:
            print(f"Falha no login para: {email}")
            return render_template('login.html', error='Credenciais inválidas!')
    else:
        return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect('/auth/login') # Redireciona para a página de login

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('username') # Agora usamos 'username' para o email
        username = request.form.get('username') # Pegamos o nome de usuário do formulário
        password = request.form.get('password')
        google_drive_folder_id = request.form['google_drive_folder_id']
        print(f"Email recebido do formulário: {email}")
        existing_user = session.query(User).filter_by(email=email).first()
        if existing_user:
            flash('Este email já está cadastrado.', 'error')
            return render_template('register.html')

        pasta_id = google_drive_folder_id  # ADICIONE ESTA LINHA
        new_user = User(email=email, username=username, senha_hash=password, pasta_id=pasta_id)
        session.add(new_user)
        session.commit()
        flash('Usuário cadastrado com sucesso! Faça o login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')