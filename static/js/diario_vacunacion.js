const isAdminCronograma = localStorage.getItem('isAdmin') === 'true';
let currentConfig = {};
let dataDiaria = [];

const fN = (str) => str ? str.replace(/ \| /g, '<br>') : '';

function addCampoPersonal(tipo, max) {
    const container = document.getElementById(`container-${tipo}`);
    if (container.children.length >= max) return alert(`Límite normativo: Máximo ${max} personas para este rol.`);

    const div = document.createElement('div');
    div.style.display = 'flex';
    div.style.gap = '10px';
    div.innerHTML = `
        <input type="text" class="dyn-nom-${tipo} uppercase-text" placeholder="NOMBRES COMPLETOS" style="flex:2;" required>
        <input type="text" class="dyn-tel-${tipo}" placeholder="NÚMERO CELULAR" style="flex:1;">
        <button type="button" class="btn btn-danger" style="padding: 0 10px;" onclick="this.parentElement.remove()">X</button>
    `;
    container.appendChild(div);
}

function addCampoConfig(tipo, max) {
    const container = document.getElementById(`container-${tipo}`);
    if (container.children.length >= max) return alert(`Límite normativo: Máximo ${max} personas para este rol.`);

    const div = document.createElement('div');
    div.style.display = 'flex';
    div.style.gap = '10px';
    div.innerHTML = `
        <input type="text" class="cfg-nom-${tipo} uppercase-text" placeholder="NOMBRES COMPLETOS" style="flex:2;" required>
        <input type="text" class="cfg-tel-${tipo}" placeholder="NÚMERO CELULAR" style="flex:1;">
        <button type="button" class="btn btn-danger" style="padding: 0 10px;" onclick="this.parentElement.remove()">X</button>
    `;
    container.appendChild(div);
}

