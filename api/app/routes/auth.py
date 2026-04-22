from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from app.models import User, LogSistema
from app import db
import re

auth_bp = Blueprint('auth', __name__)

def _log(nivel, msg, user='anonimo'):
    db.session.add(LogSistema(nivel=nivel, mensaje=msg, modulo='auth',
        usuario=user, ip=request.remote_addr))
    db.session.commit()

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        username = re.sub(r'[^a-zA-Z0-9_.@-]', '', request.form.get('username',''))[:80]
        password = request.form.get('password','')
        user = User.query.filter_by(username=username, activo=True).first()
        if user and user.bloqueado_hasta and user.bloqueado_hasta > datetime.utcnow():
            mins = int((user.bloqueado_hasta - datetime.utcnow()).total_seconds()/60)
            flash(f'Cuenta bloqueada. Intenta en {mins} minuto(s).', 'error')
            return render_template('login.html')
        if user and user.check_password(password):
            user.intentos = 0; user.bloqueado_hasta = None
            user.ultimo_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=False)
            _log('INFO', f'Login exitoso: {username}', username)
            return redirect(url_for('main.dashboard'))
        else:
            if user:
                user.intentos = (user.intentos or 0) + 1
                if user.intentos >= 5:
                    user.bloqueado_hasta = datetime.utcnow() + timedelta(minutes=15)
                    flash('Demasiados intentos. Cuenta bloqueada 15 minutos.', 'error')
                else:
                    flash(f'Credenciales incorrectas. Intento {user.intentos}/5.', 'error')
                db.session.commit()
            else:
                flash('Credenciales incorrectas.', 'error')
            _log('WARN', f'Login fallido: {username}')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    _log('INFO', f'Logout: {current_user.username}', current_user.username)
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/cambiar-password', methods=['GET','POST'])
@login_required
def cambiar_password():
    if request.method == 'POST':
        actual = request.form.get('actual','')
        nueva  = request.form.get('nueva','')
        conf   = request.form.get('confirmar','')
        if not current_user.check_password(actual):
            flash('Contrasena actual incorrecta.', 'error')
        elif nueva != conf:
            flash('Las contrasenas nuevas no coinciden.', 'error')
        elif len(nueva) < 8:
            flash('La contrasena debe tener al menos 8 caracteres.', 'error')
        else:
            current_user.set_password(nueva)
            db.session.commit()
            flash('Contrasena actualizada.', 'success')
            return redirect(url_for('main.dashboard'))
    return render_template('cambiar_password.html')
