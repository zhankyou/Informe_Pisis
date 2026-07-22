const isAdmin = localStorage.getItem('isAdmin') === 'true';

class AppSidebar extends HTMLElement {
  connectedCallback() {
    const activeMenu = this.getAttribute('active-menu') || '';

    let adminMenus = '';
    if (isAdmin) {
        adminMenus = `
          <div class="nav-item" style="margin-top: 15px; font-weight: 700; color: white;">📁 Resolución SER124DREC</div>
          <a href="/poblacional" class="sub-item ${activeMenu === 'poblacional' ? 'active' : ''}">📄 Poblacional (SI-APS)</a>
          <a href="/financiero" class="sub-item ${activeMenu === 'financiero' ? 'active' : ''}">💰 Financiero (SER124)</a>
          <a href="/consultas" class="sub-item-child ${activeMenu === 'consultas' ? 'active' : ''}">↳ 🔍 Auditoría (SER124)</a>
        `;
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
    const userLabel = isAdmin ? '👤 Rol: ADMINISTRADOR' : '👤 VISTA PÚBLICA';
    const btnAccion = isAdmin
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
    localStorage.removeItem('isAdmin');
    window.location.href = '/';
};

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