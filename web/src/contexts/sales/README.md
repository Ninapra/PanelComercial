# Bounded Context — Sales

Ciclo de venta: renovaciones, daily de contactos, transferencias.

## Responsabilidades

- Renovaciones (vencimientos, agenda, asignación por agente)
- Daily: registros de contactos de la jornada
- Transferencias: gestión y resumen

## Capas

```
sales/
├── domain/           # Renewal, DailyEntry, Transfer (agregados), Agent (VO)
├── application/      # ScheduleRenewal, LogDailyEntry, CreateTransfer, GetResumen
├── infrastructure/   # SalesApi, LocalStorageRepos (mcc_d2, mcc_t2 legacy)
└── presentation/     # RenewalsTable, DailyForm, TransfersList
```

## Slices legacy a migrar

- `index.html` — tabs "Renovaciones", "Daily", "Transferencias"
- Variables globales `_DB64`, `_TB64` → endpoints `api/ventas/*`
- `localStorage.mcc_d2`, `localStorage.mcc_t2` → sincronización con backend
