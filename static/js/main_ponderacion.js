let categoriaActual = 'ENFERMERIA';
const formatoMoneda = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' });

const matricesBase = {
    'ENFERMERIA': [
        { item: 1, pct: 3, meta: 1 }, { item: 2, pct: 3, meta: 1 }, { item: 3, pct: 5, meta: 2 },
        { item: 4, pct: 5, meta: 1 }, { item: 5, pct: 1, meta: 1 }, { item: 6, pct: 8, meta: 1 },
        { item: 7, pct: 10, meta: 75 }, { item: 8, pct: 10, meta: 75 }, { item: 9, pct: 5, meta: 225 },
        { item: 10, pct: 7, meta: 1 }, { item: 11, pct: 5, meta: 1 }, { item: 12, pct: 10, meta: 1 },
        { item: 13, pct: 5, meta: 1 }, { item: 14, pct: 4, meta: 1 }, { item: 15, pct: 6, meta: 1 },
        { item: 16, pct: 1, meta: 1 }, { item: 17, pct: 2, meta: 1 }, { item: 18, pct: 5, meta: 1 },
        { item: 19, pct: 1, meta: 1 }, { item: 20, pct: 3, meta: 1 }, { item: 21, pct: 0, meta: 1 },
        { item: 22, pct: 1, meta: 1 }
    ],
    'MEDICINA': [
        { item: 1, pct: 3, meta: 1 }, { item: 2, pct: 3, meta: 1 }, { item: 3, pct: 5, meta: 2 },
        { item: 4, pct: 5, meta: 1 }, { item: 5, pct: 1, meta: 1 }, { item: 6, pct: 12, meta: 1 },
        { item: 7, pct: 12, meta: 75 }, { item: 8, pct: 12, meta: 75 }, { item: 9, pct: 6, meta: 225 },
        { item: 10, pct: 10, meta: 1 }, { item: 11, pct: 5, meta: 1 }, { item: 12, pct: 2, meta: 1 },
        { item: 13, pct: 4, meta: 1 }, { item: 14, pct: 2, meta: 1 }, { item: 15, pct: 6, meta: 1 },
        { item: 16, pct: 1, meta: 1 }, { item: 17, pct: 2, meta: 1 }, { item: 18, pct: 5, meta: 1 },
        { item: 19, pct: 1, meta: 1 }, { item: 20, pct: 2, meta: 1 }, { item: 21, pct: 0, meta: 1 },
        { item: 22, pct: 1, meta: 1 }
    ],
    'PSICOLOGIA': [
        { item: 1, pct: 3, meta: 1 }, { item: 2, pct: 3, meta: 1 }, { item: 3, pct: 3, meta: 2 },
        { item: 4, pct: 3, meta: 1 }, { item: 5, pct: 3, meta: 1 }, { item: 6, pct: 5, meta: 1 },
        { item: 7, pct: 5, meta: 75 }, { item: 8, pct: 5, meta: 75 }, { item: 9, pct: 1, meta: 225 },
        { item: 10, pct: 12, meta: 1 }, { item: 11, pct: 12, meta: 1 }, { item: 12, pct: 6, meta: 1 },
        { item: 13, pct: 11, meta: 1 }, { item: 14, pct: 3, meta: 1 }, { item: 15, pct: 5, meta: 1 },
        { item: 16, pct: 5, meta: 1 }, { item: 17, pct: 5, meta: 1 }, { item: 18, pct: 8, meta: 1 },
        { item: 19, pct: 1, meta: 1 }, { item: 20, pct: 1, meta: 1 }, { item: 21, pct: 0, meta: 1 },
        { item: 22, pct: 0, meta: 1 }
    ],
    'TECNICO': [
        { item: 1, pct: 3, meta: 1 }, { item: 2, pct: 3, meta: 1 }, { item: 3, pct: 3, meta: 2 },
        { item: 4, pct: 5, meta: 1 }, { item: 5, pct: 5, meta: 1 }, { item: 6, pct: 12, meta: 1 },
        { item: 7, pct: 12, meta: 75 }, { item: 8, pct: 7, meta: 75 }, { item: 9, pct: 12, meta: 225 },
        { item: 10, pct: 10, meta: 1 }, { item: 11, pct: 4, meta: 1 }, { item: 12, pct: 2, meta: 1 },
        { item: 13, pct: 2, meta: 1 }, { item: 14, pct: 3, meta: 1 }, { item: 15, pct: 5, meta: 1 },
        { item: 16, pct: 3, meta: 1 }, { item: 17, pct: 3, meta: 1 }, { item: 18, pct: 3, meta: 1 },
        { item: 19, pct: 2, meta: 1 }, { item: 20, pct: 0, meta: 1 }, { item: 21, pct: 1, meta: 1 }
    ]
};

