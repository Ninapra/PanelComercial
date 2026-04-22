/**
 * Shared — Infrastructure — Env loader
 *
 * Valida `import.meta.env` al arranque con zod. Fail-fast si falta una
 * variable requerida o tiene un formato inválido.
 *
 * Úsalo desde `main.ts` antes de montar la app:
 *   import { env } from '@shared/infrastructure/env';
 *   console.log(env.VITE_API_BASE_URL);
 */
import { z } from 'zod';

const envSchema = z.object({
  VITE_API_BASE_URL: z.string().url({
    message: 'VITE_API_BASE_URL debe ser una URL válida (ej. http://127.0.0.1:5000)',
  }),
  VITE_ENV: z.enum(['development', 'staging', 'production']).default('development'),
  VITE_AUTH_STORAGE_KEY: z.string().min(1).default('pc_session'),
});

export type AppEnv = z.infer<typeof envSchema>;

function parseEnv(): AppEnv {
  const result = envSchema.safeParse(import.meta.env);
  if (!result.success) {
    // eslint-disable-next-line no-console
    console.error('[env] Configuración inválida:', result.error.flatten().fieldErrors);
    throw new Error(
      'Variables de entorno inválidas. Copia web/.env.example a web/.env y completa los valores.',
    );
  }
  return result.data;
}

export const env: AppEnv = parseEnv();
