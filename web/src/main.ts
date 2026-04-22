/**
 * Entry point de la app modular.
 *
 * Este bundle convive con `index.html` legacy durante la migración.
 * Por ahora solo valida env y expone el kernel compartido; a medida que los
 * slices del monolito se migren a bounded contexts, se montarán aquí.
 */
import { env } from '@shared/infrastructure/env';

// eslint-disable-next-line no-console
console.info(`[panel-comercial] env=${env.VITE_ENV} api=${env.VITE_API_BASE_URL}`);

// Roadmap: montar el router aquí cuando el primer bounded context esté listo.
// import { mountIdentity } from '@contexts/identity/presentation/mount';
// mountIdentity(document.getElementById('identity-root')!);

export {};
