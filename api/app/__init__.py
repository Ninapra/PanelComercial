from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from datetime import timedelta
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv es opcional; en producción las vars deben venir del entorno.
    pass

db = SQLAlchemy()
login_manager = LoginManager()


def _require_env(var: str) -> str:
    """Lee una variable obligatoria del entorno o falla rápido.

    Fail-fast es intencional: no queremos defaults en secretos.
    """
    value = os.environ.get(var)
    if not value:
        raise RuntimeError(
            f"Variable de entorno obligatoria '{var}' no está definida. "
            f"Copia api/.env.example a api/.env y complétala."
        )
    return value


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    app.config.update(
        SECRET_KEY=_require_env('SECRET_KEY'),
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'renovaciones.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
        UPLOAD_FOLDER=os.path.join(os.path.dirname(app.instance_path), 'uploads'),
        LOG_FOLDER=os.path.join(os.path.dirname(app.instance_path), 'logs'),
    )
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['LOG_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Inicia sesion para continuar.'

    # CORS: habilita llamadas cross-origin desde el frontend (web/ servido
    # en puerto distinto). Los origenes permitidos vienen del entorno para
    # no hardcodear URLs de prod.
    cors_origins = [o.strip() for o in os.environ.get('CORS_ORIGINS', '').split(',') if o.strip()]
    if cors_origins:
        CORS(app, resources={r"/api/*": {"origins": cors_origins}}, supports_credentials=True)

    from app.routes.auth    import auth_bp
    from app.routes.main    import main_bp
    from app.routes.api     import api_bp
    from app.routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp,     url_prefix='/api')
    app.register_blueprint(reports_bp, url_prefix='/reportes')

    with app.app_context():
        db.create_all()
        _seed_admin()
    return app


def _seed_admin():
    """Crea usuarios iniciales + config SMTP si la BD está vacía.

    Todos los valores se leen de entorno — nunca hardcoded. Si una variable
    crítica falta, ese usuario específico se omite (no rompe el arranque).

    Variables soportadas:
      - ADMIN_EMAIL / ADMIN_PASSWORD: admin único (obligatorio si es primer run)
      - USERS_SEED_JSON: JSON opcional con lista de usuarios extra. Formato:
          [
            {"email":"paula@example.com","password":"...","nombre":"Paula","rol":"agente"},
            ...
          ]
        Se usa para poblar los agentes iniciales (Paula/Camila/Nina/Gerencia)
        sin tener que crearlos manualmente por la UI.
    """
    import json as _json
    from app.models import User, ConfigSMTP
    from werkzeug.security import generate_password_hash

    def _slug(email):
        return (email or '').split('@', 1)[0].replace('.', '_') or 'user'

    def _ensure_user(email, password, nombre, rol='operador'):
        if not email or not password:
            return
        email_norm = email.strip().lower()
        existing = User.query.filter_by(email=email_norm).first()
        if existing:
            return
        db.session.add(User(
            username=_slug(email_norm),
            nombre=nombre or email_norm.split('@', 1)[0].title(),
            email=email_norm,
            rol=rol,
            password_hash=generate_password_hash(password),
        ))

    admin_email = os.environ.get('ADMIN_EMAIL')
    admin_password = os.environ.get('ADMIN_PASSWORD')
    admin_name = os.environ.get('ADMIN_NAME', 'Administrador')
    _ensure_user(admin_email, admin_password, admin_name, 'admin')

    users_raw = os.environ.get('USERS_SEED_JSON', '').strip()
    if users_raw:
        try:
            extra = _json.loads(users_raw)
            if isinstance(extra, list):
                for u in extra:
                    if isinstance(u, dict):
                        _ensure_user(
                            u.get('email'),
                            u.get('password'),
                            u.get('nombre'),
                            u.get('rol', 'operador'),
                        )
        except _json.JSONDecodeError:
            # En dev ignoramos silenciosamente; en prod conviene validar.
            pass

    smtp_user = os.environ.get('IMAP_USER')
    smtp_password = os.environ.get('IMAP_PASSWORD')
    if not ConfigSMTP.query.first() and smtp_user and smtp_password:
        db.session.add(ConfigSMTP(
            host_smtp=os.environ.get('SMTP_HOST', 'smtp.example.com'),
            port_smtp=int(os.environ.get('SMTP_PORT', '465')),
            cifrado=os.environ.get('SMTP_CIPHER', 'ssl'),
            host_imap=os.environ.get('IMAP_HOST', 'imap.example.com'),
            port_imap=int(os.environ.get('IMAP_PORT', '993')),
            usuario=smtp_user,
            password_enc=smtp_password,
            remitente=os.environ.get('SMTP_SENDER', f'Renovaciones <{smtp_user}>'),
            email_destino=os.environ.get('SMTP_DESTINATION', smtp_user),
            email_reporte=os.environ.get('REPORT_RECIPIENT', smtp_user),
            max_dia=int(os.environ.get('SMTP_MAX_PER_DAY', '300')),
        ))
    db.session.commit()
