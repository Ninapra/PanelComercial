"""Script ejecutado por la tarea programada diaria a las 10 AM"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from app import create_app, db
from app.models import ArchivoExcel, ConfigSMTP, LogSistema
from scripts.notificador_core import procesar_excel
from datetime import datetime

app = create_app()
with app.app_context():
    excel = ArchivoExcel.query.filter_by(activo=True).order_by(ArchivoExcel.subido_en.desc()).first()
    cfg   = ConfigSMTP.query.first()
    if not excel or not cfg:
        print('[ERROR] Sin archivo Excel activo o sin configuracion SMTP')
        sys.exit(1)
    estado = {'corriendo': True, 'progreso': 0, 'total': 0,
              'mensaje': 'Iniciando...', 'log': [], 'enviados': 0, 'errores': 0}
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Iniciando proceso automatico...')
    procesar_excel(excel.ruta, cfg, estado, db, __import__('app.models',fromlist=['Notificacion']).Notificacion, __import__('app.models',fromlist=['LogSistema']).LogSistema)
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Completado: {estado["enviados"]} enviados.')
