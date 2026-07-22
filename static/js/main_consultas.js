const formatoMoneda = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' });
let tablaActual = 'ser_control';
let rawData = [];
let sortCol = null;
let sortAsc = true;

let currentPage = 1;
let itemsPerPage = 10;

function isCurrencyField(key) {
  return ['valor_incorporado', 'valor_contrato', 'valor_ejecutado', 'valor_pagado', 'valor_reintegrado'].includes(key);
}

function setTab(tabla, element) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  element.classList.add('active');
  tablaActual = tabla;

  const fId = document.getElementById('flt-id');
  const fContrato = document.getElementById('flt-contrato');
  const fActo = document.getElementById('flt-acto');

  fId.style.display = tabla === 'ser_control' ? 'none' : 'flex';
  fContrato.style.display = ['ser_contratos', 'ser_polizas', 'ser_seguimiento'].includes(tabla) ? 'flex' : 'none';
  fActo.style.display = ['ser_incorporacion', 'ser_reintegro_no_ejecutado', 'ser_reintegro_rendimientos'].includes(tabla) ? 'flex' : 'none';

  document.getElementById('f_id_recurso').value = '';
  document.getElementById('f_num_contrato').value = '';
  document.getElementById('f_num_acto').value = '';

  buscarDatos();
}

async function buscarDatos() {
  const id = document.getElementById('f_id_recurso').value.trim();
  const contrato = document.getElementById('f_num_contrato').value.trim();
  const acto = document.getElementById('f_num_acto').value.trim();

  const url = `/api/consultas/${tablaActual}?id_recurso=${encodeURIComponent(id)}&num_contrato=${encodeURIComponent(contrato)}&num_acto=${encodeURIComponent(acto)}`;

  try {
    const res = await fetch(url);
    const json = await res.json();

    if (json.status === 'success') {
      rawData = json.data;
      sortCol = null;
      currentPage = 1;
      renderTable();
    } else {
      alert("Error: " + json.msg);
    }
  } catch (err) {
    document.getElementById('t-body').innerHTML = `<tr><td style="color: #e53935;">Error consultando la base de datos local.</td></tr>`;
  }
}

function sortData(key) {
  if (sortCol === key) {
    sortAsc = !sortAsc;
  } else {
    sortCol = key;
    sortAsc = true;
  }

  rawData.sort((a, b) => {
    let valA = a[key];
    let valB = b[key];

    if (valA === null) valA = '';
    if (valB === null) valB = '';

    if (typeof valA === 'string') valA = valA.toLowerCase();
    if (typeof valB === 'string') valB = valB.toLowerCase();

    if (valA < valB) return sortAsc ? -1 : 1;
    if (valA > valB) return sortAsc ? 1 : -1;
    return 0;
  });

  currentPage = 1;
  renderTable();
}

function renderTable() {
  const thead = document.getElementById('t-head');
  const tbody = document.getElementById('t-body');

  if (rawData.length === 0) {
    thead.innerHTML = `<tr><th>Sin Resultados</th></tr>`;
    tbody.innerHTML = `<tr><td style="text-align: center; color: #5d7290; padding: 25px;">No se encontraron registros en la tabla <b>${tablaActual}</b>.</td></tr>`;
    document.getElementById('page-info').textContent = "Mostrando 0 de 0 registros";
    document.getElementById('btn-prev').disabled = true;
    document.getElementById('btn-next').disabled = true;
    return;
  }

  const keys = Object.keys(rawData[0]).filter(k => k !== 'id' && k !== 'resolucion_origen');

  thead.innerHTML = `<tr>
    <th style="text-align: center; min-width: 150px;">ACCIONES</th>
    ${keys.map(k => {
      let cls = sortCol === k ? (sortAsc ? 'sort-asc' : 'sort-desc') : '';
      return `<th class="${cls}" onclick="sortData('${k}')">${k.replace(/_/g, ' ').toUpperCase()}</th>`;
    }).join('')}
  </tr>`;

  const totalItems = rawData.length;
  const totalPages = itemsPerPage === 'all' ? 1 : Math.ceil(totalItems / itemsPerPage);

  let startIdx = 0;
  let endIdx = totalItems;

  if (itemsPerPage !== 'all') {
    startIdx = (currentPage - 1) * itemsPerPage;
    endIdx = Math.min(startIdx + itemsPerPage, totalItems);
  }

  const paginatedData = rawData.slice(startIdx, endIdx);

  tbody.innerHTML = paginatedData.map(row => {
    let actions = `
      <button class="btn-action btn-edit" onclick="editarRegistro(${row.id})">Editar</button>
      <button class="btn-action btn-delete" onclick="eliminarRegistro(${row.id})">Eliminar</button>
    `;

    let cols = keys.map(k => {
      let val = row[k] !== null ? row[k] : '-';
      if (val !== '-' && isCurrencyField(k)) {
        val = formatoMoneda.format(val);
      }
      return `<td>${val}</td>`;
    }).join('');

    return `<tr><td style="text-align:center;">${actions}</td>${cols}</tr>`;
  }).join('');

  document.getElementById('page-info').textContent = `Mostrando ${startIdx + 1} al ${endIdx} de ${totalItems} registros`;
  document.getElementById('page-number').textContent = currentPage;
  document.getElementById('btn-prev').disabled = currentPage === 1;
  document.getElementById('btn-next').disabled = currentPage === totalPages || itemsPerPage === 'all';
}

function changePageSize() {
  const val = document.getElementById('pageSize').value;
  itemsPerPage = val === 'all' ? 'all' : parseInt(val);
  currentPage = 1;
  renderTable();
}

function changePage(dir) {
  currentPage += dir;
  renderTable();
}

function editarRegistro(id) {
  alert("Normativa PISIS: Para EDITAR un registro, debe diligenciarlo nuevamente en el formulario del Módulo Financiero utilizando el Indicador de Actualización 'A' (Actualizar) o 'E' (Anular) según aplique.");
}

async function eliminarRegistro(id) {
  if(!confirm("⚠️ ADVERTENCIA ADMINISTRATIVA: ¿Está seguro de eliminar físicamente este registro de la base de datos local?")) return;

  try {
    const res = await fetch(`/api/consultas/${tablaActual}/${id}`, { method: 'DELETE' });
    const data = await res.json();

    if (data.status === 'success') {
      alert("✅ Registro eliminado de la base de datos.");
      buscarDatos();
    } else {
      alert("❌ " + data.msg);
    }
  } catch (e) { alert("❌ Fallo conectando al servidor."); }
}

document.addEventListener('DOMContentLoaded', buscarDatos);