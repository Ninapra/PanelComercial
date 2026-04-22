from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import check_password_hash
from datetime import datetime, date, timedelta
from sqlalchemy import func
from app.models import User, Notificacion, ArchivoExcel, LogSistema, ConfigSMTP
from app import db
import threading, json, smtplib, ssl

api_bp = Blueprint('api', __name__)


# ── Health / conectividad ──────────────────────────────────────────────────
# Endpoint publico usado por el frontend para verificar que el backend esta
# arriba antes de habilitar features que dependen del API.
@api_bp.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'service': 'panel-comercial-api',
        'time': datetime.utcnow().isoformat() + 'Z',
    })


# ── Auth JSON (fuente unica de autenticacion para el panel master) ─────────
# El panel web (web/index.html) llama a /api/auth/login con email+password.
# Flask-Login crea la sesion (cookie SameSite=Lax en dominio :5000) y el
# iframe del "Notificador" hereda esa sesion sin pedir re-login.

def _user_payload(u):
    return {
        'email':  u.email,
        'nombre': u.nombre,
        'rol':    u.rol,
        'inicial': (u.nombre or u.email or '?')[:1].upper(),
    }


@api_bp.route('/auth/login', methods=['POST', 'OPTIONS'])
def auth_login():
    if request.method == 'OPTIONS':
        return ('', 204)
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    if not email or not password:
        return jsonify({'ok': False, 'error': 'missing_credentials'}), 400
    user = User.query.filter(func.lower(User.email) == email).first()
    if not user or not user.activo or not check_password_hash(user.password_hash, password):
        return jsonify({'ok': False, 'error': 'invalid_credentials'}), 401
    login_user(user, remember=True)
    user.ultimo_login = datetime.utcnow()
    db.session.commit()
    return jsonify({'ok': True, 'user': _user_payload(user)})


@api_bp.route('/auth/me')
def auth_me():
    if not current_user.is_authenticated:
        return jsonify({'ok': False, 'error': 'not_authenticated'}), 401
    return jsonify({'ok': True, 'user': _user_payload(current_user)})


@api_bp.route('/auth/logout', methods=['POST'])
def auth_logout():
    if current_user.is_authenticated:
        logout_user()
    return jsonify({'ok': True})


estado_proceso = {
    'corriendo': False, 'progreso': 0, 'total': 0,
    'mensaje': 'Esperando...', 'log': [], 'inicio': None,
    'enviados': 0, 'errores': 0
}

@api_bp.route('/stats')
@login_required
def stats():
    hoy = date.today()
    hoy_cnt = Notificacion.query.filter(
        func.date(Notificacion.fecha_envio)==hoy, Notificacion.estado=='enviado').count()
    cfg = ConfigSMTP.query.first()
    lim = cfg.max_dia if cfg else 300
    return jsonify({'enviados_hoy': hoy_cnt, 'limite': lim,
        'pct': round((hoy_cnt/lim)*100,1) if lim else 0})

@api_bp.route('/progreso')
@login_required
def progreso():
    return jsonify(estado_proceso)

@api_bp.route('/lanzar', methods=['POST'])
@login_required
def lanzar():
    global estado_proceso
    if estado_proceso['corriendo']:
        return jsonify({'ok': False, 'msg': 'Proceso en ejecucion.'})
    excel = ArchivoExcel.query.filter_by(activo=True).order_by(ArchivoExcel.subido_en.desc()).first()
    if not excel:
        return jsonify({'ok': False, 'msg': 'Carga un archivo Excel primero.'})
    cfg = ConfigSMTP.query.first()
    if not cfg or not cfg.usuario:
        return jsonify({'ok': False, 'msg': 'Configura el servidor SMTP.'})
    estado_proceso.update({'corriendo':True,'progreso':0,'total':0,
        'mensaje':'Iniciando...','log':[],'inicio':datetime.now().strftime('%H:%M:%S'),
        'enviados':0,'errores':0})
    app = current_app._get_current_object()
    t = threading.Thread(target=_run, args=(app, excel, cfg, current_user.username), daemon=True)
    t.start()
    return jsonify({'ok': True})

@api_bp.route('/detener', methods=['POST'])
@login_required
def detener():
    estado_proceso['corriendo'] = False
    estado_proceso['mensaje']   = 'Detenido por usuario.'
    return jsonify({'ok': True})

