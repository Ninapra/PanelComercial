# Panel Comercial — mi.com.co

Plataforma de inteligencia comercial y gestión de renovaciones.
Monorepo con dos piezas:

```
PanelComercial/
├── web/                    # Frontend: panel monolítico en migración a DDD modular
│   ├── index.html          # Entry point (SPA vanilla, será fragmentado)
│   └── config/
│       └── auth.example.js # Plantilla de credenciales cliente (dev local)
│
├── api/                    # Backend Flask: renovaciones + notificaciones SMTP/IMAP
│   ├── app/                # Blueprints (auth, main, api, reports), modelos SQLAlchemy
│   ├── scripts/            # Motor de notificaciones (notificador_core.py)
│   ├── plantillas/         # Templates HTML de correos
│   ├── requirements.txt
│   └── .env.example        # Variables de entorno requeridas (copiar a .env)
│
├── .claude/                # Guardrails de seguridad (hooks, permisos, patrones)
├── .gitignore
├── .env.example            # Variables globales (reserva para compose/dev)
└── .gitleaks.toml
```

## Quick start

### Backend (api/)

```bash
cd api
python -m venv .venv && source .venv/bin/activate   # o .venv\Scripts\activate en Windows
pip install -r requirements.txt
cp .env.example .env                                 # completa los valores reales
python run.py                                        # http://127.0.0.1:5000
```

### Frontend (web/)

Por ahora el frontend es un archivo HTML estático. Sírvelo con cualquier servidor:

```bash
cd web
cp config/auth.example.js config/auth.local.js      # completa credenciales dev
python -m http.server 8080                           # http://127.0.0.1:8080
```

El scaffold Vite + TypeScript + DDD se añade en el siguiente commit del roadmap.

## Seguridad

- **Nunca** hardcodees credenciales. Los hooks en `.claude/hooks/` bloquean commits con secretos (patrones en `.claude/hooks/secret-patterns.json`).
- Auth client-side del `web/` es **transitorio**. Producción debe delegar autenticación al backend (ver `docs/MIGRATION.md`).
- `api/.env`, `web/config/auth.local.js` y `.env` están en `.gitignore`.

## Git flow

- `main` — producción
- `develop` — integración (base de features)
- `feature/*` — trabajo en curso
- `release/*`, `hotfix/*` — estándar gitflow

## Guardrails

Configuración alineada al estándar [ccicode/claude-guardrails](https://github.com/ccicode/claude-guardrails).
Ver `.claude/settings.json` para permisos y hooks activos.
