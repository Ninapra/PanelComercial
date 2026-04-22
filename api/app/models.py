from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nombre        = db.Column(db.String(120))
    email         = db.Column(db.String(120))
    rol           = db.Column(db.String(20), default='operador')
    activo        = db.Column(db.Boolean, default=True)
    ultimo_login  = db.Column(db.DateTime)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    intentos      = db.Column(db.Integer, default=0)
    bloqueado_hasta = db.Column(db.DateTime)

    def set_password(self, p): self.password_hash = generate_password_hash(p)
    def check_password(self, p): return check_password_hash(self.password_hash, p)

class Notificacion(db.Model):
    __tablename__ = 'notificaciones'
    id               = db.Column(db.Integer, primary_key=True)
    dominio          = db.Column(db.String(255), nullable=False, index=True)
    servicios        = db.Column(db.String(500))
    tipo_envio       = db.Column(db.String(20), default='individual')
    fecha_vencimiento= db.Column(db.Date)
    correo_destino   = db.Column(db.String(255))
    fecha_envio      = db.Column(db.DateTime, default=datetime.utcnow)
    estado           = db.Column(db.String(20), default='enviado')
    tipo_alerta      = db.Column(db.String(20))
    dias_diff        = db.Column(db.Integer)
    numero_alerta    = db.Column(db.Integer, default=1)
    asunto           = db.Column(db.String(500))
    error_msg        = db.Column(db.Text)
    excel_archivo    = db.Column(db.String(255))
    ia_revisado      = db.Column(db.Boolean, default=False)

class ArchivoExcel(db.Model):
    __tablename__ = 'archivos_excel'
    id         = db.Column(db.Integer, primary_key=True)
    nombre     = db.Column(db.String(255))
    ruta       = db.Column(db.String(500))
    subido_en  = db.Column(db.DateTime, default=datetime.utcnow)
    subido_por = db.Column(db.String(80))
    total_filas= db.Column(db.Integer)
    activo     = db.Column(db.Boolean, default=True)

class LogSistema(db.Model):
    __tablename__ = 'logs_sistema'
    id         = db.Column(db.Integer, primary_key=True)
    nivel      = db.Column(db.String(10))
    mensaje    = db.Column(db.Text)
    modulo     = db.Column(db.String(50))
    usuario    = db.Column(db.String(80))
    ip         = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

class ConfigSMTP(db.Model):
    __tablename__ = 'config_smtp'
    id           = db.Column(db.Integer, primary_key=True)
    host_smtp    = db.Column(db.String(255))
    port_smtp    = db.Column(db.Integer, default=465)
    cifrado      = db.Column(db.String(10), default='ssl')
    host_imap    = db.Column(db.String(255))
    port_imap    = db.Column(db.Integer, default=993)
    usuario      = db.Column(db.String(255))
    password_enc = db.Column(db.String(500))
    remitente    = db.Column(db.String(255))
    email_destino= db.Column(db.String(255))
    email_reporte= db.Column(db.String(255))
    max_dia      = db.Column(db.Integer, default=300)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow)
