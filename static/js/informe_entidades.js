const formatoMoneda = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 });
let globalData = {};

function switchTab(tabId, btn) {
    document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
    btn.classList.add('active');
}

function renderChart(id, type, labels, data, colors) {
    const ctx = document.getElementById(id);
    if(!ctx) return;
    if(labels.length === 0 || data.every(v => v === 0)) { labels = ['Sin Datos']; data = [1]; colors = '#e2e8f0'; }
    new Chart(ctx, {
        type: type,
        data: { labels: labels, datasets: [{ data: data, backgroundColor: colors, borderRadius: type === 'bar' ? 4 : 0 }] },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: type !== 'bar', position: 'right', labels: {font: {size: 10, family: 'Sora'}} },
                       tooltip: { callbacks: { label: c => type === 'bar' ? formatoMoneda.format(c.raw) : c.raw } } },
            scales: type === 'bar' ? { y: { beginAtZero: true } } : {},
            animation: { duration: 0 } // Desactiva animación para capturar imagen Base64 instantáneamente
        }
    });
}

async function cargarInformeEntidades() {
    try {
        const res = await fetch('/api/informe_entidades/datos');
        const json = await res.json();

        if (json.status === 'success') {
            globalData = json.data;
            const d = json.data;
            const fin = d.financiero;

            document.getElementById('fin-girado').textContent = formatoMoneda.format(fin.global.girado || 0);
            document.getElementById('fin-eje').textContent = formatoMoneda.format(fin.global.ejecutado || 0);

            const contRes = document.getElementById('contenedor-resoluciones');
            contRes.innerHTML = '';

            if(fin.resoluciones.length === 0) {
                contRes.innerHTML = '<div style="color:var(--muted); text-align:center;">No se detectaron resoluciones financieras activas.</div>';
            }

            fin.resoluciones.forEach((r, i) => {
                const idChart1 = `c-fin-eje-${i}`;
                const idChart2 = `c-fin-perf-${i}`;
                const perf = r.perfiles;

                contRes.innerHTML += `
                    <div style="margin-bottom: 30px; border-top: 2px dashed var(--border); padding-top: 20px;">
                        <div style="font-size: 1.05rem; font-weight: 700; color: var(--navy); margin-bottom: 15px;">
                            Resolución: ${r.id} - ${r.descripcion.slice(0,80)}...
                            <span class="stat-badge">${r.estado}</span>
                        </div>
                        
                        <div class="kpi-grid" style="grid-template-columns: repeat(4, 1fr); margin-bottom: 15px;">
                            <div class="kpi g"><div class="kpi-n" style="font-size: 1.2rem;">${formatoMoneda.format(r.girado)}</div><div class="kpi-l">Incorporado</div></div>
                            <div class="kpi p"><div class="kpi-n" style="font-size: 1.2rem;">${formatoMoneda.format(r.ejecutado)}</div><div class="kpi-l">Gastado</div></div>
                            <div class="kpi o"><div class="kpi-n" style="font-size: 1.2rem;">${formatoMoneda.format(r.saldo)}</div><div class="kpi-l">Saldo a Devolver</div></div>
                            <div class="kpi r"><div class="kpi-n" style="font-size: 1.2rem;">${formatoMoneda.format(r.rendimientos)}</div><div class="kpi-l">Rendimientos</div></div>
                        </div>

                        <div style="display: grid; grid-template-columns: 1fr 1.5fr; gap: 20px;">
                            <div class="cbox">
                                <h4>Balance de Ejecución vs Devolución</h4>
                                <div class="cwrap"><canvas id="${idChart1}"></canvas></div>
                            </div>
                            <div class="cbox">
                                <h4>Inversión por Perfiles Profesionales</h4>
                                <div class="cwrap"><canvas id="${idChart2}"></canvas></div>
                                <table style="margin-top:10px; font-size:0.75rem; background:transparent;">
                                    <tr><td>Profesional Medicina</td><td style="text-align:right; font-weight:bold;">${formatoMoneda.format(perf.med)}</td></tr>
                                    <tr><td>Profesional Enfermería</td><td style="text-align:right; font-weight:bold;">${formatoMoneda.format(perf.enf)}</td></tr>
                                    <tr><td>Profesional Psicología</td><td style="text-align:right; font-weight:bold;">${formatoMoneda.format(perf.psi)}</td></tr>
                                    <tr><td>Especialidades / Otros</td><td style="text-align:right; font-weight:bold;">${formatoMoneda.format(perf.esp)}</td></tr>
                                    <tr><td>Técnico o Aux. Enfermería</td><td style="text-align:right; font-weight:bold;">${formatoMoneda.format(perf.tec)}</td></tr>
                                </table>
                            </div>
                        </div>
                    </div>
                `;
            });

            const tb = document.getElementById('tb-comparativo');
            let tF = 0, tP = 0, tG = 0, tD = 0;

            [2024, 2025, 2026].forEach(yr => {
                const row = d[yr.toString()];
                if(!row) return;

                const k = row.kpis;
                tF += k.familias; tP += k.personas; tG += k.gestantes; tD += k.discapacidad;

                tb.innerHTML += `
                    <tr>
                        <td style="font-weight: 700; color: var(--navy);">${yr}</td>
                        <td>${k.familias.toLocaleString('es-CO')}</td>
                        <td>${k.personas.toLocaleString('es-CO')}</td>
                        <td>${k.gestantes.toLocaleString('es-CO')}</td>
                        <td>${k.discapacidad.toLocaleString('es-CO')}</td>
                    </tr>`;

                const suf = yr.toString().slice(2);
                const elFam = document.getElementById(`k${suf}-fam`);
                if(elFam) elFam.textContent = k.familias.toLocaleString('es-CO');
                const elPer = document.getElementById(`k${suf}-per`);
                if(elPer) elPer.textContent = k.personas.toLocaleString('es-CO');
                const elGes = document.getElementById(`k${suf}-ges`);
                if(elGes) elGes.textContent = k.gestantes.toLocaleString('es-CO');
            });

            tb.innerHTML += `
                <tr style="background: #f8fafc;">
                    <td style="font-weight: 700; color: var(--teal);">TOTAL ACUMULADO</td>
                    <td style="font-weight: 700;">${tF.toLocaleString('es-CO')}</td>
                    <td style="font-weight: 700;">${tP.toLocaleString('es-CO')}</td>
                    <td style="font-weight: 700;">${tG.toLocaleString('es-CO')}</td>
                    <td style="font-weight: 700;">${tD.toLocaleString('es-CO')}</td>
                </tr>`;

            // Timeout para asegurar montaje del DOM
            setTimeout(() => {
                fin.resoluciones.forEach((r, i) => {
                    renderChart(`c-fin-eje-${i}`, 'doughnut', ['Ejecutado', 'Saldo a Devolver'], [r.ejecutado, r.saldo], ['#3498db', '#f39c12']);
                    const p = r.perfiles;
                    const lbls = ['Medicina', 'Enfermería', 'Psicología', 'Especialidades', 'Técnico/Auxiliar'];
                    const vals = [p.med, p.enf, p.psi, p.esp, p.tec];
                    const cols = ['#e74c3c', '#1abc9c', '#9b59b6', '#f1c40f', '#34495e'];
                    renderChart(`c-fin-perf-${i}`, 'bar', lbls, vals, cols);
                });

                new Chart(document.getElementById('chart-comparativo').getContext('2d'), {
                    type: 'bar',
                    data: {
                        labels: ['2024', '2025', '2026'],
                        datasets: [
                            { label: 'Familias Caracterizadas', data: [d["2024"]?.kpis.familias || 0, d["2025"]?.kpis.familias || 0, d["2026"]?.kpis.familias || 0], backgroundColor: '#1abc9c', borderRadius: 4 },
                            { label: 'Población Tamizada', data: [d["2024"]?.kpis.personas || 0, d["2025"]?.kpis.personas || 0, d["2026"]?.kpis.personas || 0], backgroundColor: '#34495e', borderRadius: 4 }
                        ]
                    },
                    options: { responsive: true, maintainAspectRatio: false, animation: { duration: 0 } }
                });

                [2024, 2025, 2026].forEach(yr => {
                    const row = d[yr.toString()];
                    if(!row) return;
                    const suf = yr.toString().slice(2);
                    renderChart(`c${suf}-sex`, 'doughnut', row.charts.sexo.map(x=>x.label), row.charts.sexo.map(x=>x.total), ['#e74c3c', '#3498db', '#f1c40f']);
                    renderChart(`c${suf}-eps`, 'bar', row.charts.eps.map(x=>x.label), row.charts.eps.map(x=>x.total), '#34495e');
                });
            }, 100);
        }
    } catch (e) {
        console.error("Fallo de renderizado:", e);
    }
}