def _run(app, excel, cfg, usuario):
    with app.app_context():
        try:
            import sys, os
            sys.path.insert(0, os.path.dirname(app.instance_path))
            from scripts.notificador_core import procesar_excel
            procesar_excel(excel.ruta, cfg, estado_proceso, db, Notificacion, LogSistema)
        except Exception as e:
            estado_proceso['log'].append(f'[ERROR CRITICO] {e}')
            estado_proceso['mensaje'] = f'Error: {e}'
            db.session.add(LogSistema(nivel='ERROR', mensaje=str(e)[:500],
                modulo='notificador', usuario=usuario, ip='127.0.0.1'))
            db.session.commit()
        finally:
            estado_proceso['corriendo'] = False

@api_bp.route('/test-smtp', methods=['POST'])
@login_required
def test_smtp():
    cfg = ConfigSMTP.query.first()
    if not cfg: return jsonify({'ok':False,'msg':'Sin configuracion SMTP.'})
    try:
        if cfg.cifrado == 'ssl':
            srv = smtplib.SMTP_SSL(cfg.host_smtp, cfg.port_smtp,
                context=ssl.create_default_context(), timeout=10)
        else:
            srv = smtplib.SMTP(cfg.host_smtp, cfg.port_smtp, timeout=10)
            srv.starttls()
        srv.login(cfg.usuario, cfg.password_enc)
        srv.quit()
        return jsonify({'ok':True, 'msg':f'Conexion exitosa a {cfg.host_smtp}:{cfg.port_smtp}'})
    except Exception as e:
        return jsonify({'ok':False, 'msg':str(e)})

@api_bp.route('/reporte-data')
@login_required
def reporte_data():
    rango = request.args.get('rango','semanal')
    hoy   = date.today()
    delta = {'semanal':7,'quincenal':15,'mensual':30}.get(rango,7)
    inicio = hoy - timedelta(days=delta)
    rows = Notificacion.query.filter(
        Notificacion.fecha_envio>=inicio, Notificacion.estado=='enviado'
    ).order_by(Notificacion.fecha_envio.desc()).all()
    data = [{'dominio':n.dominio,'servicios':n.servicios,'tipo':n.tipo_alerta,
        'vence':n.fecha_vencimiento.strftime('%d/%m/%Y') if n.fecha_vencimiento else '',
        'correo':n.correo_destino,
        'enviado':n.fecha_envio.strftime('%d/%m/%Y %H:%M') if n.fecha_envio else '',
        'alerta':n.numero_alerta,'tipo_envio':n.tipo_envio} for n in rows]
    return jsonify({'ok':True,'data':data,'total':len(data),'rango':rango})

@api_bp.route('/ia/mejorar', methods=['POST'])
@login_required
def ia_mejorar():
    """Agente IA: analiza y mejora el texto del correo antes de enviarlo"""
    datos  = request.get_json() or {}
    texto  = datos.get('texto','')
    modo   = datos.get('modo','ortografia')
    if not texto:
        return jsonify({'ok':False,'msg':'Texto vacio'})
    try:
        import anthropic, os
        client = anthropic.Anthropic()
        if modo == 'ortografia':
            prompt = f"""Eres experto en redaccion corporativa en espanol colombiano.
Revisa este texto de correo electronico:
1. Corrige ortografia y gramatica
2. Mejora redaccion: profesional, cordial, claro
3. Conserva TODOS los placeholders como {{{{DOMINIO}}}}, {{{{SERVICIO}}}}, {{{{FECHA_VENCIMIENTO}}}}
4. Responde SOLO con el texto corregido, sin explicaciones

Texto: {texto}"""
        else:
            prompt = f"""Analiza este listado de renovaciones y genera un resumen ejecutivo en espanol:
- Cuantos dominios proximos a vencer
- Cuantos ya vencidos
- Servicios mas frecuentes
- Recomendaciones de accion inmediata
Datos: {texto}"""
        msg = client.messages.create(
            model='claude-sonnet-4-6', max_tokens=1024,
            messages=[{'role':'user','content':prompt}]
        )
        return jsonify({'ok':True,'texto':msg.content[0].text})
    except Exception as e:
        return jsonify({'ok':False,'msg':f'Error IA: {e}'})
