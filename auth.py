from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user
from models import User
from db import Session
from werkzeug.security import check_password_hash, generate_password_hash

# Define um Blueprint chamado 'auth'.
# O 'url_prefix='/auth'' significa que todas as rotas definidas neste Blueprint
# terão o prefixo '/auth' na URL final (ex: /auth/login, /auth/register).
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Esta rota lida com o login de usuários.
    - Se o usuário já estiver autenticado, redireciona para a rota 'listar_arquivos_route'.
    - No método POST, tenta autenticar o usuário com base no email e senha.
    - No método GET, simplesmente renderiza o formulário de login.
    """
    # Verifica se o usuário já está logado. Se sim, redireciona para a página de arquivos.
    if current_user.is_authenticated:
        return redirect(url_for('listar_arquivos_route')) # Redireciona para a rota de listagem de arquivos (definida em app.py)

    local_session = Session() # Cria uma nova sessão de banco de dados para esta requisição
    try:
        if request.method == 'POST':
            print("Função de login (POST) foi chamada!") # Log para depuração
            email = request.form.get('username') # Obtém o email/username do formulário
            password = request.form.get('password') # Obtém a senha do formulário
            print(f"Tentativa de login para o usuário: {email}") # Log
            
            # Busca o usuário no banco de dados pelo email
            user = local_session.query(User).filter_by(email=email).first()
            
            if user:
                print(f"Usuário encontrado no banco de dados: {user.email}, ID={user.id}") # Log
                print(f"Senha Hashed no Banco: {user.senha_hash}") # Log (cuidado com logs de senhas em produção)
                
                # Primeira tentativa: verifica se a senha fornecida corresponde ao hash armazenado
                if check_password_hash(user.senha_hash, password):
                    login_user(user) # Faz o login do usuário usando Flask-Login
                    print(f"Login bem-sucedido para: {email}") # Log
                    return redirect(url_for('listar_arquivos_route')) # Redireciona para a página de arquivos

                # Segunda tentativa (compatibilidade): Se a senha no banco não é um hash (texto puro),
                # e corresponde à senha fornecida, atualiza para o hash e faz login.
                # Esta é uma lógica de migração/compatibilidade de senhas.
                elif user.senha_hash == password: # CUIDADO: Isso expõe senhas em texto puro se user.senha_hash não for um hash
                    print(f"Login bem-sucedido (senha texto puro) para: {email}") # Log
                    user.senha_hash = generate_password_hash(password) # Gera o hash da senha
                    local_session.commit() # Salva o novo hash no banco de dados
                    login_user(user) # Faz o login do usuário
                    return redirect(url_for('listar_arquivos_route')) # Redireciona para a página de arquivos
                else:
                    print(f"Falha na verificação da senha para: {email}") # Log
                    return render_template('login.html', error='Credenciais inválidas!') # Renderiza o formulário com erro
            else:
                print(f"Usuário NÃO encontrado no banco de dados com o email: {email}") # Log
                return render_template('login.html', error='Credenciais inválidas!') # Renderiza o formulário com erro
    finally:
        local_session.close() # Garante que a sessão do banco de dados seja fechada

    # Se o método for GET (ou se o POST falhar e não redirecionar), renderiza o formulário de login
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """
    Esta rota lida com o logout do usuário.
    Desloga o usuário usando Flask-Login e redireciona para a página de login.
    """
    logout_user() # Desloga o usuário
    return redirect(url_for('auth.login')) # Redireciona para a página de login (endpoint 'login' dentro do Blueprint 'auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Esta rota lida com o registro de novos usuários.
    - No método POST, tenta criar um novo usuário com as informações fornecidas.
    - No método GET, simplesmente renderiza o formulário de registro.
    """
    local_session = Session() # Cria uma nova sessão de banco de dados
    try:
        if request.method == 'POST':
            email = request.form.get('username') # Obtém o email/username do formulário
            username = request.form.get('username') # Obtém o username (aqui é o mesmo que email)
            password = request.form.get('password') # Obtém a senha
            google_drive_folder_id = request.form['google_drive_folder_id'] # Obtém o ID da pasta do Google Drive
            print(f"Email recebido do formulário: {email}") # Log
            
            # Verifica se o email já existe no banco de dados
            existing_user = local_session.query(User).filter_by(email=email).first()
            if existing_user:
                flash('Este email já está cadastrado.', 'error') # Mensagem de erro
                return render_template('register.html') # Renderiza o formulário de registro novamente

            pasta_id = google_drive_folder_id # Atribui o ID da pasta
            hashed_password = generate_password_hash(password) # Gera o hash da senha
            
            # Cria um novo objeto User
            new_user = User(email=email, username=username, senha_hash=hashed_password, pasta_id=pasta_id)
            local_session.add(new_user) # Adiciona o novo usuário à sessão
            local_session.commit() # Salva as mudanças no banco de dados
            
            flash('Usuário cadastrado com sucesso! Faça o login.', 'success') # Mensagem de sucesso
            return redirect(url_for('auth.login')) # Redireciona para a página de login
    finally:
        local_session.close() # Garante que a sessão do banco de dados seja fechada

    # Se o método for GET, renderiza o formulário de registro
    return render_template('register.html')