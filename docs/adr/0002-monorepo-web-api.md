# ADR 0002 — Monorepo con separación web/ y api/

- **Fecha:** 2026-04-22
- **Estado:** Aceptada
- **Supera:** estructura previa con `index.html` en raíz y `micomco_panel` como carpeta suelta.

## Contexto

Antes de este cambio, el proyecto tenía:

- `index.html` en la raíz del repo (monolito frontend).
- `D:\PanelComercial\micomco_panel\` como carpeta **no versionada**, con la
  app Flask de renovaciones + notificaciones SMTP/IMAP.

Ambos piezas se desarrollan juntas, comparten dominio (renovaciones, clientes),
pero viven desacopladas y con credenciales hardcoded en ambos lados.

## Decisión

Unificar en un monorepo con dos top-level:

```
PanelComercial/
├── web/     # Frontend (index.html legacy + src/ DDD scaffold en migración)
└── api/     # Backend Flask (antes micomco_panel)
```

- `web/` se desarrolla con Vite. Durante la migración convive con
  `index.html` legacy servido tal cual.
- `api/` mantiene su estructura Flask (blueprints, templates Jinja2) pero
  todos los secretos se leen de `api/.env` (via `python-dotenv`).
- Cada módulo tiene su propio `.env.example` + `.env` gitignored.
- Las llamadas del frontend al backend usan el proxy `/api → http://127.0.0.1:5000`
  configurado en `vite.config.ts`.

## Alternativas consideradas

- **Git submódulo para `micomco_panel`:** rechazado. El historial del submódulo
  no existe (era carpeta no-git), y los submódulos añaden fricción en CI
  y especialmente en Windows.
- **Git subtree:** aplicable pero sin upstream separado hoy no aporta valor;
  preferimos copia directa + historial unificado.
- **Dos repos separados:** rechazado — las entidades de dominio (Cliente,
  Renovación) son las mismas; separar genera desincronización y duplicación
  de modelos.
- **pnpm/npm workspaces:** reservado para cuando `web/` tenga múltiples
  paquetes. Por ahora un solo `package.json` en `web/`.

## Consecuencias

**Positivas:**

- Un solo repo → un solo PR cuando una feature cruza frontend y backend.
- Secretos centralizados: dos `.env.example` claros, ambos gitignored.
- Guardrails de seguridad (`.claude/hooks/`) cubren ambos módulos.

**Negativas:**

- CI debe levantar Python + Node; pipelines más largos.
- Devs necesitan dos runtimes locales (Python 3.11+, Node 20+).
