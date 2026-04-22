/**
 * web/config/api-client.js
 *
 * Cliente ligero al backend Flask. Vive en `config/` para cargarse desde
 * index.html (legacy) sin necesidad de bundler todavía. Cuando la migración
 * a Vite/DDD avance, este archivo se reemplaza por
 * `src/shared/infrastructure/httpClient.ts` (ya scaffoldeado).
 *
 * Expone `window.PanelAPI` con:
 *   - baseUrl: string
 *   - health(): Promise<{ok:boolean, data?:object, error?:string}>
 *   - get(path): Promise<{ok:boolean, status:number, data?:any, error?:string}>
 *   - post(path, body): idem
 *
 * Configuración: define `window.__API_BASE__` ANTES de cargar este script
 * para sobreescribir la URL (útil en staging/prod). Si no, usa el default.
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
        var url = buildUrl(path);
        var init = {
            method: method,
            credentials: 'include',
            headers: { 'Accept': 'application/json' },
        };
        if (body !== undefined) {
            init.headers['Content-Type'] = 'application/json';
            init.body = JSON.stringify(body);
        }
        return fetch(url, init).then(function (res) {
            return res.text().then(function (text) {
                var data;
                try { data = text ? JSON.parse(text) : null; } catch (e) { data = text; }
                return {
                    ok: res.ok,
                    status: res.status,
                    data: res.ok ? data : undefined,
                    error: res.ok ? undefined : (data && data.error) || res.statusText,
                };
            });
        }).catch(function (err) {
            return { ok: false, status: 0, error: err && err.message ? err.message : 'network' };
        });
    }

    window.PanelAPI = {
        baseUrl: baseUrl,
        health: function () { return request('GET', '/api/health'); },
        get:    function (path)       { return request('GET',  path); },
        post:   function (path, body) { return request('POST', path, body); },
    };

    // Health check al cargar — expone window.__API_STATUS__ (ok/offline) y
    // emite el evento `panel-api-status` para que el panel reaccione.
    function broadcast(status, detail) {
        window.__API_STATUS__ = status;
        try {
            var ev = new CustomEvent('panel-api-status', { detail: { status: status, detail: detail } });
            window.dispatchEvent(ev);
        } catch (e) { /* IE11 y similares: ignorar */ }
        // Log corto en consola para verificar desde el navegador.
        var msg = '[PanelAPI] ' + status + ' @ ' + baseUrl;
        if (status === 'ok') {
            console.info(msg, detail);
        } else {
            console.warn(msg, detail);
        }
    }

    window.PanelAPI.health().then(function (r) {
        broadcast(r.ok ? 'ok' : 'offline', r);
    });
})();
