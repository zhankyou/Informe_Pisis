const isAdminDashboard = localStorage.getItem('isAdmin') === 'true';
const formatoMoneda = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' });
const meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];
let chartInstances = [];

const mapTipos = { "1": "Contrato", "2": "Convenio", "3": "Nómina", "4": "Resolución", "5": "Oficio", "6": "Acta", "7": "Factura" };
const mapActas = { "1": "Parcial", "2": "Final", "3": "Liquidación" };
const NIT_ENTIDAD = "822002459";

function getLocalDateString() {
    const tzOffset = (new Date()).getTimezoneOffset() * 60000;
    return new Date(Date.now() - tzOffset).toISOString().split('T')[0];
}

async function inicializarDashboard() {
  if (isAdminDashboard) {
      document.getElementById('btn-nueva-res').style.display = 'block';
      document.getElementById('th-acciones').style.display = 'table-cell';
  }

  const fechaHoyStr = getLocalDateString();
  const partesFecha = fechaHoyStr.split('-');
  const anioActual = partesFecha[0];
  const mesActualStr = `${anioActual}-${partesFecha[1]}`;

  document.getElementById('fecha-operativa-lbl').textContent = `Datos al: ${fechaHoyStr}`;

  try {
    const [resEjecucion, resCroMensual, resCroDiario, resPoblacional] = await Promise.all([
      fetch('/api/dashboard/ejecucion').catch(() => null),
      fetch(`/api/cronograma/mensual?mes=${mesActualStr}`).catch(() => null),
      fetch(`/api/cronograma/diario?fecha=${fechaHoyStr}`).catch(() => null),
      fetch('/api/dashboard/poblacional').catch(() => null)
    ]);

    let controlFinanciero = [];
    let datosPoblacionales = null;

    if (resEjecucion && resEjecucion.ok) {
      const jsonEjecucion = await resEjecucion.json();
      if (jsonEjecucion.status === 'success') {
        chartInstances.forEach(chart => chart.destroy());
        chartInstances = [];
        renderizarTablas(jsonEjecucion.data_recursos);
        renderizarPanelesResolucion(jsonEjecucion.data_recursos);
        controlFinanciero = jsonEjecucion.data_control || [];
      }
    }

    if (resCroMensual && resCroMensual.ok) {
      const jsonMensual = await resCroMensual.json();
      if (jsonMensual.status === 'success') {
        document.getElementById('stat-territorios').textContent = new Set(jsonMensual.data.map(d => d.territorio)).size;
      }
    }

    if (resCroDiario && resCroDiario.ok) {
      const jsonDiario = await resCroDiario.json();
      if (jsonDiario.status === 'success') {
        document.getElementById('stat-duplas').textContent = jsonDiario.data.length;
        document.getElementById('stat-actividades').textContent = jsonDiario.data.length;
      }
    }

    if (resPoblacional && resPoblacional.ok) {
      const jsonPob = await resPoblacional.json();
      if (jsonPob.status === 'success') datosPoblacionales = jsonPob.data;
    }

    renderizarControlPISIS(controlFinanciero, datosPoblacionales);

  } catch (e) {
    console.error("Error crítico inicializando el dashboard:", e);
  }
}

