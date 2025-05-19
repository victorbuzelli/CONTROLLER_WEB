from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import User, session
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Message
from flask import current_app, url_for
import re
import secrets

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

@profile_bp.route('/')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@profile_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        user = current_user

        if not user:
            flash('Usuário não encontrado.', 'error')
            return redirect(url_for('profile.profile'))

        # TEMPORARIAMENTE USANDO SENHA EM TEXTO PURO - LEMBRAR DE USAR HASHING EM PRODUÇÃO!
        if current_password == user.senha_hash:
            if new_password == confirm_password:
                if len(new_password) >= 6: # Adicione uma validação mínima para a senha
                    # EM PRODUÇÃO, USE generate_password_hash(new_password) AQUI!
                    user.senha_hash = new_password # TEMPORÁRIO - SUBSTITUIR POR HASHING!
                    session.commit()
                    flash('Senha alterada com sucesso!', 'success')
                    return redirect(url_for('profile.profile'))
                else:
                    flash('A nova senha deve ter pelo menos 6 caracteres.', 'error')
            else:
                flash('A nova senha e a confirmação não coincidem.', 'error')
        else:
            flash('Senha atual incorreta.', 'error')

    return redirect(url_for('profile.profile'))

'''@profile_bp.route('/change_email', methods=['POST'])
@login_required
def change_email():
    if request.method == 'POST':
        new_email = request.form.get('new_email')
        confirm_new_email = request.form.get('confirm_new_email')

        user = current_user

        if not user:
            flash('Usuário não encontrado.', 'error')
            return redirect(url_for('profile.profile'))

        if new_email == confirm_new_email:
            if re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
                existing_user = session.query(User).filter(User.email == new_email, User.id != user.id).first()
                if existing_user:
                    flash('Este e-mail já está cadastrado por outro usuário.', 'error')
                else:
                    token = secrets.token_urlsafe(32)
                    user.new_email = new_email
                    user.email_token = token
                    session.commit()

                    send_verification_email(user, token, new_email) # Envia o e-mail
                    flash('Um link de verificação foi enviado para o seu novo e-mail.', 'info')
                    return redirect(url_for('profile.profile'))
            else:
                flash('Formato de e-mail inválido.', 'error')
        else:
            flash('O novo e-mail e a confirmação não coincidem.', 'error')

    return redirect(url_for('profile.profile'))'''

@profile_bp.route('/change_email', methods=['POST'])
@login_required
def change_email():
    if request.method == 'POST':
        new_email = request.form.get('new_email')
        confirm_new_email = request.form.get('confirm_new_email')

        user = current_user

        if not user:
            flash('Usuário não encontrado.', 'error')
            return redirect(url_for('profile.profile'))

        if new_email == confirm_new_email:
            if re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
                existing_user = session.query(User).filter(User.email == new_email, User.id != user.id).first()
                if existing_user:
                    flash('Este e-mail já está cadastrado por outro usuário.', 'error')
                else:
                    token = secrets.token_urlsafe(32)
                    user.new_email = new_email
                    user.email_token = token
                    session.commit()

                    with current_app.app_context(): # ENVOLVA A CHAMADA AQUI
                        send_verification_email(user, token, new_email)

                    flash('Um link de verificação foi enviado para o seu novo e-mail.', 'info')
                    return redirect(url_for('profile.profile'))
            else:
                flash('Formato de e-mail inválido.', 'error')
        else:
            flash('O novo e-mail e a confirmação não coincidem.', 'error')

    return redirect(url_for('profile.profile'))

def send_verification_email(user, token, new_email):
    with current_app.app_context(): # Adicione este bloco
        msg = Message('Verifique seu novo endereço de e-mail',
                      sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
                      recipients=[new_email])
        link = url_for('profile.verify_email', token=token, _external=True)
        msg.body = f'Por favor, clique no link abaixo para verificar seu novo endereço de e-mail:\n\n{link}\n\nSe você não solicitou esta alteração, ignore este e-mail.'
        try:
            current_app.mail.send(msg)
        except Exception as e:
            flash(f'Erro ao enviar e-mail de verificação: {e}', 'error')
            # É importante logar este erro para depuração

@profile_bp.route('/verify_email/<token>')
@login_required
def verify_email(token):
    user = current_user

    if user:
        if user.email_token == token:
            user.email = user.new_email
            user.new_email = None
            user.email_token = None
            session.commit()
            flash('Seu e-mail foi verificado e alterado com sucesso!', 'success')
        else:
            flash('Link de verificação inválido.', 'error')
    else:
        flash('Usuário não encontrado.', 'error')

    return redirect(url_for('profile.profile'))