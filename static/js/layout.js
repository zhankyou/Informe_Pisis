// ==============================================================================
// COMPONENTES WEB - SISTEMA INFORME APS (RESPONSIVE & COLOR FIX)
// ==============================================================================

class AppSidebar extends HTMLElement {
  connectedCallback() {
    const activeMenu = this.getAttribute('active-menu') || '';

    // Sanitización robusta del rol
    const rolRaw = sessionStorage.getItem('rol_usuario') || localStorage.getItem('rol_usuario') || 'publico';
    const rol = rolRaw.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();

    // Validación RBAC
    const isAdmin = rol.includes('admin') || rol.includes('coordinador') || localStorage.getItem('isAdmin') === 'true';

    let adminMenus = '';
    let adminComponentes = '';

    if (rol !== 'publico') {
        adminComponentes = `<a href="/indicadores_componentes" class="sub-item ${activeMenu === 'indicadores_componentes' ? 'active' : ''}">↳ Indicadores Componentes</a>`;

        adminMenus = `
          <div class="nav-item-title" style="margin-top: 15px; font-weight: 700; color: white;">📁 Resolución SER124DREC</div>
          <a href="/poblacional" class="sub-item ${activeMenu === 'poblacional' ? 'active' : ''}">📄 Poblacional (SI-APS)</a>
          <a href="/financiero" class="sub-item ${activeMenu === 'financiero' ? 'active' : ''}">💰 Financiero (SER124)</a>
          <a href="/consultas" class="sub-item-child ${activeMenu === 'consultas' ? 'active' : ''}">↳ 🔍 Auditoría (SER124)</a>

          <div class="nav-item-title" style="margin-top: 15px; font-weight: 700; color: white;">📁 Gestión Humana y Pagos</div>
          <a href="/ponderacion" class="sub-item ${activeMenu === 'ponderacion' ? 'active' : ''}">📊 Matriz de Ponderación</a>
          <a href="/seguimiento_pagos" class="sub-item ${activeMenu === 'seguimiento_pagos' ? 'active' : ''}">💵 Seguimiento Pagos</a>
        `;
    }

    let consultaAutorizaciones = '';
    if (isAdmin) {
        consultaAutorizaciones = `<a href="/consulta_acceso" class="sub-item ${activeMenu === 'consulta_acceso' ? 'active' : ''}">↳ 🔍 Consulta Autorizaciones</a>`;
    }

    this.innerHTML = `
      <div id="sidebar-overlay" class="sidebar-overlay" onclick="toggleSidebar()"></div>
      <div id="sidebar-container" class="sidebar-internal">
        <div class="brand">
          <div>
            <img src="/static/img/logo-ese.png" alt="Logo ESE">
            <span>INFORME APS</span>
          </div>
          <button class="mobile-close-btn" onclick="toggleSidebar()"><i class="fas fa-times"></i></button>
        </div>
        <div class="nav-menu">
          <a href="/" class="nav-item ${activeMenu === 'dashboard' ? 'active' : ''}">📊 Dashboard General</a>
          <a href="/informe" class="nav-item ${activeMenu === 'informe' ? 'active' : ''}">📈 Informe Entidades</a>
          
          <div class="nav-item-title" style="margin-top: 15px; font-weight: 700; color: white;">📋 Autorizaciones PISIS</div>
          <a href="/formulario_acceso" class="sub-item ${activeMenu === 'formulario_acceso' ? 'active' : ''}">📝 Diligenciar Acceso</a>
          ${consultaAutorizaciones}

          <div class="nav-item-title" style="margin-top: 15px; font-weight: 700; color: white;">📈 INDICADORES APS</div>
          <a href="/indicadores_cobertura" class="sub-item ${activeMenu === 'indicadores_cobertura' ? 'active' : ''}">↳ Indicadores Cobertura</a>
          ${adminComponentes}

          ${adminMenus}
          
          <div class="nav-item-title" style="margin-top: 15px; font-weight: 700; color: white;">📅 Cronograma (EBS)</div>
          <a href="/cronograma" class="sub-item ${activeMenu === 'cronograma' ? 'active' : ''}">📍 Programación Operativa</a>
        </div>
      </div>
      <style>
        app-sidebar {
            position: fixed;
            top: 0; left: 0;
            height: 100vh;
            z-index: 1000;
        }
        .sidebar-internal { 
            width: 260px; 
            background: #0a1f3d; 
            color: white; 
            height: 100vh; 
            position: absolute; 
            top: 0; left: 0; 
            overflow-y: auto; 
            padding-bottom: 20px; 
            transition: transform 0.3s ease;
            box-shadow: 2px 0 10px rgba(0,0,0,0.2);
            display: flex;
            flex-direction: column;
        }
        .brand {
            display: flex; justify-content: space-between; align-items: center; 
            padding: 20px 15px; border-bottom: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 10px;
        }
        .brand div { display: flex; align-items: center; gap: 10px; }
        .brand img { max-height: 40px; width: auto; object-fit: contain; }
        .brand span { font-weight: bold; white-space: nowrap; }
        .nav-menu { padding: 0 15px; display: flex; flex-direction: column; gap: 6px; }
        
        .nav-item-title { padding: 5px 15px; font-size: 0.85rem; }
        
        /* FIX DE COLORES PARA NAV-ITEM */
        .nav-item { color: #ffffff !important; text-decoration: none; padding: 10px 15px; border-radius: 6px; transition: 0.2s; display: block; white-space: nowrap; }
        .nav-item:hover { background: rgba(255,255,255,0.1); color: #ffffff !important; }
        .nav-item.active { background: #00b09b !important; color: #ffffff !important; font-weight: bold; }
        
        .sub-item { color: #d1d5db; text-decoration: none; padding: 8px 15px 8px 30px; font-size: 0.9rem; border-radius: 6px; display: block; white-space: nowrap; }
        .sub-item:hover { background: rgba(255,255,255,0.05); color: #ffffff; }
        .sub-item.active { color: #00b09b !important; font-weight: bold; }
        
        .sub-item-child { color: #9ca3af; text-decoration: none; padding: 8px 15px 8px 45px; font-size: 0.85rem; border-radius: 6px; display: block; white-space: nowrap; }
        .sub-item-child:hover { color: #ffffff; }
        
        .sidebar-overlay { 
            display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; 
            background: rgba(0,0,0,0.6); z-index: -1; opacity: 0; transition: opacity 0.3s ease;
        }
        .mobile-close-btn { 
            display: none; background: none; border: none; color: white; 
            font-size: 1.5rem; cursor: pointer; padding: 5px;
        }

        /* COMPORTAMIENTO MÓVIL ESTRICTO */
        @media (max-width: 768px) {
            app-sidebar { width: 0; overflow: visible; }
            .sidebar-internal { transform: translateX(-100%); }
            .sidebar-internal.open { transform: translateX(0); }
            .sidebar-overlay.open { display: block; opacity: 1; }
            .mobile-close-btn { display: block; }
        }
      </style>
    `;
  }
}