async function cargarDiario() {
  const fecha = document.getElementById('filtro-fecha').value;
  const partes = fecha.split('-');
  const isEditable = isAdminCronograma;

  document.getElementById('btn-add-dupla').style.display = isEditable ? 'block' : 'none';
  document.getElementById('btn-edit-txt').style.display = isEditable ? 'block' : 'none';
  document.getElementById('btn-group-duplicar').style.display = isEditable ? 'flex' : 'none';

  document.getElementById('lbl-fecha-tabla').textContent = `${partes[2]}/${partes[1]}/${partes[0]}`;
  document.getElementById('v-fecha').value = fecha;

  try {
    const res = await fetch(`/api/cronograma/diario?fecha=${fecha}`);
    const json = await res.json();
    const tbody = document.getElementById('tabla-diario');

    if (json.status === 'success') {
      dataDiaria = json.data;
      currentConfig = json.config;

      let nombresCEMI = currentConfig.entrega_nombres ? currentConfig.entrega_nombres.split(' | ') : [];
      let telsCEMI = currentConfig.entrega_telefonos ? currentConfig.entrega_telefonos.split(' | ') : [];
      let strCEMI = "";
      for(let i=0; i<nombresCEMI.length; i++) {
          if(nombresCEMI[i].trim() !== '') strCEMI += `<strong>${nombresCEMI[i].toUpperCase()}</strong> (${telsCEMI[i] || ''}) &nbsp; | &nbsp; `;
      }
      if(strCEMI) {
          document.getElementById('tr-entrega-nombres').innerHTML = `<td colspan="${isEditable ? 12 : 11}" style="text-align: left; background: #fff7ed; padding-left: 15px; font-size: 0.75rem;">${strCEMI}</td>`;
      } else {
          document.getElementById('tr-entrega-nombres').innerHTML = '';
      }

      let html = "";
      if(dataDiaria.length === 0) {
        html += `<tr><td colspan="${isEditable ? 12 : 11}" style="color: var(--muted); padding: 20px;">No hay programación operativa registrada para esta fecha.</td></tr>`;
      } else {
        html += dataDiaria.map((row, idx) => {
          const hi = row.hora_inicio ? row.hora_inicio.slice(0,5) : '';
          const hf = row.hora_fin ? row.hora_fin.slice(0,5) : '';
          return `
          <tr>
            <td style="font-weight: 700; font-size: 0.85rem;">${row.dupla}</td>
            <td style="text-align: left; font-weight: 700; color: #1e3a8a;">${row.lugar}</td>
            <td style="font-weight: 600; color: #4b5563;">${hi} - ${hf}</td>
            <td style="text-align: left; font-weight: 600;">${fN(row.vacunador)}</td>
            <td>${fN(row.tel_vacunador)}</td>
            <td style="text-align: left; font-weight: 600;">${fN(row.anotador)}</td>
            <td>${fN(row.tel_anotador)}</td>
            <td style="text-align: left; font-weight: 600;">${fN(row.profesional_valoracion)}</td>
            <td>${fN(row.tel_profesional)}</td>
            <td style="text-align: left; font-weight: 600;">${fN(row.desistimientos)}</td>
            <td>${fN(row.tel_desistimientos)}</td>
            ${isEditable ? `
            <td style="min-width: 80px;">
              <button class="btn-icon" title="Editar" onclick="abrirFormDupla(${idx})">✏️</button>
              <button class="btn-icon" title="Eliminar" onclick="eliminarDupla(${row.id})">🗑️</button>
            </td>` : ''}
          </tr>
        `;}).join('');
      }

      const hIniArch = currentConfig.archivo_hora_inicio ? currentConfig.archivo_hora_inicio.slice(0,5) : '08:00';
      const hFinArch = currentConfig.archivo_hora_fin ? currentConfig.archivo_hora_fin.slice(0,5) : '16:00';

      html += `
        <tr><td colspan="${isEditable ? 12 : 11}" class="th-pink" style="margin-top: 10px; border-top: 3px solid #9ca3af; padding-left: 15px;">ARCHIVO Y PAIWEB EN OFICINA ADMINISTRATIVA APS</td></tr>
        <tr class="th-pink" style="font-weight: 600;">
          <td colspan="2" rowspan="3" style="vertical-align: middle;">${hIniArch} A ${hFinArch}</td>
          <td colspan="2">PAPELERÍA</td>
          <td colspan="${isEditable ? 6 : 5}" style="color: #1e3a8a; text-align: left;">${fN(currentConfig.papeleria_nombres).toUpperCase()}</td>
          <td colspan="2">${fN(currentConfig.papeleria_telefonos)}</td>
        </tr>
        <tr class="th-pink" style="font-weight: 600;">
          <td colspan="2">CARGUE A PAIWEB</td>
          <td colspan="${isEditable ? 6 : 5}" style="color: #1e3a8a; text-align: left;">${fN(currentConfig.cargue_nombres).toUpperCase()}</td>
          <td colspan="2">${fN(currentConfig.cargue_telefonos)}</td>
        </tr>
        <tr class="th-pink" style="font-weight: 600;">
          <td colspan="2">VALIDACIÓN PAIWEB</td>
          <td colspan="${isEditable ? 6 : 5}" style="color: #1e3a8a; text-align: left;">${fN(currentConfig.validacion_nombres).toUpperCase()}</td>
          <td colspan="2">${fN(currentConfig.validacion_telefonos)}</td>
        </tr>
        <tr class="th-pink">
          <td colspan="${isEditable ? 12 : 11}" style="text-align: left; padding: 15px;">
            <span style="color: #b91c1c; font-weight: 700; white-space: pre-wrap;">${(currentConfig.observaciones || '').toUpperCase()}</span>
          </td>
        </tr>
      `;
      tbody.innerHTML = html;
    }
  } catch (e) { alert("Error consultando cronograma."); }
}

async function duplicarDiario() {
    if (!isAdminCronograma) return window.location.replace('/login');

    const fechaOrigen = document.getElementById('fecha-origen-copy').value;
    const fechaDestino = document.getElementById('filtro-fecha').value;

    if (!fechaOrigen || !fechaDestino) {
        return alert("⚠️ Seleccione ambas fechas (Origen y Destino) antes de duplicar.");
    }

    if (fechaOrigen === fechaDestino) {
        return alert("⚠️ La fecha de origen y destino no pueden ser iguales.");
    }

    if (!confirm(`⚠️ ¿Clonar la programación del ${fechaOrigen} hacia el ${fechaDestino}?\n(Esto sobreescribirá los datos del destino)`)) return;

    try {
        const res = await fetch('/api/cronograma/diario/duplicar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ fecha_origen: fechaOrigen, fecha_destino: fechaDestino })
        });
        const data = await res.json();
        alert(data.status === 'success' ? "✅ " + data.msg : "❌ Error: " + data.msg);
        if(data.status === 'success') cargarDiario();
    } catch (err) { alert("Error de red."); }
}

