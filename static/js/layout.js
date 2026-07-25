class AppSidebar extends HTMLElement {
  connectedCallback() {
    const activeMenu = this.getAttribute('active-menu') || '';

    // Sanitización robusta del rol
    const rolRaw = sessionStorage.getItem('rol_usuario') || localStorage.getItem('rol_usuario') || 'publico';
    const rol = rolRaw.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();

    // Validación RBAC para el menú de consultas
    const isAdmin = rol.includes('admin') || rol.includes('coordinador') || localStorage.getItem('isAdmin') === 'true';

    let adminMenus = '';
    if (rol !== 'publico') {
        adminMenus = `
          <div class="nav-item" style="margin-top: 15px; font-weight: 700; color: white;">📁 Resolución SER124DREC</div>
          <a href="/poblacional" class="sub-item ${activeMenu === 'poblacional' ? 'active' : ''}">📄 Poblacional (SI-APS)</a>
          <a href="/financiero" class="sub-item ${activeMenu === 'financiero' ? 'active' : ''}">💰 Financiero (SER124)</a>
          <a href="/consultas" class="sub-item-child ${activeMenu === 'consultas' ? 'active' : ''}">↳ 🔍 Auditoría (SER124)</a>

          <div class="nav-item" style="margin-top: 15px; font-weight: 700; color: white;">📁 Gestión Humana y Pagos</div>
          <a href="/ponderacion" class="sub-item ${activeMenu === 'ponderacion' ? 'active' : ''}">📊 Matriz de Ponderación</a>
        `;
    }

    let consultaAutorizaciones = '';
    if (isAdmin) {
        consultaAutorizaciones = `<a href="/consulta_acceso" class="sub-item ${activeMenu === 'consulta_acceso' ? 'active' : ''}">↳ 🔍 Consulta Autorizaciones</a>`;
    }

    this.innerHTML = `
      <div class="sidebar-internal">
        <div class="brand">
          <img src="/static/img/logo-ese.png" alt="Logo ESE" style="max-height: 40px; width: auto; object-fit: contain;">
          INFORME APS
        </div>
        <div class="nav-menu">
          <a href="/" class="nav-item ${activeMenu === 'dashboard' ? 'active' : ''}">📊 Dashboard General</a>
          <a href="/informe" class="nav-item ${activeMenu === 'informe' ? 'active' : ''}">📈 Informe Entidades</a>
          
          <div class="nav-item" style="margin-top: 15px; font-weight: 700; color: white;">📋 Autorizaciones PISIS</div>
          <a href="/formulario_acceso" class="sub-item ${activeMenu === 'formulario_acceso' ? 'active' : ''}">📝 Diligenciar Acceso</a>
          ${consultaAutorizaciones}

          ${adminMenus}
          
          <div class="nav-item" style="margin-top: 15px; font-weight: 700; color: white;">📅 Cronograma (EBS)</div>
          <a href="/cronograma" class="sub-item ${activeMenu === 'cronograma' ? 'active' : ''}">📍 Programación Operativa</a>
        </div>
      </div>
    `;
  }
}

class AppTopbar extends HTMLElement {
  connectedCallback() {
    const titulo = this.getAttribute('titulo') || 'Módulo Principal';

    // Extracción y sanitización de sesión
    const rolRaw = sessionStorage.getItem('rol_usuario') || localStorage.getItem('rol_usuario') || 'publico';
    const userRaw = sessionStorage.getItem('username') || localStorage.getItem('username') || '';

    // Evaluación segura sin tildes ni mayúsculas
    const rolNormalizado = rolRaw.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();
    const esPublico = rolNormalizado === 'publico';

    // Formateo visual
    const rol = rolRaw.toUpperCase().replace('ADMIN', 'ADMINISTRADOR');
    const usuario = userRaw ? userRaw.toUpperCase() : 'INVITADO';

    const userLabel = esPublico ? '👤 VISTA PÚBLICA' : `👤 ${usuario} | Rol: <span style="color: #3b82f6;">${rol}</span>`;

    // Condicional exacto del botón
    const btnAccion = !esPublico
        ? `<button class="btn-logout" onclick="cerrarSesion()">Cerrar Sesión</button>`
        : `<button class="btn-logout" style="background: var(--teal);" onclick="window.location.href='/login'">Iniciar Sesión</button>`;

    this.innerHTML = `
      <div class="topbar-internal">
        <span>${titulo}</span>
        <div style="display: flex; align-items: center;">
          <span style="font-size: 0.8rem; color: var(--muted); font-weight: 700; margin-right: 15px;">${userLabel}</span>
          ${btnAccion}
        </div>
      </div>
    `;
  }
}

customElements.define('app-sidebar', AppSidebar);
customElements.define('app-topbar', AppTopbar);

window.cerrarSesion = function() {
    // Purga integral de la sesión
    sessionStorage.clear();
    localStorage.clear();
    window.location.href = '/';
};

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
            <div class="custom-alert-box">
                <div class="custom-alert-title">${window.location.host} dice</div>
                <div class="custom-alert-body" id="custom-alert-message"></div>
                <div class="custom-alert-btn-wrapper"><button class="custom-alert-btn" onclick="closeCustomAlert()">Aceptar</button></div>
            </div>`;
        document.body.appendChild(overlay);
    }
    document.getElementById('custom-alert-message').innerHTML = String(message).replace(/\n/g, '<br>');
    overlay.classList.add('show');
};

window.closeCustomAlert = function() {
    const overlay = document.getElementById('custom-alert-overlay');
    if(overlay) overlay.classList.remove('show');
};
