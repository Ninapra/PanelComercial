# Bounded Context — Catalog

Catálogo de servicios, categorías y taxonomías comerciales.

## Responsabilidades

- Servicios ofrecidos (correo, hosting, SSL, dominios, etc.)
- Categorías y jerarquía
- Metadatos visibles en perfil de cliente y filtros

## Capas

```
catalog/
├── domain/           # Service, Category (entidades + VOs)
├── application/      # ListServices, GetServiceByCode, GroupByCategory
├── infrastructure/   # CatalogApi (lee de api/catalog/*), InMemoryCatalog (fallback)
└── presentation/     # ServicePicker, CategoryBadge
```

## Slices legacy a migrar

- `index.html` — taxonomía embebida de servicios
- Constantes JS con nombres y colores por servicio → domain