function abrirFormConfig() {
  document.getElementById('form-vacunacion').style.display = 'none';
  document.getElementById('form-config-diario').style.display = 'block';

  ['cemi', 'papeleria', 'cargue', 'validacion'].forEach(tipo => {
      document.getElementById(`container-${tipo}`).innerHTML = '';
  });

  document.getElementById('cfg-arch-ini').value = currentConfig.archivo_hora_inicio ? currentConfig.archivo_hora_inicio.slice(0,5) : '08:00';
  document.getElementById('cfg-arch-fin').value = currentConfig.archivo_hora_fin ? currentConfig.archivo_hora_fin.slice(0,5) : '16:00';
  document.getElementById('cfg-obs').value = currentConfig.observaciones || '';

  const mapsCfg = [
      { key: 'cemi', limit: 5, db_n: currentConfig.entrega_nombres, db_t: currentConfig.entrega_telefonos },
      { key: 'papeleria', limit: 5, db_n: currentConfig.papeleria_nombres, db_t: currentConfig.papeleria_telefonos },
      { key: 'cargue', limit: 5, db_n: currentConfig.cargue_nombres, db_t: currentConfig.cargue_telefonos },
      { key: 'validacion', limit: 5, db_n: currentConfig.validacion_nombres, db_t: currentConfig.validacion_telefonos }
  ];

  mapsCfg.forEach(m => {
      let noms = m.db_n ? m.db_n.split(' | ') : [];
      let tels = m.db_t ? m.db_t.split(' | ') : [];
      if (noms.length === 0) addCampoConfig(m.key, m.limit);
      noms.forEach((n, i) => {
          if (n.trim() !== '') {
              addCampoConfig(m.key, m.limit);
              const cont = document.getElementById(`container-${m.key}`);
              cont.lastElementChild.querySelector(`.cfg-nom-${m.key}`).value = n;
              cont.lastElementChild.querySelector(`.cfg-tel-${m.key}`).value = tels[i] || '';
          }
      });
      if (document.getElementById(`container-${m.key}`).children.length === 0) {
          addCampoConfig(m.key, m.limit);
      }
  });
}

async function guardarConfigDiario(e) {
  e.preventDefault();
  if (!isAdminCronograma) return window.location.replace('/login');

  const payload = {
      fecha: document.getElementById('filtro-fecha').value,
      archivo_hora_inicio: document.getElementById('cfg-arch-ini').value,
      archivo_hora_fin: document.getElementById('cfg-arch-fin').value,
      observaciones: document.getElementById('cfg-obs').value.toUpperCase()
  };

  const rolesCfg = [
      { ui: 'cemi', db_n: 'entrega_nombres', db_t: 'entrega_telefonos' },
      { ui: 'papeleria', db_n: 'papeleria_nombres', db_t: 'papeleria_telefonos' },
      { ui: 'cargue', db_n: 'cargue_nombres', db_t: 'cargue_telefonos' },
      { ui: 'validacion', db_n: 'validacion_nombres', db_t: 'validacion_telefonos' }
  ];

  rolesCfg.forEach(r => {
      let noms = Array.from(document.querySelectorAll(`.cfg-nom-${r.ui}`)).map(i => i.value.trim().toUpperCase()).filter(v => v !== '');
      let tels = Array.from(document.querySelectorAll(`.cfg-tel-${r.ui}`)).map((i, idx) => noms[idx] ? i.value.trim() : '').filter((_, idx) => noms[idx] !== '');
      payload[r.db_n] = noms.join(' | ');
      payload[r.db_t] = tels.join(' | ');
  });

  try {
    const res = await fetch('/api/cronograma/diario/config', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
    });
    const data = await res.json();
    alert(data.status === 'success' ? "✅ " + data.msg : "❌ Error: " + data.msg);
    if(data.status === 'success') {
      document.getElementById('form-config-diario').style.display = 'none';
      cargarDiario();
    }
  } catch (err) { alert("Error de red."); }
}