class AppTopbar extends HTMLElement {
  connectedCallback() {
    const titulo = this.getAttribute('titulo') || 'Módulo Principal';
    const rolRaw = sessionStorage.getItem('rol_usuario') || localStorage.getItem('rol_usuario') || 'publico';
    const userRaw = sessionStorage.getItem('username') || localStorage.getItem('username') || '';

    const rolNormalizado = rolRaw.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();
    const esPublico = rolNormalizado === 'publico';

    const rol = rolRaw.toUpperCase().replace('ADMIN', 'ADMINISTRADOR');
    const usuario = userRaw ? userRaw.toUpperCase() : 'INVITADO';

    const userLabel = esPublico ? '<span class="hide-mobile">👤 VISTA PÚBLICA</span>' : `<span class="hide-mobile">👤 ${usuario} | Rol: <span style="color: #3b82f6;">${rol}</span></span>`;

    const btnAccion = !esPublico
        ? `<button class="btn-logout" onclick="cerrarSesion()"><i class="fas fa-sign-out-alt"></i> <span class="hide-mobile">Cerrar Sesión</span></button>`
        : `<button class="btn-logout" style="background: var(--teal, #00b09b);" onclick="window.location.href='/login'"><i class="fas fa-sign-in-alt"></i> <span class="hide-mobile">Iniciar Sesión</span></button>`;

    this.innerHTML = `
      <div class="topbar-internal">
        <div class="topbar-left">
            <button class="mobile-menu-btn" onclick="toggleSidebar()"><i class="fas fa-bars"></i></button>
            <span class="topbar-title">${titulo}</span>
        </div>
        <div class="topbar-right">
          <span class="user-label">${userLabel}</span>
          ${btnAccion}
        </div>
      </div>
      <style>
        app-topbar { display: block; width: 100%; }
        .topbar-internal { 
            display: flex; justify-content: space-between; align-items: center; 
            background: white; padding: 15px 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); 
            margin-left: 260px; transition: margin-left 0.3s ease; box-sizing: border-box;
        }
        .topbar-left { display: flex; align-items: center; gap: 15px; }
        .topbar-title { color: #004b87; font-size: 1.4rem; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .topbar-right { display: flex; align-items: center; gap: 15px; }
        .user-label { font-size: 0.85rem; color: #6c757d; font-weight: 700; }
        
        .btn-logout { background: #dc3545; color: white; border: none; padding: 8px 15px; border-radius: 6px; cursor: pointer; font-weight: bold; display: flex; align-items: center; gap: 8px; transition: 0.2s; white-space: nowrap; }
        .btn-logout:hover { opacity: 0.9; }
        .mobile-menu-btn { display: none; background: none; border: none; font-size: 1.5rem; color: #004b87; cursor: pointer; padding: 5px; }

        @media (max-width: 768px) {
            .topbar-internal { margin-left: 0; padding: 15px; width: 100%; }
            .mobile-menu-btn { display: block; }
            .hide-mobile { display: none; }
            .topbar-title { font-size: 1.1rem; }
        }
      </style>
    `;
  }
}

