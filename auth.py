# Nome do arquivo: auth.py
# Autor: Vito Buzzella
# Data: 26/05/2025

from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user
from models import User
from db import Session
from werkzeug.security import check_password_hash, generate_password_hash
import logging

# Configuração de logging para depuração específica do auth.py
auth_logger = logging.getLogger(__name__)
auth_logger.setLevel(logging.INFO)
# Adicione um handler se não estiver usando o basicConfig global do app.py
# handler = logging.StreamHandler()
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
# auth_logger.addHandler(handler)


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
    auth_logger.info("Acessando a rota /auth/login")

    # Verifica se o usuário já está logado. Se sim, redireciona para a página de arquivos.
    if current_user.is_authenticated:
        auth_logger.info(f"Usuário {current_user.email} já autenticado. Redirecionando para listar_arquivos_route.")
        return redirect(url_for('listar_arquivos_route')) # Redireciona para a rota de listagem de arquivos (definida em app.py)

    local_session = Session() # Cria uma nova sessão de banco de dados para esta requisição
    try:
        if request.method == 'POST':
            auth_logger.info("Função de login (POST) foi chamada!") # Log para depuração
            email = request.form.get('username') # Obtém o email/username do formulário
            password = request.form.get('password') # Obtém a senha do formulário
            auth_logger.info(f"Tentativa de login para o usuário: {email}") # Log
            
            # Busca o usuário no banco de dados pelo email
            user = local_session.query(User).filter_by(email=email).first()
            
            if user:
                auth_logger.info(f"Usuário encontrado no banco de dados: {user.email}, ID={user.id}") # Log
                # auth_logger.info(f"Senha Hashed no Banco: {user.senha_hash}") # Log (cuidado com logs de senhas em produção)
                
                # Primeira tentativa: verifica se a senha fornecida corresponde ao hash armazenado
                if check_password_hash(user.senha_hash, password):
                    login_user(user) # Faz o login do usuário usando Flask-Login
                    auth_logger.info(f"Login bem-sucedido para: {email}") # Log
                    flash('Login realizado com sucesso!', 'success')
                    return redirect(url_for('listar_arquivos_route')) # Redireciona para a página de arquivos

                # Segunda tentativa (compatibilidade): Se a senha no banco não é um hash (texto puro),
                # e corresponde à senha fornecida, atualiza para o hash e faz login.
                # Esta é uma lógica de migração/compatibilidade de senhas.
                # CUIDADO: Esta parte do código deve ser removida após a migração de todas as senhas.
                elif user.senha_hash == password: 
                    auth_logger.info(f"Login bem-sucedido (senha texto puro detectada) para: {email}. Atualizando para hash.") # Log
                    user.senha_hash = generate_password_hash(password) # Gera o hash da senha
                    local_session.commit() # Salva o novo hash no banco de dados
                    login_user(user) # Faz o login do usuário
                    flash('Login realizado com sucesso! Sua senha foi atualizada para um formato mais seguro.', 'success')
                    return redirect(url_for('listar_arquivos_route')) # Redireciona para a página de arquivos
                else:
                    auth_logger.warning(f"Falha na verificação da senha para: {email}") # Log
                    flash('Credenciais inválidas!', 'error') # Mensagem de erro para o usuário
                    return render_template('login.html', error='Credenciais inválidas!') # Renderiza o formulário com erro
            else:
                auth_logger.warning(f"Usuário NÃO encontrado no banco de dados com o email: {email}") # Log
                flash('Credenciais inválidas!', 'error') # Mensagem de erro para o usuário
                return render_template('login.html', error='Credenciais inválidas!') # Renderiza o formulário com erro
        
        auth_logger.info("Método GET para /auth/login. Renderizando formulário.")
        return render_template('login.html') # Se o método for GET, renderiza o formulário de login
    except Exception as e:
        local_session.rollback() # Em caso de erro, desfaz as operações do banco de dados
        auth_logger.error(f"Erro inesperado na rota /auth/login: {e}", exc_info=True) # Log completo do erro
        flash(f'Ocorreu um erro no servidor. Tente novamente mais tarde. Detalhes: {e}', 'error') # Mensagem genérica para o usuário
        return render_template('login.html', error='Ocorreu um erro no servidor.') # Renderiza com erro
    finally:
        local_session.close() # Garante que a sessão do banco de dados seja fechada

@auth_bp.route('/logout')
def logout():
    """
    Esta rota lida com o logout do usuário.
    Desloga o usuário usando Flask-Login e redireciona para a página de login.
    """
    auth_logger.info(f"Usuário {current_user.email} está fazendo logout.")
    logout_user() # Desloga o usuário
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('auth.login')) # Redireciona para a página de login (endpoint 'login' dentro do Blueprint 'auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Esta rota lida com o registro de novos usuários.
    - No método POST, tenta criar um novo usuário com as informações fornecidas.
    - No método GET, simplesmente renderiza o formulário de registro.
    """
    auth_logger.info("Acessando a rota /auth/register")
    local_session = Session() # Cria uma nova sessão de banco de dados
    try:
        if request.method == 'POST':
            email = request.form.get('username') # Obtém o email/username do formulário
            username = request.form.get('username') # Obtém o username (aqui é o mesmo que email)
            password = request.form.get('password') # Obtém a senha
            google_drive_folder_id = request.form.get('google_drive_folder_id') # Obtém o ID da pasta do Google Drive
            auth_logger.info(f"Tentativa de registro para o email: {email}") # Log
            
            # Verifica se o email já existe no banco de dados
            existing_user = local_session.query(User).filter_by(email=email).first()
            if existing_user:
                auth_logger.warning(f"Tentativa de registro com email já existente: {email}")
                flash('Este email já está cadastrado.', 'error') # Mensagem de erro
                return render_template('register.html') # Renderiza o formulário de registro novamente

            pasta_id = google_drive_folder_id # Atribui o ID da pasta
            hashed_password = generate_password_hash(password) # Gera o hash da senha
            
            # Cria um novo objeto User
            new_user = User(email=email, username=username, senha_hash=hashed_password, pasta_id=pasta_id)
            local_session.add(new_user) # Adiciona o novo usuário à sessão
            local_session.commit() # Salva as mudanças no banco de dados
            
            auth_logger.info(f"Usuário {email} cadastrado com sucesso!")
            flash('Usuário cadastrado com sucesso! Faça o login.', 'success') # Mensagem de sucesso
            return redirect(url_for('auth.login')) # Redireciona para a página de login
        
        auth_logger.info("Método GET para /auth/register. Renderizando formulário.")
        return render_template('register.html') # Se o método for GET, renderiza o formulário de registro
    except Exception as e:
        local_session.rollback() # Em caso de erro, desfaz as operações do banco de dados
        auth_logger.error(f"Erro inesperado na rota /auth/register: {e}", exc_info=True) # Log completo do erro
        flash(f'Ocorreu um erro ao tentar cadastrar. Tente novamente mais tarde. Detalhes: {e}', 'error')
        return render_template('register.html', error='Ocorreu um erro ao tentar cadastrar.')
    finally:
        local_session.close() # Garante que a sessão do banco de dados seja fechada