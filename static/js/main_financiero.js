let currentUploadTable = '';
let currentUploadData = [];

function sanitizarPISIS(e) {
  let val = e.target.value.toUpperCase();
  val = val.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  val = val.replace(/N°/g, "NO").replace(/°/g, "NO").replace(/"/g, "");
  val = val.replace(/[^A-Z0-9\s\/\.-]/g, "").replace(/\s{2,}/g, " ");
  e.target.value = val;
}

function switchTab(tabId, element) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
  element.classList.add('active');
  document.getElementById(tabId).classList.add('active');
}

async function cargarRecursos() {
  try {
    const res = await fetch('/api/recursos');
    const data = await res.json();
    const options = `<option value="">Seleccione ID Recurso...</option>` +
      data.map(r => `<option value="${r.id_recurso}">${r.id_recurso} - ${r.descripcion}</option>`).join('');
    document.querySelectorAll('.dynamic-recurso').forEach(select => select.innerHTML = options);
  } catch (err) { console.error("Error cargando recursos paramétricos", err); }
}

async function postRecurso(e) {
  e.preventDefault();
  const payload = {
    id_recurso: document.getElementById('new_id_recurso').value.trim(),
    descripcion: document.getElementById('new_descripcion').value.trim()
  };
  try {
    const res = await fetch('/api/recursos', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
    const data = await res.json();
    if (res.ok && data.status === 'success') {
      alert("✅ ID de Recurso Guardado Exitósamente.");
      e.target.reset();
      cargarRecursos();
    } else {
      alert("❌ Error: " + data.msg);
    }
  } catch (err) { alert("❌ Fallo de conexión."); }
}

async function postForm(e, endpoint) {
  e.preventDefault();
  const payload = Object.fromEntries(new FormData(e.target).entries());
  Object.keys(payload).forEach(k => payload[k] === "" && delete payload[k]);

  try {
    const res = await fetch(endpoint, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
    const data = await res.json();
    alert(data.status === 'success' ? "✅ " + data.msg : "❌ Error: " + data.msg);
    if (data.status === 'success') {
      const idRecursoPrevio = e.target.querySelector('select[name="id_recurso"]')?.value;
      e.target.reset();
      if (idRecursoPrevio) e.target.querySelector('select[name="id_recurso"]').value = idRecursoPrevio;
    }
  } catch (err) { alert("❌ Error conectando al servidor."); }
}

function abrirModalCarga(tabla, tipo) {
  currentUploadTable = tabla;
  document.getElementById('modal-title').textContent = `Carga Masiva: ${tabla.toUpperCase()} (${tipo.toUpperCase()})`;
  document.getElementById('archivoCarga').value = '';
  document.getElementById('preview-head').innerHTML = `<tr><th>Cargue un archivo para pre-visualizar la información sanitizada</th></tr>`;
  document.getElementById('preview-body').innerHTML = '';
  document.getElementById('btnConfirmarCarga').style.display = 'none';
  document.getElementById('modalCarga').style.display = 'flex';
}

function cerrarModalCarga() {
  document.getElementById('modalCarga').style.display = 'none';
  currentUploadData = [];
}

async function procesarArchivo() {
  const fileInput = document.getElementById('archivoCarga');
  if (!fileInput.files.length) return alert("Seleccione un archivo primero.");

  const formData = new FormData();
  formData.append('archivo', fileInput.files[0]);

  try {
    const res = await fetch(`/api/cargador/preview/${currentUploadTable}`, { method: 'POST', body: formData });
    const json = await res.json();

    if (res.ok && json.status === 'success') {
      currentUploadData = json.data;
      renderPreviewTable(json.columns, currentUploadData);
      document.getElementById('btnConfirmarCarga').style.display = 'block';
    } else {
      alert("❌ Error: " + json.msg);
    }
  } catch (e) { alert("❌ Fallo procesando el archivo."); }
}

function renderPreviewTable(columns, data) {
  const thead = document.getElementById('preview-head');
  const tbody = document.getElementById('preview-body');

  thead.innerHTML = `<tr>${columns.map(c => `<th>${c}</th>`).join('')}</tr>`;
  tbody.innerHTML = data.map(row =>
    `<tr>${columns.map(c => `<td>${row[c] || ''}</td>`).join('')}</tr>`
  ).join('');
}

async function confirmarCargaMasiva() {
  if(!currentUploadData.length) return;

  try {
    const res = await fetch(`/api/cargador/confirm/${currentUploadTable}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(currentUploadData)
    });
    const json = await res.json();

    if (res.ok && json.status === 'success') {
      alert("✅ " + json.msg);
      cerrarModalCarga();
    } else {
      alert("❌ Error en BD: " + json.msg);
    }
  } catch (e) { alert("❌ Fallo guardando en base de datos."); }
}

document.addEventListener('DOMContentLoaded', cargarRecursos);