function renderizarTablas(data) {
  const tbody = document.getElementById('tabla-resoluciones');
  if(data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="${isAdminDashboard ? 4 : 3}" style="text-align:center; color: var(--muted);">No hay resoluciones registradas.</td></tr>`;
      return;
  }

  tbody.innerHTML = data.map(item => {
    const isActiva = item.estado === 'ACTIVA';
    const tdAcciones = isAdminDashboard ? `<td><button class="btn ${isActiva ? 'btn-danger' : 'btn-action'}" onclick="toggleResolucion('${item.id_recurso}', '${isActiva ? 'FINALIZADA' : 'ACTIVA'}')">${isActiva ? 'Finalizar Ejecución' : 'Reactivar'}</button></td>` : '';
    return `
      <tr>
        <td><strong>${item.id_recurso}</strong></td>
        <td>${item.descripcion}</td>
        <td><span class="${isActiva ? 'badge active' : 'badge closed'}">${item.estado}</span></td>
        ${tdAcciones}
      </tr>
    `;
  }).join('');
}

function renderizarPanelesResolucion(data) {
  const grid = document.getElementById('grid-ejecucion');
  if(data.length === 0) {
      grid.innerHTML = `<p style="color: var(--muted); margin-left: 5px;">No existen datos de ejecución financiera para visualizar.</p>`;
      return;
  }

  let html = data.map(item => {
    const reintegroTeorico = item.incorporado - item.ejecutado_contratos;
    const congelado = item.estado !== 'ACTIVA';
    let filasCt = item.contratos_por_tipo.map(c => `<tr><td>${mapTipos[c.tipo] || c.tipo}</td><td>${c.cantidad}</td><td>${formatoMoneda.format(c.valor_total)}</td></tr>`).join('');
    let filasSg = item.seguimiento_detalle.map(s => `<tr><td>${mapTipos[s.tipo_contrato] || s.tipo_contrato}</td><td>${mapActas[s.tipo_acta] || s.tipo_acta}</td><td>${s.cantidad_actas}</td><td>${formatoMoneda.format(s.ejecutado)}</td></tr>`).join('');

    return `
      <div class="res-panel">
        <div class="res-header">
          <h3 style="font-size: 1rem;">${item.descripcion} <span style="opacity: 0.8; font-size: 0.85rem;">(ID: ${item.id_recurso})</span></h3>
          <span class="badge ${congelado ? 'closed' : 'active'}" style="background: white; color: ${congelado ? '#c62828' : '#008f7d'};">${item.estado}</span>
        </div>
        <div class="res-body">
          <div class="res-box" style="border-top: 3px solid var(--navy);">
            <h4>Ejecución Presupuestal</h4>
            <div class="res-item"><span>Incorporado:</span> <strong>${formatoMoneda.format(item.incorporado)}</strong></div>
            <div class="res-item"><span>Ejecutado (Contratos):</span> <strong>${formatoMoneda.format(item.ejecutado_contratos)}</strong></div>
            <div class="res-item" style="margin-top: 5px; padding-top: 10px; border-top: 1px dashed var(--border);">
              <span>Saldo No Ejecutado:</span>
              <strong style="color: ${reintegroTeorico >= 0 ? '#00b09b' : '#e53935'}; font-size: 1.1rem;">${formatoMoneda.format(reintegroTeorico)}</strong>
            </div>
            <div class="chart-container"><canvas id="chart-presupuesto-${item.id_recurso}"></canvas></div>
          </div>
          <div class="res-box" style="border-top: 3px solid #16a085;">
            <h4>Perfiles de Contratación</h4>
            <table style="font-size: 0.75rem; margin-top: 0; margin-bottom: 10px;">
              <thead><tr><th>Perfil</th><th>Cant.</th><th>Valor Total</th></tr></thead>
              <tbody>
                <tr><td>Medicina</td><td>${item.perfiles_contratacion.MEDICINA.cant}</td><td>${formatoMoneda.format(item.perfiles_contratacion.MEDICINA.val)}</td></tr>
                <tr><td>Enfermería</td><td>${item.perfiles_contratacion.ENFERMERIA.cant}</td><td>${formatoMoneda.format(item.perfiles_contratacion.ENFERMERIA.val)}</td></tr>
                <tr><td>Psicología</td><td>${item.perfiles_contratacion.PSICOLOGIA.cant}</td><td>${formatoMoneda.format(item.perfiles_contratacion.PSICOLOGIA.val)}</td></tr>
                <tr><td>Técnico</td><td>${item.perfiles_contratacion.TECNICO.cant}</td><td>${formatoMoneda.format(item.perfiles_contratacion.TECNICO.val)}</td></tr>
              </tbody>
            </table>
            <div class="chart-container"><canvas id="chart-perfiles-${item.id_recurso}"></canvas></div>
          </div>
          <div class="res-box" style="border-top: 3px solid #f39c12;">
            <h4>Detalle Contratos y Pólizas</h4>
            <div style="display: flex; justify-content: space-between; font-size: 0.75rem; margin-bottom: 10px;">
              <span>Nuevos: <strong>${item.contratos_i}</strong></span><span>Editados: <strong>${item.contratos_a}</strong></span><span>Anulados: <strong style="color: #e53935;">${item.contratos_e}</strong></span>
            </div>
            <table style="font-size: 0.75rem; margin-top: 0;">
              <thead><tr><th>Tipo Contrato</th><th>Cant.</th><th>Valor Total</th></tr></thead>
              <tbody>${filasCt || '<tr><td colspan="3">No hay contratos registrados.</td></tr>'}</tbody>
            </table>
            <div class="res-item" style="margin-top: auto; padding-top: 10px; border-top: 1px dashed var(--border);">
              <span>Total Pólizas Registradas:</span> <strong>${item.polizas_totales}</strong>
            </div>
          </div>
          <div class="res-box" style="border-top: 3px solid #8e44ad;">
            <h4>Seguimiento Técnico y Reintegros</h4>
            <div class="res-item"><span>Total Pagado:</span> <strong>${formatoMoneda.format(item.seg_pagado)}</strong></div>
            <table style="font-size: 0.75rem; margin-top: 5px;">
              <thead><tr><th>Contrato</th><th>Acta</th><th>Cant.</th><th>Ejecutado</th></tr></thead>
              <tbody>${filasSg || '<tr><td colspan="4">No hay actas registradas.</td></tr>'}</tbody>
            </table>
            <div class="res-item" style="margin-top: auto; padding-top: 10px; border-top: 1px dashed var(--border);">
              <span>Reintegro Rendimientos:</span> <strong style="color: var(--teal);">${formatoMoneda.format(item.reintegro_rendimientos)}</strong>
            </div>
            <div class="res-item"><span>Reintegro No Ejecutado:</span> <strong>${formatoMoneda.format(item.reintegro_no_ejecutado_oficial)}</strong></div>
          </div>
        </div>
      </div>
    `;
  }).join('');
  grid.innerHTML = html;

  data.forEach(item => {
    const reintegroTeorico = item.incorporado - item.ejecutado_contratos;
    const ctxP = document.getElementById(`chart-presupuesto-${item.id_recurso}`).getContext('2d');
    chartInstances.push(new Chart(ctxP, {
        type: 'doughnut',
        data: { labels: ['Ejecutado', 'Sobrante'], datasets: [{ data: [item.ejecutado_contratos, reintegroTeorico > 0 ? reintegroTeorico : 0], backgroundColor: ['#0a1f3d', '#00b09b'], borderWidth: 0 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right', labels: { boxWidth: 10, font: { size: 10, family: 'Sora' } } } } }
    }));

    const ctxPerf = document.getElementById(`chart-perfiles-${item.id_recurso}`).getContext('2d');
    chartInstances.push(new Chart(ctxPerf, {
        type: 'bar',
        data: { labels: ['Med', 'Enf', 'Psi', 'Téc', 'Otr'], datasets: [{ data: [item.perfiles_contratacion.MEDICINA.cant, item.perfiles_contratacion.ENFERMERIA.cant, item.perfiles_contratacion.PSICOLOGIA.cant, item.perfiles_contratacion.TECNICO.cant, item.perfiles_contratacion.OTROS.cant], backgroundColor: ['#e74c3c', '#3498db', '#9b59b6', '#2ecc71', '#95a5a6'], borderRadius: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } }
    }));
  });
}

function renderizarControlPISIS(financiero, poblacional) {
  const grid = document.getElementById('grid-pisis');
  let html = '';

  if (poblacional) {
    const f = poblacional.familias.sincronizadas || 0;
    const i = poblacional.integrantes.sincronizadas || 0;
    const pendientes = poblacional.familias.pendientes + poblacional.integrantes.pendientes;
    const totalReg = f + i;

    const isSync = totalReg > 0 && pendientes === 0;
    const isWorking = pendientes > 0;

    let badgeHtml = '<span class="badge closed">SIN DATOS</span>';
    let stepClass = '';
    if (isSync) { badgeHtml = '<span class="badge active">ETL EXITOSO</span>'; stepClass = 'done'; }
    if (isWorking) badgeHtml = '<span class="badge warning">PENDIENTE ETL</span>';

    const fechaFormat = getLocalDateString().replace(/-/g, '');
    const fileNamePob = `APS124CCFP${fechaFormat}NI${NIT_ENTIDAD}.TXT`;

    html += `
      <div class="pisis-card">
        <div class="pisis-header pob">
          <h4>📊 Anexo Poblacional (SI-APS)</h4>
          ${badgeHtml}
        </div>
        <div class="pisis-body">
          <div class="pisis-row"><span>Registros de Detalle (Tipo 2):</span><span>${f}</span></div>
          <div class="pisis-row"><span>Registros de Detalle (Tipo 3):</span><span>${i}</span></div>
          <div class="pisis-row" style="border: none;"><span>Cola ETL Pendiente:</span><span style="color: #e53935;">${pendientes}</span></div>
          
          <div style="margin-top: 10px;">
            <span style="font-size: 0.75rem; color: var(--navy); font-weight: 700;">Estructura Generada (PISIS):</span>
            <span class="pisis-filename">${fileNamePob}</span>
          </div>

          <div class="pisis-stepper">
            <div class="pisis-step ${stepClass}">1. Extracción</div>
            <div class="pisis-step ${stepClass}">2. Transform.</div>
            <div class="pisis-step ${stepClass}">3. Carga .TXT</div>
          </div>
        </div>
      </div>
    `;
  }

  if (financiero && financiero.length > 0) {
    html += financiero.map(item => {
      const d = new Date(item.fecha_final);
      const periodo = !isNaN(d.getTime()) ? `${meses[d.getMonth()]} ${d.getFullYear()}` : 'Periodo';
      const fechaFormat = item.fecha_final.replace(/-/g, '');
      const fileNameFin = `SER124DREC${fechaFormat}NI${NIT_ENTIDAD}ID${item.id_recurso}.txt`;

      return `
        <div class="pisis-card">
          <div class="pisis-header fin">
            <h4>💰 Anexo Financiero (${periodo})</h4>
            <span class="badge active">LISTO PARA REPORTE</span>
          </div>
          <div class="pisis-body">
            <div class="pisis-row"><span>Periodo Reportado:</span><span>${item.fecha_inicial} al ${item.fecha_final}</span></div>
            <div class="pisis-row"><span>ID Recurso:</span><span>${item.id_recurso}</span></div>
            <div class="pisis-row" style="border: none;"><span>Total Registros (Tipo 2-7):</span><span>Automático</span></div>
            
            <div style="margin-top: 10px;">
              <span style="font-size: 0.75rem; color: var(--navy); font-weight: 700;">Estructura Generada (PISIS):</span>
              <span class="pisis-filename">${fileNameFin}</span>
            </div>

            <div class="pisis-stepper">
              <div class="pisis-step done">1. Val. Estructura</div>
              <div class="pisis-step done">2. Val. Calidad</div>
              <div class="pisis-step done">3. Aprobado SISPRO</div>
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  if (html === '') {
      grid.innerHTML = '<p style="color: var(--muted); padding: 15px;">No hay reportes ni sincronizaciones PISIS disponibles.</p>';
  } else {
      grid.innerHTML = html;
  }
}

async function toggleResolucion(id, estado) {
  if (!confirm(estado === 'FINALIZADA' ? "⚠️ ¿Desea FINALIZAR la resolución y congelar la captura?" : "🔓 ¿Desea REACTIVAR la resolución?")) return;
  try {
    const res = await fetch('/api/recursos/toggle', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id_recurso: id, estado: estado }) });
    const data = await res.json();
    if(data.status === 'success') { inicializarDashboard(); } else { alert("Error: " + data.msg); }
  } catch (err) { alert("Fallo de conexión al servidor."); }
}

document.addEventListener('DOMContentLoaded', inicializarDashboard);