customElements.define('app-sidebar', AppSidebar);
customElements.define('app-topbar', AppTopbar);

// ============================================================================
// LÓGICA DE INTERACCIÓN MÓVIL
// ============================================================================
window.toggleSidebar = function() {
    const sidebar = document.querySelector('app-sidebar #sidebar-container');
    const overlay = document.querySelector('app-sidebar #sidebar-overlay');
    if (sidebar) sidebar.classList.toggle('open');
    if (overlay) overlay.classList.toggle('open');
};

window.cerrarSesion = function() {
    sessionStorage.clear();
    localStorage.clear();
    window.location.href = '/';
};

// ============================================================================
// INYECCIÓN DE CSS GLOBAL PARA RESETEAR LAYOUT.CSS EN MÓVILES
// ============================================================================
const globalResponsiveFix = document.createElement('style');
globalResponsiveFix.textContent = `
    body, html { margin: 0; padding: 0; overflow-x: hidden; width: 100%; }
    .main-content { margin-left: 260px; transition: margin-left 0.3s ease; box-sizing: border-box; }
    
    @media (max-width: 768px) {
        .main-content { margin-left: 0 !important; width: 100% !important; padding-bottom: 20px; }
        
        /* Ajuste estructural para Tablas y Formularios */
        .toolbar { flex-direction: column !important; align-items: stretch !important; gap: 10px !important; padding: 15px !important; margin: 10px !important; }
        .toolbar .form-group { width: 100%; }
        .toolbar .form-group select, .toolbar .form-group input { width: 100%; box-sizing: border-box; }
        .btn-action { width: 100%; }
        
        .table-container { margin: 10px !important; overflow-x: auto; -webkit-overflow-scrolling: touch; }
        table { min-width: 800px; } 
        
        /* Ajuste de Modales */
        .modal-box { width: 90% !important; max-width: 400px; padding: 20px !important; box-sizing: border-box; }
    }
`;
document.head.appendChild(globalResponsiveFix);

// ============================================================================
// OVERRIDE DE ALERTAS NATIVAS
// ============================================================================
window.originalAlert = window.alert;
window.alert = function(message) {
    let overlay = document.getElementById('custom-alert-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'custom-alert-overlay';
        overlay.className = 'custom-alert-overlay';
        overlay.innerHTML = `
            <div class="custom-alert-box" style="background: white; width: 90%; max-width: 350px; padding: 25px; border-radius: 12px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
                <div class="custom-alert-title" style="color: #004b87; font-weight: bold; font-size: 1.2rem; margin-bottom: 10px;">Notificación</div>
                <div class="custom-alert-body" id="custom-alert-message" style="color: #444; font-size: 0.95rem; margin-bottom: 20px; line-height: 1.4;"></div>
                <button style="background: #004b87; color: white; border: none; padding: 10px; width: 100%; border-radius: 6px; font-weight: bold; cursor: pointer;" onclick="closeCustomAlert()">Aceptar</button>
            </div>`;
        document.body.appendChild(overlay);
    }
    document.getElementById('custom-alert-message').innerHTML = String(message).replace(/\n/g, '<br>');

    overlay.style.display = 'flex';
    overlay.style.position = 'fixed';
    overlay.style.top = '0'; overlay.style.left = '0';
    overlay.style.width = '100vw'; overlay.style.height = '100vh';
    overlay.style.background = 'rgba(0,0,0,0.6)';
    overlay.style.zIndex = '999999';
    overlay.style.alignItems = 'center';
    overlay.style.justifyContent = 'center';
};

window.closeCustomAlert = function() {
    const overlay = document.getElementById('custom-alert-overlay');
    if(overlay) overlay.style.display = 'none';
};
