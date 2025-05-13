from flask import Blueprint, request, render_template, redirect, jsonify
from flask_login import login_user, current_user, logout_user
from models import User, USUARIOS

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/arquivos') # Se já estiver logado, redireciona

    if request.method == 'POST':
        print("Função de login (POST) foi chamada!")
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"Tentativa de login para o usuário: {username}")
        if username in USUARIOS and USUARIOS[username]['senha'] == password:
            user_id = None
            for i, u in enumerate(USUARIOS.keys()):
                if u == username:
                    user_id = str(i)
                    break
            if user_id is not None:
                user_info = USUARIOS[username]
                user = User(user_id, username, user_info['senha'], user_info['pasta_id'])
                login_user(user)  # Registra o usuário na sessão
                print(f"Login bem-sucedido para: {username}")
                return redirect('/arquivos')
            else:
                print(f"Erro ao obter ID do usuário: {username}")
                return render_template('login.html', error='Erro interno ao logar!')
        else:
            print(f"Falha no login para: {username}")
            return render_template('login.html', error='Credenciais inválidas!')
    else:
        return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect('/auth/login') # Redireciona para a página de login