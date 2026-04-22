/**
 * web/config/api-client.js
 *
 * Cliente ligero al backend Flask. Expone `window.PanelAPI` consumido por
 * el login del panel master (index.html), el health check y cualquier
 * llamada server-side desde el cliente legacy.
 *
 * API pública:
 *   PanelAPI.baseUrl               string
 *   PanelAPI.health()              Promise<{ok,data?,error?}>
 *   PanelAPI.get(path)             Promise<{ok,status,data?,error?}>
 *   PanelAPI.post(path, body)      Promise<{ok,status,data?,error?}>
 *
 * Eventos:
 *   `panel-api-status` — se emite al terminar el health check inicial
 *     detail: { status: 'ok' | 'offline', detail: {...} }
 *
 * Configuración:
 *   - window.__API_BASE__  → sobreescribe URL base (default http://127.0.0.1:5000)
 *
 * Reemplazo futuro: `src/shared/infrastructure/httpClient.ts` cuando el
 * scaffold DDD esté activo (ver docs/MIGRATION.md).
 */
(function () {
    'use strict';

    var DEFAULT_BASE = 'http://127.0.0.1:5000';
    var baseUrl = (typeof window !== 'undefined' && window.__API_BASE__) || DEFAULT_BASE;
    baseUrl = baseUrl.replace(/\/+$/, '');

    function buildUrl(path) {
        if (!path) return baseUrl;
        return baseUrl + (path.charAt(0) === '/' ? path : '/' + path);
    }

    function request(method, path, body) {
        var init = {
            method: method,
            credentials: 'include',
            headers: { 'Accept': 'application/json' }
        };
        if (body !== undefined) {
            init.headers['Content-Type'] = 'application/json';
            init.body = JSON.stringify(body);
        }
        return fetch(buildUrl(path), init).then(function (res) {
            return res.text().then(function (text) {
                var data;
                try { data = text ? JSON.parse(text) : null; } catch (e) { data = text; }
                return {
                    ok: res.ok,
                    status: res.status,
                    data: res.ok ? data : (typeof data === 'object' ? data : undefined),
                    error: res.ok ? undefined : ((data && data.error) || res.statusText)
                };
            });
        }).catch(function (err) {
            return { ok: false, status: 0, error: err && err.message ? err.message : 'network' };
        });
    }

    function broadcast(status, detail) {
        window.__API_STATUS__ = status;
        try {
            var ev = new CustomEvent('panel-api-status', { detail: { status: status, detail: detail } });
            window.dispatchEvent(ev);
        } catch (e) { /* IE y similares: ignorar */ }
        var msg = '[PanelAPI] ' + status + ' @ ' + baseUrl;
        if (status === 'ok') console.info(msg); else console.warn(msg, detail);
    }

    window.PanelAPI = {
        baseUrl: baseUrl,
        health: function () { return request('GET',  '/api/health'); },
        get:    function (path)       { return request('GET',  path); },
        post:   function (path, body) { return request('POST', path, body); }
    };

    // Health check inicial — el panel puede reaccionar al evento
    // `panel-api-status` para mostrar fallback si el backend no responde.
    window.PanelAPI.health().then(function (r) {
        broadcast(r.ok ? 'ok' : 'offline', r);
    });
})();