async function descargarPDF() {
    const btn = document.getElementById('btnExportPDF');
    const entidadInput = document.getElementById('inputEntidad').value;

    // Captura de lienzos a Base64
    let imgComparativo = null;
    let imgPerfiles = null;
    try {
        const cComp = document.getElementById('chart-comparativo');
        if (cComp) imgComparativo = cComp.toDataURL('image/png', 1.0);
        const cPerf = document.getElementById('c-fin-perf-0'); // Extrae gráfico de perfiles de la res principal
        if (cPerf) imgPerfiles = cPerf.toDataURL('image/png', 1.0);
    } catch (e) { console.warn("Gráficos no capturados"); }

    btn.innerHTML = '⏳ Generando PDF...'; btn.disabled = true;
    try {
        const res = await fetch('/api/informe_entidades/pdf', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                financiero: globalData.financiero,
                poblacional: globalData,
                entidad: entidadInput || "Honorable Asamblea Departamental del Meta",
                graficos: { comparativo: imgComparativo, perfiles: imgPerfiles }
            })
        });
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Informe_Ejecutivo_APS_${new Date().toISOString().slice(0,10).replace(/-/g,'')}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
    } catch(e) {
        alert("Fallo al generar el archivo.");
    } finally {
        btn.innerHTML = '🖨️ Imprimir Acta Ejecutiva'; btn.disabled = false;
    }
}

document.addEventListener('DOMContentLoaded', cargarInformeEntidades);