# ADR 0001 — Arquitectura DDD modular para el panel comercial

- **Fecha:** 2026-04-22
- **Estado:** Aceptada
- **Autores:** Nina, equipo Panel Comercial

## Contexto

El panel comercial vive hoy como un `index.html` monolítico de ~4,155
líneas (4.88 MB con datos embebidos), vanilla JS sin framework, con:

- Login client-side y credenciales hardcoded (ya extraídas — ver commit `749b2a3`).
- Datos de clientes, renovaciones y daily embebidos en base64+gzip.
- 6 tabs como ruteo manual (`showTab()`).
- Persistencia en `localStorage` / `sessionStorage`.

El equipo necesita:

1. Poder iterar sin miedo a romper partes no relacionadas.
2. Separar responsabilidades para que distintos devs trabajen en paralelo.
3. Test coverage sobre reglas de negocio (KPIs, segmentación, cálculos).
4. Eliminar credenciales en el repo de forma permanente.

## Decisión

Adoptar **Domain-Driven Design tactical** con 5 bounded contexts:

| Contexto     | Propósito                                       |
|--------------|-------------------------------------------------|
| `identity`   | Autenticación, sesión, roles                    |
| `catalog`    | Servicios, categorías, taxonomías               |
| `sales`      | Renovaciones, daily, transferencias             |
| `customers`  | Cartera (22k+), segmentación, perfil            |
| `reporting`  | Dashboards, KPIs, exportes                      |

Cada contexto tiene 4 capas: `domain` / `application` / `infrastructure` /
`presentation`. Regla de dependencias: `presentation → application → domain`,
con `infrastructure` implementando interfaces definidas en `domain`. Cross-
context solo vía `application` pública (a enforcer con ESLint
`no-restricted-imports`).

## Stack técnico

- **Vite 5** + **TypeScript 5 strict** — bundler moderno, tipado no negociable.
- **Zod** — validación de env y DTOs de red.
- **Vitest** — tests co-ubicados con cada contexto.
- **Tailwind CSS** — utility-first, evita bikeshedding de naming.
- **Prettier + ESLint** — formato y reglas arquitectónicas.

No se adopta framework SPA pesado (React/Vue). La estrategia es *islands*:
Web Components o Lit en puntos puntuales del HTML renderizado por el
backend. Esto permite coexistencia con el monolito durante la migración.

## Alternativas consideradas

- **Reescritura completa con Next.js/Remix:** descartado — tiempo prohibitivo,
  y el backend Flask ya renderiza bien HTML.
- **Hexagonal/Clean sin bounded contexts:** insuficiente para aislar ventas
  de renovaciones y clientes — los agregados son distintos.
- **Microfrontends:** overkill para un equipo pequeño y un monorepo.

## Consecuencias

**Positivas:**

- Cada feature nueva vive en un contexto claro; onboarding < 1 día.
- Tests de dominio no requieren DOM ni fetch.
- Reglas ESLint previenen acoplamiento cross-context.

**Negativas:**

- Curva inicial: el equipo debe internalizar la regla de dependencias.
- Boilerplate (use cases explícitos, DTOs, adapters).
- Duplicación controlada entre contextos (Money, Email como VOs locales
  o compartidos en `shared/domain`).
