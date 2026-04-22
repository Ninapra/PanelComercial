from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta
from sqlalchemy import func
from app.models import User, Notificacion, ArchivoExcel, LogSistema, ConfigSMTP
from app import db
from functools import wraps
import os, json

main_bp = Blueprint('main', __name__)

def _log(nivel, msg, mod='sistema'):
    u = current_user.username if current_user.is_authenticated else 'sistema'
    db.session.add(LogSistema(nivel=nivel, mensaje=msg, modulo=mod, usuario=u, ip=request.remote_addr))
    db.session.commit()


def _admin_required(view):
    """Decorador — exige rol admin además de login."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if (current_user.rol or '').lower() != 'admin':
            abort(403)
        return view(*args, **kwargs)
    return wrapper

@main_bp.route('/')
@login_required
def dashboard():
    hoy = date.today()
    total   = Notificacion.query.filter_by(estado='enviado').count()
    hoy_cnt = Notificacion.query.filter(func.date(Notificacion.fecha_envio)==hoy, Notificacion.estado=='enviado').count()
    prox    = Notificacion.query.filter(Notificacion.tipo_alerta=='proximo', Notificacion.dias_diff<=30, Notificacion.dias_diff>0).distinct(Notificacion.dominio).count()
    venc    = Notificacion.query.filter_by(tipo_alerta='vencido', estado='enviado').distinct(Notificacion.dominio).count()
    labels, datos = [], []
    for i in range(6,-1,-1):
        d = hoy - timedelta(days=i)
        c = Notificacion.query.filter(func.date(Notificacion.fecha_envio)==d, Notificacion.estado=='enviado').count()
        labels.append(d.strftime('%d/%m')); datos.append(c)
    ultimas     = Notificacion.query.order_by(Notificacion.fecha_envio.desc()).limit(8).all()
    excel_activo= ArchivoExcel.query.filter_by(activo=True).order_by(ArchivoExcel.subido_en.desc()).first()
    cfg         = ConfigSMTP.query.first()
    limite      = cfg.max_dia if cfg else 300
    return render_template('dashboard.html',
        total=total, hoy_cnt=hoy_cnt, prox=prox, venc=venc,
        labels=json.dumps(labels), datos=json.dumps(datos),
        ultimas=ultimas, excel_activo=excel_activo, limite=limite,
        hoy_pct=round((hoy_cnt/limite)*100,1) if limite else 0,
        now=datetime.now())

@main_bp.route('/notificaciones')
@login_required
def notificaciones():
    page   = request.args.get('page',1,type=int)
    filtro = request.args.get('q','')
    tipo   = request.args.get('tipo','')
    estado = request.args.get('estado','')
    q = Notificacion.query
    if filtro: q = q.filter(Notificacion.dominio.ilike(f'%{filtro}%'))
    if tipo:   q = q.filter_by(tipo_alerta=tipo)
    if estado: q = q.filter_by(estado=estado)
    pag = q.order_by(Notificacion.fecha_envio.desc()).paginate(page=page,per_page=25,error_out=False)
    for n in pag.items:
        n.veces = Notificacion.query.filter_by(dominio=n.dominio, correo_destino=n.correo_destino).count()
    return render_template('notificaciones.html', notifs=pag, filtro=filtro, tipo=tipo, estado=estado, now=datetime.now())

@main_bp.route('/cargar-excel', methods=['GET','POST'])
@login_required
def cargar_excel():
    if request.method == 'POST':
        f = request.files.get('archivo')
        if not f or f.filename == '':
            flash('Selecciona un archivo Excel.', 'error')
            return redirect(request.url)
        ext = f.filename.rsplit('.',1)[-1].lower()
        if ext not in ('xlsx','xls'):
            flash('Solo archivos .xlsx o .xls', 'error')
            return redirect(request.url)
        fname = datetime.now().strftime('%Y%m%d_%H%M%S_') + secure_filename(f.filename)
        ruta  = os.path.join(current_app.config['UPLOAD_FOLDER'], fname)
        f.save(ruta)
        try:
            import pandas as pd
            from scripts.notificador_core import encontrar_hoja, _corregir_fecha
            hoja  = encontrar_hoja(ruta)
            df    = pd.read_excel(ruta, sheet_name=hoja, header=0, dtype={'Vencimiento': object})
            df.columns = df.columns.str.strip()
            df['Vencimiento'] = df['Vencimiento'].apply(_corregir_fecha)
            total = len(df.dropna(subset=['Dominio', 'Vencimiento']))
        except Exception as e:
            total = 0
        ArchivoExcel.query.update({'activo': False})
        db.session.add(ArchivoExcel(nombre=f.filename, ruta=ruta,
            subido_por=current_user.username, total_filas=total, activo=True))
        db.session.commit()
        _log('INFO', f'Excel cargado: {f.filename} ({total} filas)', 'excel')
        flash(f'Archivo cargado. {total} registros encontrados.', 'success')
        return redirect(url_for('main.dashboard'))
    archivos = ArchivoExcel.query.order_by(ArchivoExcel.subido_en.desc()).limit(10).all()
    return render_template('cargar_excel.html', archivos=archivos, now=datetime.now())

@main_bp.route('/logs')
@login_required
def logs():
    page  = request.args.get('page',1,type=int)
    nivel = request.args.get('nivel','')
    mod   = request.args.get('modulo','')
    q = LogSistema.query
    if nivel: q = q.filter_by(nivel=nivel)
    if mod:   q = q.filter_by(modulo=mod)
    pag = q.order_by(LogSistema.created_at.desc()).paginate(page=page,per_page=50,error_out=False)
    return render_template('logs.html', logs=pag, nivel=nivel, mod=mod, now=datetime.now())

@main_bp.route('/configuracion', methods=['GET','POST'])
@login_required
def configuracion():
    cfg = ConfigSMTP.query.first() or ConfigSMTP()
    if request.method == 'POST':
        cfg.host_smtp     = request.form.get('host_smtp','').strip()
        cfg.port_smtp     = int(request.form.get('port_smtp', 465))
        cfg.cifrado       = request.form.get('cifrado','ssl')
        cfg.host_imap     = request.form.get('host_imap','').strip()
        cfg.port_imap     = int(request.form.get('port_imap', 993))
        cfg.usuario       = request.form.get('usuario','').strip()
        cfg.remitente     = request.form.get('remitente','').strip()
        cfg.email_destino = request.form.get('email_destino','').strip()
        cfg.email_reporte = request.form.get('email_reporte','').strip()
        cfg.max_dia       = int(request.form.get('max_dia', 300))
        pwd = request.form.get('password','').strip()
        if pwd: cfg.password_enc = pwd
        cfg.updated_at = datetime.utcnow()
        if not cfg.id: db.session.add(cfg)
        db.session.commit()
        _log('INFO','Configuracion SMTP actualizada','config')
        flash('Configuracion guardada.', 'success')
        return redirect(url_for('main.configuracion'))
    return render_template('configuracion.html', cfg=cfg, now=datetime.now())


# ──────────────────────────────────────────────────────────────────────────
# Gestión de usuarios — admin only
# ──────────────────────────────────────────────────────────────────────────

@main_bp.route('/usuarios', methods=['GET', 'POST'])
@_admin_required
def usuarios():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        nombre = (request.form.get('nombre') or '').strip()
        rol = (request.form.get('rol') or 'operador').strip().lower()
        password = request.form.get('password') or ''
        if not email or not password:
            flash('Email y password son obligatorios.', 'error')
            return redirect(url_for('main.usuarios'))
        if len(password) < 8:
            flash('El password debe tener al menos 8 caracteres.', 'error')
            return redirect(url_for('main.usuarios'))
        if User.query.filter(func.lower(User.email) == email).first():
            flash('Ya existe un usuario con ese correo.', 'warning')
            return redirect(url_for('main.usuarios'))
        username = (email.split('@', 1)[0].replace('.', '_') or 'user')
        # Si el username ya existe, sufijo numérico
        base = username
        i = 1
        while User.query.filter_by(username=username).first():
            i += 1
            username = f"{base}{i}"
        u = User(
            username=username,
            nombre=(nombre or email.split('@', 1)[0].title()),
            email=email,
            rol=(rol if rol in ('admin', 'agente', 'operador') else 'operador'),
            password_hash=generate_password_hash(password),
        )
        db.session.add(u)
        db.session.commit()
        _log('INFO', f'Usuario creado: {email} (rol={rol})', 'usuarios')
        flash(f'Usuario {email} creado correctamente.', 'success')
        return redirect(url_for('main.usuarios'))

    users = User.query.order_by(User.id.asc()).all()
    return render_template('usuarios.html', users=users, now=datetime.now())


@main_bp.route('/usuarios/<int:user_id>/toggle', methods=['POST'])
@_admin_required
def usuarios_toggle(user_id):
    u = User.query.get_or_404(user_id)
    if u.id == current_user.id:
        flash('No puedes desactivar tu propia cuenta.', 'warning')
        return redirect(url_for('main.usuarios'))
    u.activo = not bool(u.activo)
    db.session.commit()
    estado = 'activado' if u.activo else 'desactivado'
    _log('INFO', f'Usuario {u.email} {estado}', 'usuarios')
    flash(f'Usuario {u.email} {estado}.', 'success')
    return redirect(url_for('main.usuarios'))


@main_bp.route('/usuarios/<int:user_id>/password', methods=['POST'])
@_admin_required
def usuarios_reset_password(user_id):
    u = User.query.get_or_404(user_id)
    new_password = request.form.get('password') or ''
    if len(new_password) < 8:
        flash('El password debe tener al menos 8 caracteres.', 'error')
        return redirect(url_for('main.usuarios'))
    u.password_hash = generate_password_hash(new_password)
    db.session.commit()
    _log('WARNING', f'Password de {u.email} reseteado por {current_user.email}', 'usuarios')
    flash(f'Password de {u.email} actualizado.', 'success')
    return redirect(url_for('main.usuarios'))


@main_bp.route('/usuarios/<int:user_id>/eliminar', methods=['POST'])
@_admin_required
def usuarios_eliminar(user_id):
    u = User.query.get_or_404(user_id)
    if u.id == current_user.id:
        flash('No puedes eliminar tu propia cuenta.', 'warning')
        return redirect(url_for('main.usuarios'))
    email = u.email
    db.session.delete(u)
    db.session.commit()
    _log('WARNING', f'Usuario {email} eliminado por {current_user.email}', 'usuarios')
    flash(f'Usuario {email} eliminado.', 'success')
    return redirect(url_for('main.usuarios'))
