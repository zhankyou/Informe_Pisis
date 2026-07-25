/**
 * Motor RBAC (Role-Based Access Control)
 */
document.addEventListener('DOMContentLoaded', () => {
    let rol = (sessionStorage.getItem('rol_usuario') || localStorage.getItem('rol_usuario') || 'publico').toLowerCase().trim();
    const path = window.location.pathname.toLowerCase();

    if (rol.includes('admin')) {
        rol = 'administrador';
    }

    const INTOCABLES = [
        '[href="/login"]', '[href*="login"]', '#btn-iniciar-sesion', '.btn-login',
        '[href="/logout"]', '[href="/"]', '[href="/index.html"]', '[href*="index"]',
        '.btn-inicio', '#btn-inicio', '.nav-inicio', 'app-topbar', 'app-sidebar'
    ].join(', ');

    const style = document.createElement('style');
    style.innerHTML = `${INTOCABLES} { pointer-events: auto !important; opacity: 1 !important; cursor: pointer !important; }`;
    document.head.appendChild(style);

    const bloquearElemento = (el) => {
        if (el.matches(INTOCABLES) || el.closest(INTOCABLES)) return;
        if (el.disabled && !el.hasAttribute('data-rbac-bloqueado')) return;

        el.disabled = true;
        el.style.pointerEvents = 'none';
        el.style.opacity = '0.4';
        el.classList.add('rbac-bloqueado');
        el.setAttribute('data-rbac-bloqueado', 'true');
    };

    const bloquearSelectores = (selectores) => {
        selectores.forEach(sel => {
            document.querySelectorAll(sel).forEach(bloquearElemento);
        });
    };

    const bloquearTodoVista = (excepciones = '') => {
        document.querySelectorAll('button, input, select, textarea, .action-btn, a.btn').forEach(el => {
            if (excepciones && (el.matches(excepciones) || el.closest(excepciones) || el.querySelector(excepciones))) return;
            bloquearElemento(el);
        });
    };

    const purgarVista = () => {
        document.querySelectorAll('.rbac-bloqueado, [data-rbac-bloqueado]').forEach(el => {
            el.disabled = false;
            el.style.pointerEvents = 'auto';
            el.style.opacity = '1';
            el.classList.remove('rbac-bloqueado');
            el.removeAttribute('data-rbac-bloqueado');
        });
    };

    const esVistaLibre = path.includes('formulario_acceso') || path.includes('cronograma') || path.includes('login') || path.includes('informe');

    // ADMINISTRADOR
    if (rol === 'administrador' || esVistaLibre) {
        setInterval(purgarVista, 500);
        return;
    }

    // COORDINADOR
    if (rol === 'coordinador' && (path.includes('consultas') || path.includes('ponderacion'))) {
        setInterval(purgarVista, 500);
        return;
    }

    const aplicarPoliticas = () => {
        if (rol === 'coordinador') {
            if (path === '/' || path.includes('index')) {
                bloquearSelectores(['#btn-crear-resolucion', '#btn-finalizar-ejecucion', '[data-action="crear-resolucion"]', '[data-action="finalizar-ejecucion"]']);
            }
            if (path.includes('poblacional') || path.includes('financiero')) {
                bloquearTodoVista();
            }
        }
        else if (rol === 'visualizador' || rol === 'publico') {
            if (path.includes('consultas') || path.includes('ponderacion')) {
                // Bloquea edición y guardado, pero permite visualizar, buscar y exportar PDF
                bloquearSelectores(['.btn-edit', '.btn-delete', '[onclick*="editar"]', '[onclick*="eliminar"]', 'button[type="submit"]', '#form-registro']);
            }
            else if (path.includes('poblacional') || path.includes('financiero')) {
                bloquearTodoVista();
            }
            else {
                const excepcionesGlobales = '.btn-export-pdf, .btn-pdf, [title*="PDF"], .fa-file-pdf, .btn-print, .btn-imprimir, [title*="Imprimir"], [data-action*="imprimir-acta"], .nav-rias, .btn-rias, [data-target*="rias"], [href*="rias"], [data-target*="financiero"], [href*="financiero"], .btn-financiero, [data-target*="2024"], .tab-2024, [data-year="2024"], [data-target*="2025"], .tab-2025, [data-year="2025"], [data-target*="2026"], .tab-2026, [data-year="2026"]';
                bloquearTodoVista(excepcionesGlobales);
            }
        }
    };

    aplicarPoliticas();
    new MutationObserver(aplicarPoliticas).observe(document.body, { childList: true, subtree: true });
});