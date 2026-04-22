from flask import Blueprint, render_template, request
from flask_login import login_required
from datetime import date, timedelta, datetime
from sqlalchemy import func
from app.models import Notificacion
from app import db

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
def reportes():
    rango  = request.args.get('rango','semanal')
    hoy    = date.today()
    delta  = {'semanal':7,'quincenal':15,'mensual':30}.get(rango,7)
    inicio = hoy - timedelta(days=delta)
    titulos= {'semanal':'Reporte Semanal (7 dias)','quincenal':'Reporte Quincenal (15 dias)','mensual':'Reporte Mensual (30 dias)'}
    rows   = Notificacion.query.filter(
        Notificacion.fecha_envio>=inicio, Notificacion.estado=='enviado'
    ).order_by(Notificacion.fecha_envio.desc()).all()
    por_dia= db.session.query(
        func.date(Notificacion.fecha_envio).label('dia'),
        func.count(Notificacion.id).label('total')
    ).filter(Notificacion.fecha_envio>=inicio, Notificacion.estado=='enviado'
    ).group_by(func.date(Notificacion.fecha_envio)).all()
    return render_template('reportes.html',
        rows=rows, titulo=titulos.get(rango,'Reporte'), rango=rango,
        prox=[r for r in rows if r.tipo_alerta=='proximo'],
        venc=[r for r in rows if r.tipo_alerta=='vencido'],
        labels=[str(r.dia) for r in por_dia],
        datos=[r.total for r in por_dia],
        inicio=inicio.strftime('%d/%m/%Y'), fin=hoy.strftime('%d/%m/%Y'),
        now=datetime.now())
