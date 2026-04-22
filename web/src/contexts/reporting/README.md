# Bounded Context — Reporting

Dashboards, KPIs, exportes y vistas agregadas. Este es el contexto más visible
del panel — consume datos de los demás pero no muta estado.

## Responsabilidades

- Dashboard de inicio (KPIs, metas Baja/Alta/Plus)
- Registros (auditoría, filtros, export CSV)
- Reportes por periodo (semanal / quincenal / mensual)

## Capas

```
reporting/
├── domain/           # Kpi, Period (VO), GoalTier (enum), DateRange
├── application/      # ComputeDashboardKpis, ExportRegisters, BuildPeriodReport
├── infrastructure/   # ReportingApi, CsvExporter
└── presentation/     # DashboardGrid, KpiCard, RegistersTable, ExportButton
```

## Slices legacy a migrar

- `index.html` — tab "Inicio" (dashboard), "Registros"
- Cálculos de KPI inline → use cases testables
- Export CSV inline → `CsvExporter` adapter
