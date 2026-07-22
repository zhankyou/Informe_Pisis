const isAdminMensual = localStorage.getItem('isAdmin') === 'true';
let dataMensual = [];

function initMesesMensual() {
    const selector = document.getElementById('filtro-mes');
    if(!selector) return;
    const hoy = new Date();
    for (let i = 0; i < 3; i++) {
        const d = new Date(hoy.getFullYear(), hoy.getMonth() + i, 1);
        const val = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
        const label = d.toLocaleString('es-ES', { month: 'long', year: 'numeric' }).toUpperCase();
        selector.innerHTML += `<option value="${val}">${label}</option>`;
    }
}

async function cargarMensual() {
    const mes = document.getElementById('filtro-mes').value;
    const btnProg = document.getElementById('btn-prog-mensual');
    if(btnProg) btnProg.style.display = isAdminMensual ? 'block' : 'none';

    try {
        const res = await fetch(`/api/cronograma/mensual?mes=${mes}`);
        const json = await res.json();

        const thead = document.getElementById('thead-mensual');
        const tbody = document.getElementById('tabla-mensual');

        if (json.status === 'success') {
            dataMensual = json.data;
            const diasEnMes = new Date(mes.split('-')[0], mes.split('-')[1], 0).getDate();

            let headHtml = `<tr>
                <th class="th-dark-blue" style="min-width: 150px;">TERRITORIO</th>
                <th class="th-dark-blue">EQUIPO</th>
                <th class="th-dark-blue" style="min-width: 200px;">ACTIVIDAD Y HORARIO</th>`;
            for (let i = 1; i <= diasEnMes; i++) headHtml += `<th class="th-blue">${i}</th>`;
            if(isAdminMensual) headHtml += `<th class="th-dark-blue">ACCIONES</th>`;
            headHtml += `</tr>`;
            thead.innerHTML = headHtml;

            if (dataMensual.length === 0) {
                tbody.innerHTML = `<tr><td colspan="${diasEnMes + (isAdminMensual ? 4 : 3)}" style="color: var(--muted); padding: 20px;">No hay programación para este mes.</td></tr>`;
                return;
            }

            const agrupado = {};
            dataMensual.forEach(row => {
                const key = `${row.territorio}|${row.actividad_desc}|${row.hora_inicio}|${row.hora_fin}`;
                if (!agrupado[key]) {
                    agrupado[key] = {
                        territorio_full: row.territorio,
                        equipo_id: row.equipo_id,
                        actividad: row.actividad_desc,
                        hora_inicio: row.hora_inicio || '',
                        hora_fin: row.hora_fin || '',
                        dias: []
                    };
                }
                agrupado[key].dias.push(new Date(row.fecha).getDate());
            });

            let bodyHtml = "";
            Object.values(agrupado).forEach(item => {
                let equipoF = "N/A";
                let territorioF = item.territorio_full;

                // Separación estricta de la cadena "EQUIPO XX / TERRITORIO XX"
                if (item.territorio_full.includes('/')) {
                    const parts = item.territorio_full.split('/');
                    equipoF = parts[0].trim().toUpperCase().replace('EQUIPO', 'EQ');
                    territorioF = parts[1].trim();
                } else if (item.equipo_id) {
                    equipoF = `EQ ${item.equipo_id}`;
                }

                // Extracción y formateo de hora operativa
                const hi = item.hora_inicio ? item.hora_inicio.slice(0,5) : '';
                const hf = item.hora_fin ? item.hora_fin.slice(0,5) : '';
                const horarioStr = (hi && hf) ? `<br><strong style="color:var(--navy); font-size: 0.75rem;">⌚ ${hi} - ${hf}</strong>` : '';

                bodyHtml += `<tr>
                    <td style="font-weight: 700; text-align: left;">${territorioF}</td>
                    <td style="font-weight: 700; color: var(--teal);">${equipoF}</td>
                    <td style="font-size: 0.7rem; text-align: left; white-space: normal;">${item.actividad}${horarioStr}</td>`;

                for (let i = 1; i <= diasEnMes; i++) {
                    bodyHtml += item.dias.includes(i)
                        ? `<td style="background: #e6f7f5; color: #008f7d; font-weight: 700;">X</td>`
                        : `<td style="color: #e2e8f0;">-</td>`;
                }

                if(isAdminMensual) {
                    const diasArr = JSON.stringify(item.dias);
                    bodyHtml += `<td style="min-width: 80px;">
                        <button class="btn-icon" title="Editar Programación" onclick='editarMensual("${item.territorio_full}", "${item.actividad}", "${item.hora_inicio}", "${item.hora_fin}", ${diasArr})'>✏️</button>
                        <button class="btn-icon" title="Eliminar Programación" onclick="eliminarMensual('${item.territorio_full}', '${item.actividad}')">🗑️</button>
                    </td>`;
                }
                bodyHtml += `</tr>`;
            });

            tbody.innerHTML = bodyHtml;
        }
    } catch (e) {
        console.error("Error cargando mensual", e);
    }
}

