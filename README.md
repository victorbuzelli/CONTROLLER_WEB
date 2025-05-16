# CONTROLLER_WEB
It is a app to a accountability office where clients can access their documents through it. 
# Controller Web - Acesso Simplificado ao Google Drive

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-%23000000.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)

## Descrição

O Controller Web é uma aplicação web simples construída com Python e Flask que permite aos usuários autenticados visualizar os arquivos e pastas de uma pasta específica do Google Drive e baixar arquivos diretamente pelo navegador. O objetivo principal é fornecer uma interface web intuitiva e fácil de usar para acessar e gerenciar documentos importantes armazenados no Google Drive.

## Funcionalidades Principais

* **Autenticação de Usuários:** Sistema de login para garantir o acesso seguro aos dados.
* **Listagem de Arquivos e Pastas:** Exibe os arquivos e pastas contidos na pasta do Google Drive associada ao usuário logado.
* **Download de Arquivos:** Permite o download de arquivos do Google Drive diretamente através do navegador.
* **Navegação em Pastas:** Capacidade de navegar pelas subpastas dentro da pasta principal do usuário.
* **Integração com Google Drive API:** Utiliza a API do Google Drive para acessar e manipular os arquivos de forma segura.

## Pré-requisitos

Antes de executar o Controller Web, você precisará ter o seguinte instalado:

* **Python 3.x:** Certifique-se de ter o Python instalado em sua máquina. Você pode baixá-lo em [https://www.python.org/downloads/](https://www.python.org/downloads/).
* **pip:** O gerenciador de pacotes do Python, geralmente instalado com o Python.
* **Credenciais da API do Google Drive:** Você precisará criar um projeto no Google Cloud Platform e gerar um arquivo de credenciais JSON para autenticar sua aplicação com a API do Google Drive. Siga a [documentação oficial do Google Cloud](https://developers.google.com/drive/api/v3/quickstart/python) para obter as credenciais. **Certifique-se de manter este arquivo em um local seguro e não o compartilhe publicamente.**

## Instalação

Siga estes passos para configurar e executar o Controller Web:

1.  **Clone o Repositório (se você já tiver o código no GitHub):**
    ```bash
    git clone <URL_DO_SEU_REPOSITÓRIO>
    cd controller-web
    ```

2.  **Crie um Ambiente Virtual:**
    ```bash
    python -m venv venv
    ```

3.  **Ative o Ambiente Virtual:**
    * **No Windows (PowerShell):**
        ```bash
        .\venv\Scripts\Activate.ps1
        ```
    * **No macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

4.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```
    **(Observação:** Se você ainda não tem o arquivo `requirements.txt`, você pode criá-lo listando as dependências que instalamos: `flask`, `flask-login`, `sqlalchemy`, `google-api-python-client`.)

5.  **Configure as Credenciais do Google Drive:**
    * Salve o arquivo de credenciais JSON que você obteve do Google Cloud Platform com o nome `controller-web-credentials.json` (ou o nome que você preferir) na raiz do seu projeto (ou no local especificado na variável `CREDENTIALS_FILE` no `app.py`).
    * Atualize a variável `CREDENTIALS_FILE` no seu arquivo `app.py` com o caminho correto para o seu arquivo de credenciais.

6.  **Configure o Banco de Dados:**
    * O projeto utiliza um banco de dados SQLite (`site.db` por padrão). Certifique-se de que o Flask tenha permissão para criar e gravar neste arquivo.

## Como Usar

1.  **Execute a Aplicação Flask:**
    ```bash
    python app.py
    ```

2.  **Acesse no Navegador:**
    Abra seu navegador web e navegue para `http://127.0.0.1:5000/`.

3.  **Autenticação:**
    * Você precisará criar uma conta de usuário acessando a página de registro (`/auth/register`).
    * Após o registro, faça login com suas credenciais na página de login (`/auth/login`).

4.  **Visualizar Arquivos:**
    Após o login, você será redirecionado para a página `/arquivos`, onde poderá ver os arquivos e pastas da sua pasta do Google Drive configurada.

5.  **Navegar em Pastas:**
    Clique nos nomes das pastas para navegar dentro delas.

6.  **Download de Arquivos:**
    Clique no ícone de download ao lado de um arquivo para baixá-lo para o seu computador.

## Próximos Passos (Em Desenvolvimento)

* Implementação de funcionalidades de upload de arquivos.
* Opção de criar novas pastas.
* Melhorias na interface do usuário.
* Suporte para outros serviços de armazenamento em nuvem.

## Contribuição

Contribuições são bem-vindas! Se você tiver alguma sugestão de melhoria, correção de bugs ou novas funcionalidades, sinta-se à vontade para abrir uma issue ou enviar um pull request.

## Licença

Este projeto está sob a licença [SUA_LICENÇA] (adicione a licença de sua preferência, como MIT, Apache 2.0, etc.).

## Agradecimentos

* À equipe do Flask pelo excelente framework web.
* À equipe do Flask-Login por facilitar a autenticação de usuários.
* À equipe do SQLAlchemy pela poderosa biblioteca de ORM.
* À equipe do Google pela API do Google Drive e suas ferramentas de desenvolvimento.