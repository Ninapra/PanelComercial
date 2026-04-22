# Sistema de Notificaciones de Renovaciones — MI.COM.CO v2.0

## ¿Qué es este proyecto?

Panel web que automatiza el envío de correos de notificación de vencimiento de servicios a clientes de MI.COM.CO. Reduce el proceso de 4 horas manuales a 15 minutos.

## Tecnologías

- **Backend:** Python 3 + Flask
- **Base de datos:** SQLite (via SQLAlchemy)
- **Frontend:** HTML/CSS/JS (Jinja2 templates)
- **Correo:** SMTP SSL + IMAP (copia en Enviados)
- **IA:** Anthropic Claude API (revisión de plantillas)

## Estructura del proyecto

```
micomco_panel/
├── INSTALAR.bat          ← Instalación automática (ejecutar como admin, 1 sola vez)
├── INICIAR_PANEL.bat     ← Iniciar el panel (uso diario)
├── run.py                ← Punto de entrada Flask (http://localhost:5000)
├── run_notificador.py    ← Script para tarea programada (10 AM)
├── requirements.txt      ← Dependencias Python
├── app/
│   ├── __init__.py       ← Factory Flask + seed inicial de BD
│   ├── models.py         ← Modelos: User, Notificacion, ArchivoExcel, LogSistema, ConfigSMTP
│   └── routes/
│       ├── auth.py       ← Login / logout / cambiar contraseña
│       ├── main.py       ← Dashboard, cargar Excel, notificaciones, logs, configuración
│       ├── api.py        ← /api/lanzar, /api/progreso, /api/detener, /api/ia/mejorar
│       └── reports.py    ← Reportes semanal / quincenal / mensual
├── scripts/
│   └── notificador_core.py  ← Motor principal de procesamiento y envío
└── plantillas/
    ├── proximo_vencer.html  ← Plantilla correo próximo a vencer
    └── servicio_vencido.html← Plantilla correo servicio vencido
```

## Instalación rápida (Windows)

1. Descomprimir en `C:\micomco_panel\`
2. Clic derecho sobre `INSTALAR.bat` → "Ejecutar como administrador"
3. Esperar que termine (instala Python y dependencias automáticamente)
4. Para usar: doble clic en `INICIAR_PANEL.bat`
5. Abrir navegador en: http://localhost:5000

## Credenciales iniciales

- **Usuario:** `admin`
- **Contraseña:** `Admin2024!` ← cambiar al primer ingreso

## Configuración SMTP/IMAP requerida

Ir a **Configuración** en el panel y completar:

Los valores de SMTP/IMAP se configuran vía variables de entorno.
Ver `api/.env.example` para la lista completa de variables y placeholders.

| Variable | Descripción |
|----------|-------------|
| `SMTP_HOST` / `SMTP_PORT` | Servidor SMTP saliente (ej. 465 con SSL) |
| `IMAP_HOST` / `IMAP_PORT` | Servidor IMAP para copia en Enviados |
| `IMAP_USER` / `IMAP_PASSWORD` | Credenciales de la cuenta |
| `SMTP_SENDER` | Nombre visible del remitente |

Nunca hardcodees estos valores en el código — el guardrail de seguridad
bloqueará el commit.

## Formato del Excel

El archivo Excel debe tener una hoja con las columnas:

| Columna | Descripción |
|---------|-------------|
| Dominio | Nombre del dominio (ej: empresa.com.co) |
| Servicio | Tipo de servicio (ej: Correo, Hosting, SSL) |
| Vencimiento | Fecha de vencimiento (DD/MM/YYYY) |
| Correo | Correo del cliente destinatario |
| Encargado | Nombre del encargado (opcional) |
| Categoria | Categoría del servicio (opcional) |

El sistema detecta automáticamente el nombre de la hoja y corrige fechas con formato invertido.

## Lógica de notificación

- **Próximos a vencer:** servicios que vencen en los próximos 0 a 45 días
- **Vencidos:** servicios vencidos hace cualquier cantidad de días (sin límite)
- **Anti-duplicados:** no reenvía al mismo dominio en el mismo día
- **Agrupación:** si un cliente tiene varios servicios, recibe un único correo con tabla

## API para integración con otros proyectos

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/lanzar` | POST | Lanza el proceso de notificaciones |
| `/api/progreso` | GET | Estado del proceso en curso (JSON) |
| `/api/detener` | POST | Detiene el proceso |
| `/api/reporte-data` | GET | Datos de reportes en formato JSON |
| `/api/ia/mejorar` | POST | Mejora texto con IA (ortografía / análisis) |

**Autenticación requerida** en todos los endpoints (sesión Flask o token de sesión).

## Variables de entorno opcionales

```
ANTHROPIC_API_KEY=sk-ant-...   # Para funcionalidades de IA
SECRET_KEY=tu_clave_secreta    # Clave Flask (auto-generada si no se define)
```

## Dependencias principales

```
flask>=3.0
flask-sqlalchemy>=3.1
flask-login>=0.6
flask-talisman>=1.1
pandas>=2.0
openpyxl>=3.1
anthropic>=0.25
bcrypt>=4.1
```

## Historial de versiones

| Versión | Mejora principal |
|---------|-----------------|
| v1.0 | Herramienta CLI básica (solo consola, sin panel) |
| v1.5 | Panel web básico sin retroalimentación visual |
| v2.0 | Panel completo con dashboard, gráficas y log en tiempo real |
| v2.1 | Detección automática de hoja Excel por contenido |
| v2.2 | Lógica por rangos (antes solo días exactos) |
| v2.3 | Timeout IMAP + host imap-alt02.mi.com.co correcto |
| v2.4 | Plantillas email table-based (compatible Gmail/Hotmail) |
| v2.5 | Correos vencidos sin límite de días |
| v2.6 | Corrector inteligente de fechas DD/MM↔MM/DD |
| v2.7 | Copia automática en carpeta Enviados (IMAP APPEND) |

---
Desarrollado por: Isa Salazar · Ejecutiva de Cuenta · MI.COM.CO · 2026
Construido con asistencia de Claude (Anthropic)
