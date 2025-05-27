from flask import Flask, render_template, request, redirect, url_for, flash, session
import logging # Importar logging para depuração
from .models import User, Company # Exemplo: SUAS CLASSES DE MODELO AQUI!

# Configuração do logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sua_chave_secreta_padrao')

# ... suas rotas e blueprints aqui ...

# ESTE É O BLOCO CRÍTICO PARA CRIAR AS TABELAS
with app.app_context(): # Garante que estamos no contexto da aplicação Flask
    try:
        logging.info("--- DEBUG: Tentando criar tabelas do banco de dados (Base.metadata.create_all) ---")
        Base.metadata.create_all(engine) # Aqui as tabelas são criadas
        logging.info("--- DEBUG: Tabelas do banco de dados criadas com sucesso ou já existentes. ---")
    except Exception as e:
        logging.error(f"--- ERRO: Falha ao criar tabelas do banco de dados: {e} ---")
        # Adicione um raise aqui se quiser que o app falhe se as tabelas não puderem ser criadas
        # raise