/**
 * Shared — Infrastructure — HTTP Client
 *
 * Fetch wrapper delgado con baseURL y manejo de errores uniforme.
 * Las implementaciones de Repository en cada bounded context lo consumen
 * para hablar con el backend Flask (api/).
 */
import { env } from './env';
import { Result } from '../domain/Result';

export interface HttpError {
  readonly status: number;
  readonly message: string;
  readonly body?: unknown;
}

export interface HttpClient {
  get<T>(path: string): Promise<Result<T, HttpError>>;
  post<T>(path: string, body: unknown): Promise<Result<T, HttpError>>;
}

function buildUrl(path: string): string {
  const base = env.VITE_API_BASE_URL.replace(/\/$/, '');
  const suffix = path.startsWith('/') ? path : `/${path}`;
  return `${base}${suffix}`;
}

async function request<T>(input: RequestInfo, init?: RequestInit): Promise<Result<T, HttpError>> {
  try {
    const response = await fetch(input, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
      ...init,
    });
    const text = await response.text();
    const body = text ? (JSON.parse(text) as unknown) : undefined;
    if (!response.ok) {
      return Result.fail({ status: response.status, message: response.statusText, body });
    }
    return Result.ok(body as T);
  } catch (err) {
    return Result.fail({ status: 0, message: err instanceof Error ? err.message : 'network' });
  }
}

export const httpClient: HttpClient = {
  get: (path) => request(buildUrl(path), { method: 'GET' }),
  post: (path, body) => request(buildUrl(path), { method: 'POST', body: JSON.stringify(body) }),
};
