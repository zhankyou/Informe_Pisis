const nombresMeses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"];
const diasSemanaFull = ["DOMINGO", "LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO"];
const anioActual = new Date().getFullYear();

function checkEditability(fechaObj) {
  const hoy = new Date();
  const mesEval = new Date(fechaObj.getFullYear(), fechaObj.getMonth(), 1);
  const mesActual = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
  return mesEval >= mesActual;
}

function switchTab(tabId, element) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
  element.classList.add('active');
  document.getElementById(tabId).classList.add('active');
}

async function cargarActividadesCatalogo() {
  try {
    const res = await fetch('/api/cronograma/actividades');
    const json = await res.json();
    if(json.status === 'success' && json.data.length > 0) {
      const select = document.getElementById('f-actividad');
      let html = `<option value="REVISIÓN DE ENTREGABLES">REVISIÓN DE ENTREGABLES</option>
                  <option value="RECEPCIÓN DE ENTREGABLES">RECEPCIÓN DE ENTREGABLES</option>`;
      json.data.forEach(act => {
        html += `<option value="${act.nombre}">${act.nombre}</option>`;
      });
      if(select) select.innerHTML = html;
    }
  } catch (e) { console.error(e); }
}

function abrirModalActividades() {
  document.getElementById('nueva-actividad').value = '';
  document.getElementById('modal-actividades').style.display = 'flex';
}

async function guardarActividad() {
  const nombre = document.getElementById('nueva-actividad').value.toUpperCase();
  if(!nombre) return alert('El nombre es obligatorio');
  try {
    const res = await fetch('/api/cronograma/actividades', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({nombre})
    });
    const data = await res.json();
    if(data.status === 'success') {
      document.getElementById('modal-actividades').style.display = 'none';
      cargarActividadesCatalogo();
    } else alert("Error: " + data.msg);
  } catch (e) { alert("Error de red"); }
}

document.addEventListener('DOMContentLoaded', () => {
  let htmlMeses = '';
  for(let i=0; i<12; i++){
      let val = `${anioActual}-${String(i+1).padStart(2,'0')}`;
      htmlMeses += `<option value="${val}">${nombresMeses[i]} ${anioActual}</option>`;
  }
  const fMesFiltro = document.getElementById('filtro-mes');
  if(fMesFiltro) fMesFiltro.innerHTML = htmlMeses;

  const selectEquipo = document.getElementById('f-equipo');
  const selectTerritorio = document.getElementById('f-territorio');
  if(selectEquipo && selectTerritorio) {
      for(let i=1; i<=64; i++) {
          selectEquipo.innerHTML += `<option value="${i}">EQUIPO ${i}</option>`;
          selectTerritorio.innerHTML += `<option value="${i}">TERRITORIO ${i}</option>`;
      }
  }

  const mesActualStr = `${anioActual}-${String(new Date().getMonth()+1).padStart(2,'0')}`;
  if(fMesFiltro) fMesFiltro.value = mesActualStr;
  const fMes = document.getElementById('f-mes');
  if(fMes) fMes.value = mesActualStr;

  const fFecha = document.getElementById('filtro-fecha');
  if(fFecha) fFecha.valueAsDate = new Date();

  cargarActividadesCatalogo();

  // Iniciar dependencias si existen
  if(typeof cargarDiario === 'function') cargarDiario();
  if(typeof cargarMensual === 'function') cargarMensual();
});