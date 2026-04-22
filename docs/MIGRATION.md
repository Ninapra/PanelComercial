# Plan de migración: monolito → DDD modular

Guía operativa para cortar `web/index.html` (4,155 líneas vanilla JS) en
bounded contexts **sin romper el panel durante el trabajo**.

## Principios

1. **El panel nunca queda roto.** Cada PR deja la app funcional.
2. **Un slice a la vez.** No migrar dos contextos en paralelo en el mismo PR.
3. **Borra al migrar.** Cuando un bloque legacy ya vive en `src/contexts/<ctx>/`,
   se elimina del `index.html` en el mismo PR.
4. **Tests antes de refactor.** Caso de uso con test > código movido sin tests.
5. **Sin secretos — nunca.** Los hooks en `.claude/hooks/` bloquean el commit.

## Fases

### Fase 0 — Completada ✅

- [x] Guardrails de seguridad instalados (`749b2a3`).
- [x] Gitflow establecido (main / develop / feature/*).
- [x] Credenciales `_LG` extraídas a `web/config/auth.local.js` (gitignored).
- [x] Monorepo `web/` + `api/`. Secretos del backend a `.env`.
- [x] Scaffold DDD con 5 bounded contexts.

### Fase 1 — Baseline y bundling

- [ ] Instalar dependencias de `web/` (`npm install`).
- [ ] Ejecutar smoke test manual del panel legacy. Documentar 10-15
      flujos críticos en `docs/smoke-tests.md`.
- [ ] Extraer el bloque `<style>` de `index.html` a `src/styles/legacy.css`;
      importarlo desde `main.ts`.
- [ ] Extraer el bloque `<script>` monolítico a `src/legacy/main.js`;
      referenciarlo desde `index.html` con `<script type="module" src="/src/legacy/main.js">`.
- [ ] Confirmar que `npm run build` genera un bundle funcional.

### Fase 2 — Shared kernel robusto

- [ ] Endpoint de salud en `api/routes/api.py` (`GET /api/health`).
- [ ] `httpClient` con tests (`vitest` + `msw`).
- [ ] `env.ts` con tests y mensajes de error claros.
- [ ] `AuthStorage` (adapter de sesión) en `shared/infrastructure/`.

### Fase 3 — Identity (bloqueante de todo lo demás)

- [ ] Backend: `POST /api/auth/login` retorna JWT o session cookie.
- [ ] Frontend: `contexts/identity/domain/User.ts`, `Session.ts`.
- [ ] `contexts/identity/application/LoginUseCase.ts` con test.
- [ ] `contexts/identity/infrastructure/AuthApi.ts`.
- [ ] `contexts/identity/presentation/LoginForm.ts` (Web Component).
- [ ] Reemplazar bloque `_LG` + `lgIn()` en `index.html` por mount point
      del nuevo LoginForm. **Eliminar** `config/auth.local.js` y su `<script>`.

### Fase 4 — Reporting (mayor valor visible)

- [ ] Backend: endpoints `/api/reportes/dashboard`, `/api/reportes/registros`.
- [ ] Migrar cálculos de KPI y filtros a `reporting/application/`.
- [ ] Reemplazar tabs "Inicio" y "Registros" en `index.html`.

### Fase 5 — Customers

- [ ] Backend: endpoint `/api/customers` con paginación (22k+ registros).
- [ ] Quitar `_CCLI_B64` embebido en `index.html`.
- [ ] Migrar tab "Clientes" a bounded context.

### Fase 6 — Sales (renovaciones + daily + transferencias)

- [ ] Backend: endpoints `/api/ventas/renovaciones`, `/daily`, `/transferencias`.
- [ ] Sincronizar `localStorage.mcc_d2` / `mcc_t2` con backend.
- [ ] Migrar tabs correspondientes.

### Fase 7 — Catalog

- [ ] Backend: `/api/catalog/servicios`, `/api/catalog/categorias`.
- [ ] Mover taxonomía embebida del monolito a BD.

### Fase 8 — Apagado del legacy

- [ ] `index.html` queda como shell mínimo (head + mount points).
- [ ] Borrar `src/legacy/`.
- [ ] Eliminar `sessionStorage._mcu` y cualquier estado client-side sensible.
- [ ] ADR 0003 — "Migración completada, congelamiento de arquitectura".

## Reglas de oro durante cada fase

- **Una feature por PR.** Base `develop`, título `feat(<contexto>): <slice>`.
- **Test del caso de uso obligatorio** antes de migrar un bloque.
- **Sin `--no-verify` en git.** El hook lo bloquea; si un hook falla, arregla
  la causa.
- **Sin strings de credenciales en código.** Placeholders con `example`,
  `your-...-here`, `change-me`.
- **Comentario en cada PR:** qué bloque legacy se borró (referencia por línea).