function abrirFormMensual() {
    if (!isAdminMensual) return window.location.replace('/login');

    document.getElementById('form-mensual').style.display = 'block';
    const mesVal = document.getElementById('filtro-mes').value;
    document.getElementById('f-mes').value = mesVal;

    const [anio, mesStr] = mesVal.split('-');
    const nombreMes = new Date(anio, parseInt(mesStr)-1, 1).toLocaleString('es-ES', { month: 'long', year: 'numeric' }).toUpperCase();
    document.getElementById('f-mes-display').value = nombreMes;

    const diasEnMes = new Date(anio, mesStr, 0).getDate();
    const contDias = document.getElementById('contenedor-dias');
    contDias.innerHTML = '';
    for (let i = 1; i <= diasEnMes; i++) {
        contDias.innerHTML += `<label><input type="checkbox" name="dias" value="${i}">${i}</label>`;
    }

    document.getElementById('f-actividad').selectedIndex = -1;
    document.getElementById('f-hora-ini').value = '';
    document.getElementById('f-hora-fin').value = '';
    document.getElementById('form-mensual').scrollIntoView({ behavior: 'smooth' });
}

function editarMensual(territorio_full, actividad, h_ini, h_fin, dias) {
    if (!isAdminMensual) return window.location.replace('/login');
    abrirFormMensual();

    const selAct = document.getElementById('f-actividad');
    for(let i = 0; i < selAct.options.length; i++) {
        selAct.options[i].selected = actividad.includes(selAct.options[i].value);
    }

    const fTerritorio = document.getElementById('f-territorio');
    if (fTerritorio) {
        let found = false;
        for(let i = 0; i < fTerritorio.options.length; i++) {
            if(fTerritorio.options[i].value === territorio_full) {
                fTerritorio.selectedIndex = i;
                found = true; break;
            }
        }
        if(!found) fTerritorio.innerHTML += `<option value="${territorio_full}" selected>${territorio_full}</option>`;
    }

    document.getElementById('f-hora-ini').value = h_ini ? h_ini.slice(0,5) : '';
    document.getElementById('f-hora-fin').value = h_fin ? h_fin.slice(0,5) : '';

    document.querySelectorAll('input[name="dias"]').forEach(cb => {
        cb.checked = dias.includes(parseInt(cb.value));
    });
}

async function guardarMensual(e) {
    e.preventDefault();
    if (!isAdminMensual) return window.location.replace('/login');

    const form = new FormData(e.target);
    const diasSeleccionados = form.getAll('dias');
    if (diasSeleccionados.length === 0) return alert("Debe seleccionar al menos un día operativo.");

    const payload = {
        mes: form.get('mes'),
        actividades: form.getAll('actividad'),
        equipo: form.get('equipo') || 1,
        territorio: form.get('territorio') || 'TERRITORIO BASE',
        hora_inicio: form.get('hora_inicio'),
        hora_fin: form.get('hora_fin'),
        dias: diasSeleccionados.map(Number)
    };

    try {
        const res = await fetch('/api/cronograma/mensual', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        alert(data.status === 'success' ? "✅ " + data.msg : "❌ Error: " + data.msg);
        if (data.status === 'success') {
            document.getElementById('form-mensual').style.display = 'none';
            cargarMensual();
        }
    } catch (err) {
        alert("Fallo de conexión.");
    }
}

async function eliminarMensual(territorio, actividad) {
    if (!isAdminMensual) return window.location.replace('/login');
    if (!confirm(`⚠️ ¿Eliminar la programación de ${territorio} para la actividad seleccionada en este mes?`)) return;

    const mes = document.getElementById('filtro-mes').value;
    try {
        const res = await fetch(`/api/cronograma/mensual?mes=${mes}&territorio=${encodeURIComponent(territorio)}&actividad=${encodeURIComponent(actividad)}`, { method: 'DELETE' });
        const data = await res.json();
        alert(data.status === 'success' ? "✅ " + data.msg : "❌ Error: " + data.msg);
        if (data.status === 'success') cargarMensual();
    } catch (err) {
        alert("Fallo de conexión.");
    }
}

function exportarPDFMensual() {
    const mes = document.getElementById('filtro-mes').value;
    window.open(`/api/cronograma/mensual/pdf?mes=${mes}`, '_blank');
}

document.addEventListener('DOMContentLoaded', () => {
    initMesesMensual();
    cargarMensual();
});