function setCategoria(cat, btn) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    categoriaActual = cat;
    document.getElementById('lbl-cat').textContent = cat;
    limpiarFormulario();
    cargarTabla();
}

function inicializarMatriz(itemsToLoad = null) {
    const tbody = document.getElementById('tbody-matriz');
    tbody.innerHTML = '';
    const arr = itemsToLoad || matricesBase[categoriaActual];

    arr.forEach(data => {
        agregarFilaMatriz(data.item, data.pct, data.meta, data.ejecucion || 0);
    });
    calcularMatriz();
}

function agregarFilaMatriz(itemStr = '', pct = 0, meta = 1, ejecucion = 0) {
    const tbody = document.getElementById('tbody-matriz');
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><input type="text" class="mat-item" value="${itemStr}"></td>
        <td><input type="number" class="mat-pct" step="0.01" value="${pct}" oninput="calcularMatriz()"></td>
        <td><input type="text" class="mat-valpct" readonly tabindex="-1"></td>
        <td class="col-meta"><input type="number" class="mat-meta" value="${meta}" oninput="calcularMatriz()"></td>
        <td class="col-ejec"><input type="number" class="mat-ejec" value="${ejecucion}" oninput="calcularMatriz()"></td>
        <td><input type="text" class="mat-pago" readonly tabindex="-1" style="color: #059669; font-weight: 700;"></td>
        <td class="no-print"><button type="button" class="btn-del" onclick="this.closest('tr').remove(); calcularMatriz()">🗑</button></td>
    `;
    tbody.appendChild(tr);
}

function calcularMatriz() {
    const totalContrato = parseFloat(document.getElementById('valor_contrato').value) || 0;
    const filas = document.querySelectorAll('#tbody-matriz tr');

    let sumPct = 0;
    let sumPago = 0;

    filas.forEach(tr => {
        const pct = parseFloat(tr.querySelector('.mat-pct').value) || 0;
        const meta = parseFloat(tr.querySelector('.mat-meta').value) || 0;
        const ejec = parseFloat(tr.querySelector('.mat-ejec').value) || 0;

        sumPct += pct;

        const valorPct = totalContrato * (pct / 100);
        tr.querySelector('.mat-valpct').value = formatoMoneda.format(valorPct);

        let pagoMes = 0;
        if (meta > 0) {
            pagoMes = (ejec >= meta) ? valorPct : (ejec / meta) * valorPct;
        }

        tr.querySelector('.mat-pago').value = formatoMoneda.format(pagoMes);
        sumPago += pagoMes;
    });

    document.getElementById('tot-porcentaje').textContent = sumPct.toFixed(2);
    document.getElementById('tot-cobro').textContent = formatoMoneda.format(sumPago);
    document.getElementById('lbl_valor_cobrar').textContent = formatoMoneda.format(sumPago);
    document.getElementById('valor_cobrar').value = sumPago.toFixed(2);
}

function extraerItemsBD() {
    const items = [];
    document.querySelectorAll('#tbody-matriz tr').forEach(tr => {
        items.push({
            item: tr.querySelector('.mat-item').value,
            pct: parseFloat(tr.querySelector('.mat-pct').value) || 0,
            meta: parseFloat(tr.querySelector('.mat-meta').value) || 0,
            ejecucion: parseFloat(tr.querySelector('.mat-ejec').value) || 0
        });
    });
    return JSON.stringify(items);
}

async function guardarRegistro(e) {
    e.preventDefault();
    const id = document.getElementById('reg_id').value;
    const data = {
        categoria: categoriaActual,
        nombre_completo: document.getElementById('nombre_completo').value,
        numero_documento: document.getElementById('numero_documento').value,
        numero_contrato: document.getElementById('numero_contrato').value,
        cuenta: document.getElementById('cuenta').value,
        fecha_inicio: document.getElementById('fecha_inicio').value,
        fecha_fin: document.getElementById('fecha_fin').value,
        valor_contrato: document.getElementById('valor_contrato').value,
        valor_cobrar: document.getElementById('valor_cobrar').value,
        observaciones: document.getElementById('observaciones').value,
        detalles_items: extraerItemsBD()
    };

    const url = id ? `/api/ponderacion/${id}` : '/api/ponderacion';
    const method = id ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const json = await res.json();

        if (json.status === 'success') {
            alert(json.msg);
            limpiarFormulario();
            cargarTabla();
        } else { alert("Error: " + json.msg); }
    } catch (e) { alert("Fallo de conexión en el guardado."); }
}

async function cargarTabla() {
    const q = document.getElementById('busqueda').value.trim();
    const tbody = document.getElementById('tbody-datos');
    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding: 25px;">Cargando registros...</td></tr>';

    try {
        const res = await fetch(`/api/ponderacion/${categoriaActual}?q=${encodeURIComponent(q)}`);
        const json = await res.json();

        if (json.status === 'success') {
            if (json.data.length === 0) {
                tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding: 25px; color: var(--muted);">No hay registros históricos en esta categoría.</td></tr>`;
                return;
            }
            tbody.innerHTML = json.data.map(row => `
                <tr>
                    <td style="text-align: center;"><button class="btn-edit" onclick='editarRegistro(${JSON.stringify(row).replace(/'/g, "&#39;")})'>Editar</button></td>
                    <td style="font-weight: 600;">${row.nombre_completo}</td>
                    <td>${row.numero_documento}</td>
                    <td>${row.numero_contrato}</td>
                    <td>${row.fecha_inicio} al ${row.fecha_fin}</td>
                    <td>${row.cuenta}</td>
                    <td>${formatoMoneda.format(row.valor_contrato)}</td>
                    <td style="font-weight: 700; color: var(--teal);">${formatoMoneda.format(row.valor_cobrar)}</td>
                    <td style="white-space: normal; min-width: 250px;">${row.observaciones || '-'}</td>
                </tr>
            `).join('');
        } else { tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; color: #e53935;">Error cargando datos de BD.</td></tr>`; }
    } catch (e) { tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; color: #e53935;">Error de conexión.</td></tr>`; }
}

