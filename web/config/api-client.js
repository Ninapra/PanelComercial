/**
 * web/config/api-client.js
 *
 * Cliente ligero al backend Flask + submenú flotante "Renovaciones".
 * Vive en `config/` para cargarse desde index.html (legacy) sin bundler.
 *
 * Expone `window.PanelAPI` con:
 *   - baseUrl: string
 *   - health(): Promise<{ok, data?, error?}>
 *   - get(path) / post(path, body): Promise<{ok, status, data?, error?}>
 *   - openSubmenu() / closeSubmenu(): control programático del menú
 *
 * Configuración:
 *   - `window.__API_BASE__`  → sobreescribe URL base (default: http://127.0.0.1:5000)
 *   - `window.__API_MENU__ = false` ANTES de cargar para desactivar el menú visual
 *
 * Reemplazo futuro: `src/shared/infrastructure/httpClient.ts` cuando Vite esté activo.
 */
(function () {
    'use strict';

    // ── Config ────────────────────────────────────────────────────────────
    var DEFAULT_BASE = 'http://127.0.0.1:5000';
    var baseUrl = (typeof window !== 'undefined' && window.__API_BASE__) || DEFAULT_BASE;
    baseUrl = baseUrl.replace(/\/+$/, '');
    var MENU_ENABLED = (typeof window === 'undefined' || window.__API_MENU__ !== false);

    // Rutas del backend Flask. Orden = orden de aparición en el submenú.
    var BACKEND_LINKS = [
        { label: 'Dashboard',       path: '/',               icon: '📊' },
        { label: 'Notificaciones',  path: '/notificaciones', icon: '📧' },
        { label: 'Cargar Excel',    path: '/cargar-excel',   icon: '📥' },
        { label: 'Reportes',        path: '/reportes/',      icon: '📈' },
        { label: 'Logs',            path: '/logs',           icon: '🗒️' },
        { label: 'Configuración',   path: '/configuracion',  icon: '⚙️' }
    ];

    // ── HTTP ──────────────────────────────────────────────────────────────
    function buildUrl(path) {
        if (!path) return baseUrl;
        return baseUrl + (path.charAt(0) === '/' ? path : '/' + path);
    }

    function request(method, path, body) {
        var init = { method: method, credentials: 'include', headers: { 'Accept': 'application/json' } };
        if (body !== undefined) {
            init.headers['Content-Type'] = 'application/json';
            init.body = JSON.stringify(body);
        }
        return fetch(buildUrl(path), init).then(function (res) {
            return res.text().then(function (text) {
                var data;
                try { data = text ? JSON.parse(text) : null; } catch (e) { data = text; }
                return {
                    ok: res.ok, status: res.status,
                    data: res.ok ? data : undefined,
                    error: res.ok ? undefined : (data && data.error) || res.statusText
                };
            });
        }).catch(function (err) {
            return { ok: false, status: 0, error: err && err.message ? err.message : 'network' };
        });
    }

    // ── Submenú flotante ──────────────────────────────────────────────────
    var menuRoot = null;
    var menuDot  = null;
    var menuList = null;
    var menuBtn  = null;
    var menuOpen = false;

    function injectStyles() {
        if (document.getElementById('panel-api-styles')) return;
        var css = [
            '#panel-api-menu{position:fixed;bottom:20px;right:20px;z-index:99999;font-family:Inter,system-ui,-apple-system,Segoe UI,sans-serif}',
            '#panel-api-menu *{box-sizing:border-box}',
            '#panel-api-menu .pam-btn{display:flex;align-items:center;gap:8px;padding:10px 14px;background:#fff;border:1px solid #e2e8f0;border-radius:999px;box-shadow:0 4px 14px rgba(15,23,42,.08);cursor:pointer;color:#0f172a;font-size:13px;font-weight:500;transition:all .15s ease}',
            '#panel-api-menu .pam-btn:hover{box-shadow:0 6px 20px rgba(15,23,42,.12);transform:translateY(-1px)}',
            '#panel-api-menu .pam-dot{width:8px;height:8px;border-radius:50%;background:#94a3b8;box-shadow:0 0 0 3px rgba(148,163,184,.25);transition:all .2s ease}',
            '#panel-api-menu[data-status="ok"] .pam-dot{background:#16a34a;box-shadow:0 0 0 3px rgba(22,163,74,.22)}',
            '#panel-api-menu[data-status="offline"] .pam-dot{background:#dc2626;box-shadow:0 0 0 3px rgba(220,38,38,.22)}',
            '#panel-api-menu .pam-caret{margin-left:2px;transition:transform .2s ease;color:#64748b}',
            '#panel-api-menu[data-open="true"] .pam-caret{transform:rotate(180deg)}',
            '#panel-api-menu .pam-list{display:none;position:absolute;bottom:calc(100% + 8px);right:0;min-width:240px;background:#fff;border:1px solid #e2e8f0;border-radius:12px;box-shadow:0 10px 30px rgba(15,23,42,.15);padding:6px;overflow:hidden}',
            '#panel-api-menu[data-open="true"] .pam-list{display:block}',
            '#panel-api-menu .pam-header{padding:10px 12px 6px;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#64748b;font-weight:600}',
            '#panel-api-menu .pam-header small{font-weight:400;text-transform:none;letter-spacing:0;color:#94a3b8;display:block;margin-top:2px;font-size:11px}',
            '#panel-api-menu a.pam-link{display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:8px;text-decoration:none;color:#0f172a;font-size:13px;font-weight:500;transition:background .12s ease}',
            '#panel-api-menu a.pam-link:hover{background:#f1f5f9}',
            '#panel-api-menu a.pam-link .pam-icon{width:20px;text-align:center;font-size:14px}',
            '#panel-api-menu .pam-divider{height:1px;background:#e2e8f0;margin:6px 8px}',
            '#panel-api-menu .pam-foot{padding:8px 12px;font-size:11px;color:#94a3b8}',
            '#panel-api-menu .pam-foot code{background:#f1f5f9;padding:1px 5px;border-radius:3px;color:#0f172a;font-size:11px}'
        ].join('');
        var style = document.createElement('style');
        style.id = 'panel-api-styles';
        style.textContent = css;
        document.head.appendChild(style);
    }

    function buildMenu() {
        if (!MENU_ENABLED) return;
        if (menuRoot) return;
        injectStyles();

        menuRoot = document.createElement('div');
        menuRoot.id = 'panel-api-menu';
        menuRoot.setAttribute('data-status', 'checking');
        menuRoot.setAttribute('data-open', 'false');

        menuBtn = document.createElement('button');
        menuBtn.type = 'button';
        menuBtn.className = 'pam-btn';
        menuBtn.setAttribute('aria-expanded', 'false');
        menuDot = document.createElement('span');
        menuDot.className = 'pam-dot';
        var label = document.createElement('span');
        label.textContent = 'Renovaciones';
        var caret = document.createElement('span');
        caret.className = 'pam-caret';
        caret.textContent = '▾';
        menuBtn.appendChild(menuDot);
        menuBtn.appendChild(label);
        menuBtn.appendChild(caret);
        menuBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            setOpen(!menuOpen);
        });

        menuList = document.createElement('div');
        menuList.className = 'pam-list';
        menuList.setAttribute('role', 'menu');

        var header = document.createElement('div');
        header.className = 'pam-header';
        header.innerHTML = 'Panel de Renovaciones<small id="pam-status-text">Verificando conexión...</small>';
        menuList.appendChild(header);

        var divider = document.createElement('div');
        divider.className = 'pam-divider';
        menuList.appendChild(divider);

        BACKEND_LINKS.forEach(function (link) {
            var a = document.createElement('a');
            a.className = 'pam-link';
            a.href = baseUrl + link.path;
            a.target = '_blank';
            a.rel = 'noopener noreferrer';
            a.setAttribute('role', 'menuitem');
            a.innerHTML = '<span class="pam-icon">' + link.icon + '</span><span>' + link.label + '</span>';
            menuList.appendChild(a);
        });

        var divider2 = document.createElement('div');
        divider2.className = 'pam-divider';
        menuList.appendChild(divider2);

        var foot = document.createElement('div');
        foot.className = 'pam-foot';
        foot.innerHTML = 'API: <code>' + baseUrl + '</code>';
        menuList.appendChild(foot);

        menuRoot.appendChild(menuList);
        menuRoot.appendChild(menuBtn);
        document.body.appendChild(menuRoot);

        // Click fuera cierra el menú
        document.addEventListener('click', function (e) {
            if (menuOpen && !menuRoot.contains(e.target)) setOpen(false);
        });
        // Escape cierra
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && menuOpen) setOpen(false);
        });
    }

    function setOpen(v) {
        menuOpen = !!v;
        if (menuRoot) {
            menuRoot.setAttribute('data-open', menuOpen ? 'true' : 'false');
            if (menuBtn) menuBtn.setAttribute('aria-expanded', menuOpen ? 'true' : 'false');
        }
    }

    function updateMenuStatus(status, detail) {
        if (!menuRoot) return;
        menuRoot.setAttribute('data-status', status);
        var txt = document.getElementById('pam-status-text');
        if (txt) {
            if (status === 'ok') {
                var t = (detail && detail.data && detail.data.time) ? new Date(detail.data.time).toLocaleTimeString() : '';
                txt.textContent = 'Conectado' + (t ? ' · ' + t : '');
            } else if (status === 'offline') {
                txt.textContent = 'Sin conexión · ' + (detail && detail.error ? detail.error : 'verifica el backend');
            } else {
                txt.textContent = 'Verificando conexión...';
            }
        }
    }

    // ── Status broadcasting ───────────────────────────────────────────────
    function broadcast(status, detail) {
        window.__API_STATUS__ = status;
        try {
            var ev = new CustomEvent('panel-api-status', { detail: { status: status, detail: detail } });
            window.dispatchEvent(ev);
        } catch (e) { /* IE11: ignorar */ }
        var msg = '[PanelAPI] ' + status + ' @ ' + baseUrl;
        if (status === 'ok') console.info(msg, detail); else console.warn(msg, detail);
        updateMenuStatus(status, detail);
    }

    // ── Public API ────────────────────────────────────────────────────────
    window.PanelAPI = {
        baseUrl: baseUrl,
        health: function () { return request('GET', '/api/health'); },
        get:    function (path)       { return request('GET',  path); },
        post:   function (path, body) { return request('POST', path, body); },
        openSubmenu:  function () { setOpen(true); },
        closeSubmenu: function () { setOpen(false); }
    };

    // ── Bootstrap ─────────────────────────────────────────────────────────
    function boot() {
        buildMenu();
        window.PanelAPI.health().then(function (r) {
            broadcast(r.ok ? 'ok' : 'offline', r);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();
