/**
 * Shared — Domain — Result<T, E>
 *
 * Tipo de retorno funcional para casos de uso y operaciones que pueden fallar.
 * Evita throw/catch en límites de dominio: los errores son explícitos en el
 * tipo de retorno.
 *
 * Uso:
 *   function divide(a: number, b: number): Result<number, 'DIV_BY_ZERO'> {
 *     if (b === 0) return Result.fail('DIV_BY_ZERO');
 *     return Result.ok(a / b);
 *   }
 */
export type Result<T, E = Error> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: E };

export const Result = {
  ok<T>(value: T): Result<T, never> {
    return { ok: true, value };
  },
  fail<E>(error: E): Result<never, E> {
    return { ok: false, error };
  },
  isOk<T, E>(r: Result<T, E>): r is { ok: true; value: T } {
    return r.ok;
  },
  isFail<T, E>(r: Result<T, E>): r is { ok: false; error: E } {
    return !r.ok;
  },
};