function editarRegistro(row) {
    document.getElementById('reg_id').value = row.id;
    document.getElementById('nombre_completo').value = row.nombre_completo;
    document.getElementById('numero_documento').value = row.numero_documento;
    document.getElementById('numero_contrato').value = row.numero_contrato;
    document.getElementById('cuenta').value = row.cuenta;
    document.getElementById('fecha_inicio').value = row.fecha_inicio;
    document.getElementById('fecha_fin').value = row.fecha_fin;
    document.getElementById('valor_contrato').value = row.valor_contrato;
    document.getElementById('observaciones').value = row.observaciones;

    try {
        const items = JSON.parse(row.detalles_items);
        inicializarMatriz(items.length > 0 ? items : null);
    } catch(e) { inicializarMatriz(); }

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function limpiarFormulario() {
    document.getElementById('form-registro').reset();
    document.getElementById('reg_id').value = '';
    document.getElementById('valor_cobrar').value = '';
    document.getElementById('lbl_valor_cobrar').textContent = '$ 0.00';
    inicializarMatriz();
}

function imprimirComprobante() {
    // 1. Extraer datos del UI
    const vNombre = document.getElementById('nombre_completo').value || '---';
    const vDoc = document.getElementById('numero_documento').value || '---';
    const vContrato = document.getElementById('numero_contrato').value || '---';
    const vCuenta = document.getElementById('cuenta').value || '---';
    const vInicio = document.getElementById('fecha_inicio').value || '---';
    const vFin = document.getElementById('fecha_fin').value || '---';
    const vObs = document.getElementById('observaciones').value || 'Sin observaciones registradas.';

    // 2. Inyectar al Template Oculto
    document.getElementById('pt-cat').textContent = categoriaActual;
    document.getElementById('pt-nombre').textContent = vNombre;
    document.getElementById('pt-doc').textContent = vDoc;
    document.getElementById('pt-contrato').textContent = vContrato;
    document.getElementById('pt-cuenta').textContent = vCuenta;
    document.getElementById('pt-periodo').textContent = `${vInicio} al ${vFin}`;

    const now = new Date();
    document.getElementById('pt-fecha-gen').textContent = `Generado el: ${now.toLocaleDateString()} a las ${now.toLocaleTimeString()}`;

    document.getElementById('pt-obs').textContent = vObs;
    document.getElementById('pt-val-base').textContent = formatoMoneda.format(document.getElementById('valor_contrato').value || 0);
    document.getElementById('pt-val-cobro').textContent = document.getElementById('lbl_valor_cobrar').textContent;
    document.getElementById('pt-tot-pct').textContent = document.getElementById('tot-porcentaje').textContent + '%';
    document.getElementById('pt-tot-cobro').textContent = document.getElementById('tot-cobro').textContent;

    // 3. Llenar la Tabla
    const tbMatriz = document.getElementById('tbody-matriz');
    const ptTbody = document.getElementById('pt-tbody');
    ptTbody.innerHTML = '';

    Array.from(tbMatriz.querySelectorAll('tr')).forEach(tr => {
        const item = tr.querySelector('.mat-item').value;
        const pct = tr.querySelector('.mat-pct').value;
        const valpct = tr.querySelector('.mat-valpct').value;
        const meta = tr.querySelector('.mat-meta').value;
        const ejec = tr.querySelector('.mat-ejec').value;
        const pago = tr.querySelector('.mat-pago').value;

        ptTbody.innerHTML += `
            <tr>
                <td>${item}</td>
                <td>${pct}%</td>
                <td>${valpct}</td>
                <td class="bg-print-highlight">${meta}</td>
                <td class="bg-print-highlight">${ejec}</td>
                <td class="bg-print-pago">${pago}</td>
            </tr>
        `;
    });

    // 4. Lanzar la ventana de Impresión Nativa (Navegador)
    window.print();
}

document.addEventListener('DOMContentLoaded', () => {
    inicializarMatriz();
    cargarTabla();

    document.getElementById('form-registro').addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.target.tagName !== 'BUTTON' && e.target.tagName !== 'TEXTAREA') {
            e.preventDefault();
        }
    });

    // Navegación Vertical
    document.getElementById('tbody-matriz').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const inputActual = e.target;

            if (inputActual.tagName === 'INPUT') {
                const td = inputActual.closest('td');
                const tr = td.closest('tr');
                const colIndex = Array.from(tr.children).indexOf(td);
                const nextTr = tr.nextElementSibling;

                if (nextTr) {
                    const nextInput = nextTr.children[colIndex].querySelector('input');
                    if (nextInput) {
                        nextInput.focus();
                        nextInput.select();
                    }
                }
            }
        }
    });
});