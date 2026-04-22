"""
Motor de notificaciones v5.1
- LOGICA POR RANGOS: notifica cualquier servicio que vence en 0-45 dias
  o que vencio hace 1-45 dias (no dias exactos)
- Agrupa multiples servicios del mismo dominio/correo en un solo correo
- Sin seccion Encargado en plantillas
"""
import os
import smtplib, ssl, json
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

BASE_DIR  = Path(__file__).resolve().parent.parent
PLANT_DIR = BASE_DIR / 'plantillas'
TODAY     = date.today()
TODAY_LBL = TODAY.strftime('%d/%m/%Y')
ANIO      = str(TODAY.year)
MAX_VENC  = 45   # Usado para barra de progreso y fecha limite en plantilla vencido


# ── Utilidades ─────────────────────────────────────────────────────────────

def _tpl(nombre):
    r = PLANT_DIR / nombre
    return r.read_text(encoding='utf-8') if r.exists() else ''

def _url(dominio):
    return f'https://mi.com.co/Renovar/servicio?dominio={dominio}'

def _num_alerta(dias):
    """Calcula numero de alerta (1-5) segun rango de dias."""
    if dias >= 0:
        # Proximo: 1=urgente(0-4d), 2=critico(5-9d), 3=aviso(10-19d), 4=proximo(20-29d), 5=anticipado(30-45d)
        if dias <= 4:   return 5   # alerta maxima
        elif dias <= 9: return 4
        elif dias <= 19: return 3
        elif dias <= 29: return 2
        else:            return 1
    else:
        # Vencido: numero de veces notificado (cada 5 dias)
        return max(1, abs(dias) // 5)

def _visual(dias):
    if dias <= 4:
        return {'COLOR_INICIO':'#b71c1c','COLOR_FIN':'#c62828',
                'TITULO_PRINCIPAL':f'Vence en {dias} dias - URGENTE'}
    elif dias <= 9:
        return {'COLOR_INICIO':'#c62828','COLOR_FIN':'#e53935',
                'TITULO_PRINCIPAL':f'Vence en {dias} dias - CRITICO'}
    elif dias <= 19:
        return {'COLOR_INICIO':'#e65100','COLOR_FIN':'#f57c00',
                'TITULO_PRINCIPAL':f'Vence en {dias} dias - PROXIMO'}
    elif dias <= 29:
        return {'COLOR_INICIO':'#f9a825','COLOR_FIN':'#fbc02d',
                'TITULO_PRINCIPAL':f'Vence en {dias} dias - AVISO'}
    else:
        return {'COLOR_INICIO':'#1565c0','COLOR_FIN':'#1976d2',
                'TITULO_PRINCIPAL':f'Vence en {dias} dias - RECORDATORIO'}


# ── Plantillas HTML ─────────────────────────────────────────────────────────

def _html_individual(dominio, servicio, dias, fecha_str, num_alerta, total_alertas):
    tpl = _tpl('proximo_vencer.html')
    if not tpl:
        return f'<html><body><h2>Recordatorio: {servicio} de {dominio} vence el {fecha_str} ({dias} dias)</h2></body></html>'
    v = _visual(dias)
    rep = {
        '{{DOMINIO}}': dominio, '{{SERVICIO}}': servicio,
        '{{DIAS_RESTANTES}}': str(dias), '{{FECHA_VENCIMIENTO}}': fecha_str,
        '{{FECHA_ENVIO}}': TODAY_LBL, '{{NUMERO_ALERTA}}': str(num_alerta),
        '{{TOTAL_ALERTAS}}': str(total_alertas),
        '{{URL_RENOVACION}}': _url(dominio), '{{ANIO}}': ANIO,
    }
    rep.update({f'{{{{{k}}}}}': v2 for k, v2 in v.items()})
    for k, v2 in rep.items():
        tpl = tpl.replace(k, v2)
    return tpl

def _html_vencido(dominio, servicio, dias_v, fecha_str):
    tpl = _tpl('servicio_vencido.html')
    if not tpl:
        return f'<html><body><h2>VENCIDO: {servicio} de {dominio} vencio el {fecha_str} (hace {dias_v} dias)</h2></body></html>'
    num  = max(1, dias_v // 5)
    total = MAX_VENC // 5
    pct  = min(int((dias_v / MAX_VENC) * 100), 100)
    lim  = (TODAY - timedelta(days=dias_v) + timedelta(days=MAX_VENC)).strftime('%d/%m/%Y')
    rep  = {
        '{{DOMINIO}}': dominio, '{{SERVICIO}}': servicio,
        '{{DIAS_VENCIDO}}': str(dias_v), '{{FECHA_VENCIMIENTO}}': fecha_str,
        '{{FECHA_ENVIO}}': TODAY_LBL, '{{NUMERO_ALERTA}}': str(num),
        '{{TOTAL_ALERTAS}}': str(total), '{{PROGRESO_PCT}}': str(pct),
        '{{FECHA_LIMITE_ALERTAS}}': lim, '{{URL_RENOVACION}}': _url(dominio),
        '{{ANIO}}': ANIO,
    }
    for k, v in rep.items():
        tpl = tpl.replace(k, v)
    return tpl

def _html_agrupado(dominio, servicios_info):
    # ── Filas table-based (sin flexbox, compatible Gmail/Hotmail/Outlook) ──
    filas = ''
    for i, s in enumerate(servicios_info):
        dias = s['dias']
        bg   = '#ffffff' if i % 2 == 0 else '#f7f9fc'
        if dias >= 0:
            badge_color = '#b71c1c' if dias <= 4 else '#e65100' if dias <= 19 else '#1565c0'
            badge_txt   = f'Vence en {dias} día(s)'
        else:
            badge_color = '#7f0000'
            badge_txt   = f'Vencido hace {abs(dias)} días'
        filas += (
            f'<tr>'
            f'<td bgcolor="{bg}" style="background-color:{bg};padding:11px 14px;border-bottom:1px solid #eef2f7;font-family:Arial,Helvetica,sans-serif;font-size:14px;font-weight:bold;color:#1a1a2e;">{s["servicio"]}</td>'
            f'<td bgcolor="{bg}" style="background-color:{bg};padding:11px 14px;border-bottom:1px solid #eef2f7;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#555555;">{s["fecha"]}</td>'
            f'<td bgcolor="{bg}" style="background-color:{bg};padding:11px 14px;border-bottom:1px solid #eef2f7;">'
            f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
            f'<td bgcolor="{badge_color}" style="background-color:{badge_color};border-radius:12px;padding:3px 10px;">'
            f'<span style="font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:bold;color:#ffffff;">{badge_txt}</span>'
            f'</td></tr></table></td>'
            f'<td bgcolor="{bg}" style="background-color:{bg};padding:11px 14px;border-bottom:1px solid #eef2f7;">'
            f'<a href="{_url(dominio)}" style="font-family:Arial,Helvetica,sans-serif;font-size:13px;font-weight:bold;color:#FF6D00;text-decoration:none;">Renovar</a></td>'
            f'</tr>'
        )
    n   = len(servicios_info)
    url = _url(dominio)
    return (
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" '
        '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" lang="es">\n'
        '<head>\n'
        '  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
        '  <meta name="x-apple-disable-message-reformatting" />\n'
        f'  <title>Renovaciones {dominio}</title>\n'
        '  <style type="text/css">\n'
        '    body,#bodyTable{margin:0!important;padding:0!important;width:100%!important;background-color:#f0f4f8!important;}\n'
        '    table{border-collapse:collapse!important;mso-table-lspace:0pt!important;mso-table-rspace:0pt!important;}\n'
        '    @media only screen and (max-width:640px){\n'
        '      .card{width:100%!important;border-radius:0!important;}\n'
        '      .pad-main{padding:18px 16px!important;}\n'
        '      .pad-hdr{padding:16px 16px 20px!important;}\n'
        '      .btn-link{display:block!important;width:auto!important;}\n'
        '      .tbl-svc td{padding:9px 8px!important;font-size:12px!important;}\n'
        '    }\n'
        '  </style>\n'
        '</head>\n'
        '<body style="margin:0;padding:0;background-color:#f0f4f8;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;">\n'
        '<table id="bodyTable" role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#f0f4f8">\n'
        '  <tr><td align="center" valign="top" style="padding:24px 12px;">\n'
        '  <table class="card" role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"\n'
        '         style="background-color:#ffffff;border-radius:10px;overflow:hidden;">\n'
        '  <!-- HEADER AZUL -->\n'
        '  <tr><td bgcolor="#0d47a1" style="background-color:#0d47a1;padding:0;">\n'
        '    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">\n'
        '      <tr><td style="padding:16px 24px 12px;border-bottom:1px solid rgba(255,255,255,0.18);">\n'
        '        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>\n'
        '          <td valign="middle" width="130">\n'
        '            <table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>\n'
        '              <td width="36" height="36" align="center" valign="middle" bgcolor="#FF6D00"\n'
        '                  style="background-color:#FF6D00;border-radius:7px;font-family:Arial,Helvetica,sans-serif;font-size:15px;font-weight:bold;color:#ffffff;line-height:36px;text-align:center;">MI</td>\n'
        '              <td valign="middle" style="padding-left:8px;"><span style="font-family:Arial,Helvetica,sans-serif;font-size:14px;font-weight:bold;color:#ffffff;">MI.COM.CO</span></td>\n'
        '            </tr></table>\n'
        '          </td>\n'
        '          <td align="right" valign="middle">\n'
        '            <table role="presentation" cellpadding="0" cellspacing="0" border="0" align="right"><tr>\n'
        '              <td bgcolor="#FF6D00" style="background-color:#FF6D00;border-radius:20px;padding:4px 14px;">\n'
        '                <span style="font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:bold;color:#ffffff;text-transform:uppercase;letter-spacing:0.8px;">Múltiples servicios</span>\n'
        '              </td>\n'
        '            </tr></table>\n'
        '          </td>\n'
        '        </tr></table>\n'
        '      </td></tr>\n'
        '    </table>\n'
        '    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">\n'
        '      <tr><td class="pad-hdr" style="padding:20px 24px 26px;">\n'
        f'        <p style="margin:0 0 6px 0;font-family:Arial,Helvetica,sans-serif;font-size:21px;font-weight:bold;color:#ffffff;line-height:1.3;">Recordatorio — {dominio}</p>\n'
        f'        <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:rgba(255,255,255,0.82);line-height:1.5;">Tienes {n} servicio(s) que requieren atención.</p>\n'
        '      </td></tr>\n'
        '    </table>\n'
        '  </td></tr>\n'
        '  <!-- CUERPO -->\n'
        '  <tr><td class="pad-main" style="padding:24px 24px 20px;background-color:#ffffff;">\n'
        '    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>\n'
        '      <td width="3" bgcolor="#0d47a1" style="background-color:#0d47a1;border-radius:3px;">&nbsp;</td>\n'
        '      <td style="padding-left:14px;">\n'
        '        <p style="margin:0 0 5px 0;font-family:Arial,Helvetica,sans-serif;font-size:17px;font-weight:bold;color:#0d47a1;line-height:1.3;">¡Hola!</p>\n'
        '        <p style="margin:0 0 9px 0;font-family:Arial,Helvetica,sans-serif;font-size:15px;color:#333333;line-height:1.7;">Espero que estés teniendo un excelente día.</p>\n'
        f'        <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:15px;color:#333333;line-height:1.7;">Te escribo porque el dominio <strong>{dominio}</strong> tiene <strong>{n} servicio(s)</strong> próximos a vencer o ya vencidos:</p>\n'
        '      </td>\n'
        '    </tr></table>\n'
        '    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td height="18" style="font-size:1px;line-height:1px;">&nbsp;</td></tr></table>\n'
        '    <table class="tbl-svc" role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border:1.5px solid #e3eaf4;border-radius:8px;">\n'
        '      <tr>\n'
        '        <td bgcolor="#0d47a1" style="background-color:#0d47a1;padding:9px 14px;border-radius:6px 6px 0 0;"><span style="font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:bold;color:#ffffff;text-transform:uppercase;letter-spacing:1px;">Servicio</span></td>\n'
        '        <td bgcolor="#0d47a1" style="background-color:#0d47a1;padding:9px 14px;"><span style="font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:bold;color:#ffffff;text-transform:uppercase;letter-spacing:1px;">Vencimiento</span></td>\n'
        '        <td bgcolor="#0d47a1" style="background-color:#0d47a1;padding:9px 14px;"><span style="font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:bold;color:#ffffff;text-transform:uppercase;letter-spacing:1px;">Estado</span></td>\n'
        '        <td bgcolor="#0d47a1" style="background-color:#0d47a1;padding:9px 14px;border-radius:0 6px 0 0;"><span style="font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:bold;color:#ffffff;text-transform:uppercase;letter-spacing:1px;">Acción</span></td>\n'
        '      </tr>\n'
        + filas +
        '    </table>\n'
        '    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td height="20" style="font-size:1px;line-height:1px;">&nbsp;</td></tr></table>\n'
        '    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%"><tr><td align="center">\n'
        '      <table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>\n'
        f'        <td bgcolor="#FF6D00" style="background-color:#FF6D00;border-radius:6px;mso-padding-alt:0;">\n'
        f'          <a class="btn-link" href="{url}" style="display:inline-block;background-color:#FF6D00;border-radius:6px;color:#ffffff;font-family:Arial,Helvetica,sans-serif;font-size:15px;font-weight:bold;line-height:1;padding:14px 32px;text-decoration:none;text-align:center;">Renovar servicios de {dominio}</a>\n'
        '        </td>\n'
        '      </tr></table>\n'
        '    </td></tr></table>\n'
        '    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td height="22" style="border-top:1px solid #eef2f7;font-size:1px;line-height:1px;">&nbsp;</td></tr></table>\n'
        '    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="padding-top:16px;">\n'
        '      <p style="margin:0 0 12px 0;font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#555555;line-height:1.7;">Quedo atenta a cualquier cosa que necesites.</p>\n'
        '      <p style="margin:0 0 2px 0;font-family:Arial,Helvetica,sans-serif;font-size:15px;font-weight:bold;color:#0d47a1;line-height:1.3;">Isa Salazar</p>\n'
        '      <p style="margin:0 0 10px 0;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#777777;line-height:1.4;">Ejecutiva de Cuenta · Renovaciones</p>\n'
        '      <table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>\n'
        '        <td bgcolor="#0d47a1" style="background-color:#0d47a1;border-radius:4px;padding:4px 11px;">\n'
        '          <span style="font-family:Arial,Helvetica,sans-serif;font-size:12px;font-weight:bold;color:#ffffff;">MI.COM.CO</span>\n'
        '        </td>\n'
        '      </tr></table>\n'
        '    </td></tr></table>\n'
        '  </td></tr>\n'
        '  <!-- FOOTER -->\n'
        '  <tr><td bgcolor="#f7f9fc" style="background-color:#f7f9fc;border-top:1px solid #e3eaf4;padding:14px 24px;">\n'
        f'    <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:11px;color:#b0b8c8;text-align:center;line-height:1.7;">Mensaje automático generado por el sistema de renovaciones de MI.COM.CO.<br />Por favor, no responda directamente — contáctenos por nuestros canales oficiales.<br />&copy; {ANIO} MI.COM.CO. Todos los derechos reservados.</p>\n'
        '  </td></tr>\n'
        '  </table></td></tr>\n'
        '</table>\n'
        '</body></html>'
    )

# ── SMTP ────────────────────────────────────────────────────────────────────

def _conectar(cfg):
    try:
        if cfg.cifrado == 'ssl':
            srv = smtplib.SMTP_SSL(cfg.host_smtp, cfg.port_smtp,
                context=ssl.create_default_context(), timeout=15)
        else:
            srv = smtplib.SMTP(cfg.host_smtp, cfg.port_smtp, timeout=15)
            srv.ehlo(); srv.starttls(); srv.ehlo()
        srv.login(cfg.usuario, cfg.password_enc)
        return srv
    except Exception as e:
        raise ConnectionError(f'SMTP: {e}')

def _enviar(srv, cfg, dest, asunto, html):
    from email.utils import formatdate
    msg = MIMEMultipart('alternative')
    msg['Subject'] = asunto
    msg['From']    = cfg.remitente or cfg.usuario
    msg['To']      = dest
    msg['Date']    = formatdate(localtime=True)
    msg['Message-ID'] = f'<{int(__import__("time").time())}.micomco@{(cfg.remitente or cfg.usuario).split("@")[-1]}>'
    msg.attach(MIMEText(html, 'html', 'utf-8'))
    raw = msg.as_bytes()
    srv.sendmail(cfg.remitente or cfg.usuario, dest, raw)
    # Guardar copia en carpeta Enviados via IMAP (silencioso si falla)
    _copiar_enviados(cfg, raw)


def _copiar_enviados(cfg, msg_bytes):
    """
    Sube una copia del mensaje a la carpeta Enviados del buzón via IMAP.
    Usa host IMAP configurado o lo deriva del SMTP.
    Timeout estricto de 8 s en cada intento — NUNCA bloquea el flujo principal.
    """
    import imaplib, ssl as _ssl, time as _time, socket as _socket

    # ── Host IMAP: prioridad al campo imap_host si existe en cfg ──────────
    imap_host_cfg = getattr(cfg, 'imap_host', None) or ''
    smtp_host     = cfg.host_smtp or ''

    if imap_host_cfg:
        hosts = [imap_host_cfg]
    elif smtp_host.lower().startswith('smtp.'):
        base  = smtp_host[5:]                          # smtp.mi.com.co → mi.com.co
        hosts = [f'imap-alt02.{base}', f'imap.{base}', f'mail.{base}', smtp_host]
    else:
        hosts = [smtp_host]

    # Nombres comunes de carpeta Enviados (orden de probabilidad)
    carpetas = ['Sent', 'Enviados', 'Sent Items', 'INBOX.Sent',
                'INBOX.Enviados', '[Gmail]/Sent Mail', 'INBOX/Sent']

    TIMEOUT = 8   # segundos — timeout estricto para cada conexión

    ctx  = _ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode    = _ssl.CERT_NONE   # algunos servidores tienen cert auto-firmado
    imap = None

    for host in hosts:
        for port, usar_ssl in [(993, True), (143, False)]:
            try:
                _socket.setdefaulttimeout(TIMEOUT)
                if usar_ssl:
                    imap = imaplib.IMAP4_SSL(host, port, ssl_context=ctx)
                else:
                    imap = imaplib.IMAP4(host, port)
                    imap.starttls(ssl_context=ctx)
                imap.socket().settimeout(TIMEOUT)
                break
            except Exception:
                imap = None
                continue
        if imap:
            break

    _socket.setdefaulttimeout(None)   # restaurar timeout global

    if not imap:
        return   # Sin IMAP accesible — salir en silencio

    try:
        imap.login(cfg.usuario, cfg.password_enc)

        # Listar carpetas del servidor para encontrar la correcta
        carpeta_ok = None
        try:
            _, listas = imap.list()
            nombres_servidor = []
            for item in (listas or []):
                try:
                    txt    = item.decode('utf-8', errors='ignore')
                    nombre = txt.rsplit(' ', 1)[-1].strip().strip('"').strip("'")
                    nombres_servidor.append(nombre)
                except Exception:
                    pass
            for c in carpetas:
                if any(c.lower() == s.lower() for s in nombres_servidor):
                    carpeta_ok = c
                    break
        except Exception:
            pass

        # Si no encontró por lista, intentar SELECT directo
        if not carpeta_ok:
            for c in carpetas:
                try:
                    ok, _ = imap.select(f'"{c}"')
                    if ok == 'OK':
                        carpeta_ok = c
                        break
                except Exception:
                    continue

        if carpeta_ok:
            fecha_imap = imaplib.Time2Internaldate(_time.time())
            imap.append(f'"{carpeta_ok}"', r'(\Seen)', fecha_imap, msg_bytes)

    except Exception:
        pass   # Fallo silencioso
    finally:
        _socket.setdefaulttimeout(None)
        try:
            imap.logout()
        except Exception:
            pass


# ── Deteccion automatica de hoja ────────────────────────────────────────────

def encontrar_hoja(ruta_excel):
    """
    Detecta automaticamente la hoja correcta del Excel.
    Prioridad: (1) hoja que tenga columnas Dominio+Vencimiento+Correo,
               (2) hoja con al menos Dominio+Vencimiento,
               (3) coincidencia por nombre conocido,
               (4) primera hoja que no sea de resumen.
    """
    import pandas as pd
    xl    = pd.ExcelFile(ruta_excel)
    hojas = xl.sheet_names

    # ── 1. Buscar la hoja que tenga las columnas clave (criterio más fiable) ──
    mejor_hoja   = None
    mejor_score  = 0
    cols_clave   = {'dominio', 'vencimiento', 'correo', 'servicio'}
    cols_minimas = {'dominio', 'vencimiento'}

    for hoja in hojas:
        try:
            df_t  = pd.read_excel(ruta_excel, sheet_name=hoja, header=0, nrows=3)
            cols  = {str(c).strip().lower() for c in df_t.columns}
            score = len(cols & cols_clave)           # cuántas columnas clave tiene
            if score > mejor_score and cols_minimas.issubset(cols):
                mejor_score = score
                mejor_hoja  = hoja
        except Exception:
            continue

    if mejor_hoja:
        return mejor_hoja

    # ── 2. Coincidencia por nombre (solo si ninguna hoja tiene las columnas) ──
    candidatos_nombre = [
        'Vencimiento', 'vencimiento', 'VENCIMIENTO', 'Vencimientos',
        'Hoja1', 'Hoja 1', 'Hoja2', 'Hoja 2', 'Sheet1', 'Sheet 1',
    ]
    for candidato in candidatos_nombre:
        for hoja in hojas:
            if hoja.strip().lower() == candidato.lower():
                return hoja

    # ── 3. Primera hoja que no sea claramente de resumen/config ──
    excluir = {'meta', 'contacto', 'config', 'configuracion', 'resumen',
               'summary', 'data', 'datos'}
    for hoja in hojas:
        if hoja.strip().lower() not in excluir:
            return hoja

    return hojas[0] if hojas else None


# ── Motor principal ─────────────────────────────────────────────────────────

def _corregir_fecha(valor):
    """
    Convierte cualquier celda de fecha al date correcto.
    Detecta y corrige el intercambio DD/MM↔MM/DD que ocurre cuando Excel
    guarda fechas colombianas (DD/MM/YYYY) como si fueran MM/DD/YYYY.
    Casos manejados:
      - datetime de Python/Excel ya convertido (puede estar invertido)
      - string 'DD/MM/YYYY', 'YYYY-MM-DD', 'MM/DD/YYYY'
    """
    from datetime import datetime as _dt, date as _date
    import pandas as _pd

    if _pd.isna(valor) or valor is None:
        return _pd.NaT

    # Convertir a Timestamp si es datetime/date
    if isinstance(valor, (_dt, _date)):
        ts = _pd.Timestamp(valor)
    elif isinstance(valor, str):
        valor = valor.strip()
        for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%d/%m/%y'):
            try:
                ts = _pd.Timestamp(_dt.strptime(valor, fmt))
                # Strings DD/MM/YYYY ya están en formato correcto → devolver directo
                if fmt == '%d/%m/%Y':
                    return ts
                break
            except ValueError:
                continue
        else:
            return _pd.NaT
    elif isinstance(valor, _pd.Timestamp):
        ts = valor
    else:
        try:
            ts = _pd.Timestamp(valor)
        except Exception:
            return _pd.NaT

    # ── Detectar inversión DD/MM↔MM/DD ──────────────────────────────────
    # Heurística: si la fecha queda a más de 60 días en el futuro
    # Y el día<=12 (pudo haber sido el mes original), intentar invertir.
    hoy = TODAY
    if ts.date() > hoy:
        dias_diff = (ts.date() - hoy).days
        if dias_diff > 60 and ts.day <= 12:
            try:
                ts_inv    = ts.replace(month=ts.day, day=ts.month)
                dias_inv  = (ts_inv.date() - hoy).days
                # Aceptar la inversión si queda en rango razonable (-730 a +45)
                if -730 <= dias_inv <= 45:
                    return ts_inv
            except ValueError:
                pass

    return ts


def procesar_excel(ruta_excel, cfg, estado, db, Notificacion, LogSistema):
    import pandas as pd

    estado['mensaje'] = 'Leyendo Excel...'

    # Detectar hoja automaticamente
    hoja = encontrar_hoja(ruta_excel)
    if not hoja:
        raise ValueError('No se encontro ninguna hoja valida en el archivo Excel.')
    estado['log'].append(f'[INFO] Hoja detectada: {hoja}')

    # Leer sin conversión automática de fechas para poder corregirlas
    df = pd.read_excel(ruta_excel, sheet_name=hoja, header=0, dtype={'Vencimiento': object})
    df.columns = df.columns.str.strip()

    # Aplicar corrector inteligente de fechas (resuelve inversión DD/MM↔MM/DD)
    df['Vencimiento'] = df['Vencimiento'].apply(_corregir_fecha)
    df = df.dropna(subset=['Vencimiento', 'Dominio'])

    estado['log'].append(f'[INFO] {len(df)} filas validas encontradas')

    # ── Agrupar por (dominio, correo_destino) ────────────────────────────
    grupos = {}
    email_fb = cfg.email_destino or cfg.usuario
    for _, row in df.iterrows():
        dominio  = str(row.get('Dominio', '')).strip()
        servicio = str(row.get('Servicio', 'N/D')).strip()
        correo   = str(row.get('Correo', '')).strip()
        if not dominio or dominio.lower() == 'nan':
            continue
        try:
            fv = row['Vencimiento'].date()
        except Exception:
            continue
        dias = (fv - TODAY).days
        dest = correo if ('@' in correo and correo.lower() != 'nan') else email_fb
        key  = (dominio, dest)
        if key not in grupos:
            grupos[key] = []
        grupos[key].append({
            'servicio': servicio, 'fecha_vcto': fv,
            'fecha_str': fv.strftime('%d/%m/%Y'), 'dias': dias
        })

    estado['total']    = len(grupos)
    estado['progreso'] = 0
    max_dia            = cfg.max_dia or 300
    srv                = _conectar(cfg)
    sesion             = 0

    for i, ((dominio, correo), servicios) in enumerate(grupos.items()):
        estado['progreso'] = i + 1

        if not estado['corriendo']:
            estado['log'].append('[STOP] Proceso detenido por el usuario.')
            break

        # Verificar limite diario
        hoy_cnt = Notificacion.query.filter(
            db.func.date(Notificacion.fecha_envio) == TODAY,
            Notificacion.estado == 'enviado'
        ).count()
        if max_dia > 0 and (hoy_cnt + sesion) >= max_dia:
            estado['mensaje'] = f'Limite diario de {max_dia} correos alcanzado.'
            estado['log'].append(f'[LIMITE] Detenido en dominio {i+1}/{len(grupos)}')
            break

        # ── LOGICA DE NOTIFICACION ───────────────────────────────────────
        # Proximos: vence en los proximos 0-45 dias
        # Vencidos: vencio hace cualquier cantidad de dias (sin limite)
        activos = []
        for s in servicios:
            d = s['dias']
            if 0 <= d <= MAX_VENC:   # Proximo: vence hoy o en <= 45 dias
                activos.append(s)
            elif d < 0:              # Vencido: sin importar cuantos dias lleve
                activos.append(s)

        if not activos:
            estado['log'].append(f'[SKIP] {dominio} | Sin servicios en rango de notificacion')
            continue

        estado['mensaje'] = f'[{i+1}/{len(grupos)}] Enviando a {dominio}...'

        try:
            if len(activos) > 1:
                # CORREO AGRUPADO — multiples servicios
                info   = [{'servicio': s['servicio'], 'fecha': s['fecha_str'], 'dias': s['dias']}
                          for s in activos]
                html   = _html_agrupado(dominio, info)
                asunto = f'Servicios proximos a vencer en {dominio}'
                _enviar(srv, cfg, correo, asunto, html)
                for s in activos:
                    tipo = 'proximo' if s['dias'] >= 0 else 'vencido'
                    db.session.add(Notificacion(
                        dominio=dominio,
                        servicios=', '.join(x['servicio'] for x in activos),
                        tipo_envio='agrupado', fecha_vencimiento=s['fecha_vcto'],
                        correo_destino=correo, estado='enviado', tipo_alerta=tipo,
                        dias_diff=s['dias'], asunto=asunto,
                        numero_alerta=_num_alerta(s['dias'])
                    ))
                sesion += 1
                estado['log'].append(f'[AGRUPADO] {dominio} | {len(activos)} servicios | -> {correo}')
                estado['enviados'] = sesion

            else:
                # CORREO INDIVIDUAL
                s    = activos[0]
                dias = s['dias']
                num  = _num_alerta(dias)
                if dias >= 0:
                    html   = _html_individual(dominio, s['servicio'], dias, s['fecha_str'], num, 5)
                    asunto = f'Proximo a vencer {s["servicio"]} del {dominio}'
                    tipo   = 'proximo'
                else:
                    html   = _html_vencido(dominio, s['servicio'], abs(dias), s['fecha_str'])
                    asunto = f'Vencido {s["servicio"]} del {dominio}'
                    tipo   = 'vencido'
                _enviar(srv, cfg, correo, asunto, html)
                db.session.add(Notificacion(
                    dominio=dominio, servicios=s['servicio'],
                    tipo_envio='individual', fecha_vencimiento=s['fecha_vcto'],
                    correo_destino=correo, estado='enviado', tipo_alerta=tipo,
                    dias_diff=dias, asunto=asunto, numero_alerta=num
                ))
                sesion += 1
                estado['log'].append(f'[ENVIADO] {dominio} | {s["servicio"]} | {dias}d | -> {correo}')
                estado['enviados'] = sesion

            db.session.commit()

        except smtplib.SMTPServerDisconnected:
            estado['log'].append(f'[RECONECTANDO] Conexion perdida, reconectando...')
            try:
                srv = _conectar(cfg)
            except Exception as e:
                estado['log'].append(f'[ERROR SMTP] {e}')
        except Exception as e:
            estado['errores'] = estado.get('errores', 0) + 1
            estado['log'].append(f'[ERROR] {dominio}: {e}')
            try:
                db.session.add(Notificacion(
                    dominio=dominio,
                    servicios=', '.join(s['servicio'] for s in activos),
                    correo_destino=correo, estado='error', error_msg=str(e)[:500]
                ))
                db.session.commit()
            except Exception:
                db.session.rollback()

    try:
        srv.quit()
    except Exception:
        pass

    # Reporte diario a paula
    if sesion > 0:
        _reporte_paula(cfg, sesion, estado['log'])

    estado['mensaje'] = f'Completado. {sesion} correos enviados, {estado.get("errores", 0)} errores.'
    try:
        db.session.add(LogSistema(
            nivel='INFO',
            mensaje=f'Proceso finalizado. Enviados: {sesion}. Errores: {estado.get("errores", 0)}. Hoja: {hoja}',
            modulo='notificador', usuario='sistema', ip='127.0.0.1'
        ))
        db.session.commit()
    except Exception:
        pass


def _reporte_paula(cfg, total, log_lines):
    try:
        filas = ''.join(
            f'<tr style="background:{"#f9f9f9" if i%2==0 else "#fff"}">'
            f'<td style="padding:8px 12px;border-bottom:1px solid #eee;font-family:monospace;font-size:12px;">{l}</td></tr>'
            for i, l in enumerate(log_lines[:200])
        )
        html = f"""<html><body style="font-family:Arial,sans-serif;">
<div style="max-width:700px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#0d47a1,#1976d2);padding:20px;border-radius:8px 8px 0 0;">
    <h2 style="color:#fff;margin:0;">Reporte diario — {TODAY_LBL}</h2>
    <p style="color:rgba(255,255,255,.8);margin:6px 0 0;">Total enviados: <strong>{total}</strong></p>
  </div>
  <div style="background:#fff;padding:20px;border:1px solid #e3eaf4;">
    <table style="width:100%;border-collapse:collapse;">{filas}</table>
  </div>
  <div style="background:#f7f9fc;padding:12px;text-align:center;font-size:11px;color:#aaa;border:1px solid #e3eaf4;border-top:none;border-radius:0 0 8px 8px;">
    MI.COM.CO - Sistema de Renovaciones - {TODAY_LBL}
  </div>
</div></body></html>"""
        srv = _conectar(cfg)
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'[MI.COM.CO] Reporte diario {TODAY_LBL} - {total} envios'
        msg['From']    = cfg.remitente or cfg.usuario
        msg['To']      = cfg.email_reporte or os.environ.get('REPORT_RECIPIENT', '')
        msg.attach(MIMEText(html, 'html', 'utf-8'))
        srv.sendmail(cfg.remitente or cfg.usuario, cfg.email_reporte or os.environ.get('REPORT_RECIPIENT', ''), msg.as_string())
        srv.quit()
    except Exception:
        pass  # No interrumpir si falla el reporte
