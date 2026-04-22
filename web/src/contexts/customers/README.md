# Bounded Context — Customers

Gestión de cartera de clientes: segmentación, perfil, historial comercial.

## Responsabilidades

- Listado y búsqueda de clientes (22k+ registros)
- Segmentación (Alto valor / Estables / Potencial / Riesgo)
- Perfil detallado por cliente (historial, scores, servicios)
- Importación / normalización desde Excel

## Capas

```
customers/
├── domain/           # Customer (Aggregate), Segment (VO), Score (VO), History (Entity)
├── application/      # ListCustomers, GetCustomerProfile, SegmentCustomers
├── infrastructure/   # CustomerApi, CustomerIndexedDB (caché local)
└── presentation/     # CustomerList, CustomerProfile, SegmentFilters
```

## Slices legacy a migrar

- `index.html` — tab "Clientes" (panel de 22,742 registros)
- `_CCLI_B64` — datos comprimidos embebidos → mover a endpoint backend
- `decompress()` loader → adapter `CustomerSnapshotRepository`
