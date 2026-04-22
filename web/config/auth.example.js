/**
 * config/auth.example.js — Plantilla de credenciales cliente
 *
 * Este archivo documenta la ESTRUCTURA esperada por `window.__LG_CONFIG__`.
 * NO se usa en tiempo de ejecución.
 *
 * Para habilitar login local (desarrollo):
 *   1. Copia este archivo a `config/auth.local.js`
 *   2. Reemplaza los placeholders con credenciales reales
 *   3. `auth.local.js` está listado en `.gitignore` — nunca se commitea
 *
 * En PRODUCCIÓN no uses este mecanismo. La autenticación debe delegarse al
 * backend Flask (ver carpeta `api/` y `docs/MIGRATION.md`).
 *
 * Estructura:
 *   clave  = email del usuario
 *   .p     = password (idealmente hash SHA-256, no texto plano)
 *   .n     = nombre para mostrar
 *   .a     = inicial / avatar (null para ocultar avatar, ej. roles admin)
 */
window.__LG_CONFIG__ = {
    "usuario@example.com": { p: "CHANGE_ME_PLACEHOLDER", n: "Nombre Usuario", a: "U" },
    "admin@example.com":   { p: "CHANGE_ME_PLACEHOLDER", n: "Administrador",  a: null }
};
