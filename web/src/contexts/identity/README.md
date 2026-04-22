# Bounded Context — Identity

Autenticación, sesión y roles del usuario comercial.

## Responsabilidades

- Login / logout
- Gestión de sesión (storage key, expiración)
- Autorización por rol (admin / agente)
- Proxy al backend Flask (`api/app/routes/auth.py`) — no valida credenciales client-side en producción

## Capas

```
identity/
├── domain/           # User, Role, Session (entidades + VOs), AuthEvent
├── application/      # LoginUseCase, LogoutUseCase, RequireAuth guard
├── infrastructure/   # AuthApi (HTTP), SessionStorage (localStorage)
└── presentation/     # LoginForm, SessionGuard, avatars
```

## Slices legacy a migrar

- `index.html:2586-2670` — login UI + `_LG` loader + `lgIn()` + sessionStorage `_mcu`
- `index.html` — avatar / top bar con iniciales

## Decisiones

- Sesión persiste en `localStorage` con clave `env.VITE_AUTH_STORAGE_KEY`.
- Credenciales **nunca** viajan al bundle. El login hace POST al backend.
- `config/auth.local.js` es transitorio y solo dev.