function abrirFormDupla(index) {
  if (!isAdminCronograma) return window.location.replace('/login');
  document.getElementById('form-config-diario').style.display = 'none';
  document.getElementById('form-vacunacion').style.display = 'block';
  document.getElementById('frm-dupla').reset();
  document.getElementById('v-fecha').value = document.getElementById('filtro-fecha').value;

  ['vacunador', 'anotador', 'profesional', 'desistimientos'].forEach(tipo => {
      document.getElementById(`container-${tipo}`).innerHTML = '';
  });

  if(index !== null) {
    document.getElementById('lbl-form-dupla').textContent = "Editar Asignación (Dupla)";
    const row = dataDiaria[index];
    document.getElementById('v-id').value = row.id;
    document.getElementById('v-dupla').value = row.dupla;
    document.getElementById('v-lugar').value = row.lugar;
    document.getElementById('v-h-ini').value = row.hora_inicio ? row.hora_inicio.slice(0,5) : '';
    document.getElementById('v-h-fin').value = row.hora_fin ? row.hora_fin.slice(0,5) : '';

    const maps = [
        { key: 'vacunador', limit: 5, db_n: row.vacunador, db_t: row.tel_vacunador },
        { key: 'anotador', limit: 5, db_n: row.anotador, db_t: row.tel_anotador },
        { key: 'profesional', limit: 5, db_n: row.profesional_valoracion, db_t: row.tel_profesional },
        { key: 'desistimientos', limit: 5, db_n: row.desistimientos, db_t: row.tel_desistimientos }
    ];

    maps.forEach(m => {
        let noms = m.db_n ? m.db_n.split(' | ') : [];
        let tels = m.db_t ? m.db_t.split(' | ') : [];
        if (noms.length === 0) addCampoPersonal(m.key, m.limit);
        noms.forEach((n, i) => {
            if(n.trim() !== '') {
                addCampoPersonal(m.key, m.limit);
                const cont = document.getElementById(`container-${m.key}`);
                cont.lastElementChild.querySelector(`.dyn-nom-${m.key}`).value = n;
                cont.lastElementChild.querySelector(`.dyn-tel-${m.key}`).value = tels[i] || '';
            }
        });
        if (document.getElementById(`container-${m.key}`).children.length === 0) {
            addCampoPersonal(m.key, m.limit);
        }
    });
  } else {
    document.getElementById('lbl-form-dupla').textContent = "Registrar Asignación (Dupla Nueva)";
    document.getElementById('v-id').value = "";
    addCampoPersonal('vacunador', 5);
    addCampoPersonal('anotador', 5);
    addCampoPersonal('profesional', 5);
    addCampoPersonal('desistimientos', 5);
  }
  document.getElementById('frm-dupla').scrollIntoView({ behavior: 'smooth' });
}

async function guardarDiario(e) {
  e.preventDefault();
  if (!isAdminCronograma) return window.location.replace('/login');

  const payload = {
      id: document.getElementById('v-id').value || null,
      fecha: document.getElementById('v-fecha').value,
      dupla: document.getElementById('v-dupla').value,
      lugar: document.getElementById('v-lugar').value.toUpperCase(),
      hora_inicio: document.getElementById('v-h-ini').value,
      hora_fin: document.getElementById('v-h-fin').value,
      horario: `${document.getElementById('v-h-ini').value} - ${document.getElementById('v-h-fin').value}`
  };

  const roles = [
      { ui: 'vacunador', db_n: 'vacunador', db_t: 'tel_vacunador' },
      { ui: 'anotador', db_n: 'anotador', db_t: 'tel_anotador' },
      { ui: 'profesional', db_n: 'profesional_valoracion', db_t: 'tel_profesional' },
      { ui: 'desistimientos', db_n: 'desistimientos', db_t: 'tel_desistimientos' }
  ];

  roles.forEach(r => {
      let noms = Array.from(document.querySelectorAll(`.dyn-nom-${r.ui}`)).map(i => i.value.trim().toUpperCase()).filter(v => v !== '');
      let tels = Array.from(document.querySelectorAll(`.dyn-tel-${r.ui}`)).map((i, idx) => noms[idx] ? i.value.trim() : '').filter((_, idx) => noms[idx] !== '');
      payload[r.db_n] = noms.join(' | ');
      payload[r.db_t] = tels.join(' | ');
  });

  try {
    const res = await fetch('/api/cronograma/diario', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
    });
    const data = await res.json();
    alert(data.status === 'success' ? "✅ " + data.msg : "❌ Error: " + data.msg);
    if(data.status === 'success') {
      document.getElementById('form-vacunacion').style.display = 'none';
      cargarDiario();
    }
  } catch (err) { alert("Error de red."); }
}

async function eliminarDupla(id) {
  if (!isAdminCronograma) return window.location.replace('/login');
  if(!confirm("⚠️ ¿Desea eliminar definitivamente esta dupla?")) return;
  try {
    const res = await fetch(`/api/cronograma/diario/${id}`, { method: 'DELETE' });
    const data = await res.json();
    alert(data.status === 'success' ? "✅ " + data.msg : "❌ Error: " + data.msg);
    if(data.status === 'success') cargarDiario();
  } catch (err) { alert("Error de red."); }
}

function exportarPDFDiario() {
  const fecha = document.getElementById('filtro-fecha').value;
  window.open(`/api/cronograma/pdf?fecha=${fecha}`, '_blank');
}