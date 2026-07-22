# -*- coding: utf-8 -*-
import re
from modulos.inf_db_utils import get_list


def clean_currency(val):
    if not val: return 0.0
    val_str = re.sub(r'[^\d\.-]', '', str(val))
    try:
        return float(val_str) if val_str else 0.0
    except ValueError:
        return 0.0


def extraer_financiero():
    res_fin = {
        "global": {"girado": 0.0, "ejecutado": 0.0, "rendimientos": 0.0},
        "resoluciones": []
    }

    try:
        recursos = get_list(
            "SELECT id_recurso, descripcion, estado FROM ser_recursos WHERE estado IN ('ACTIVA', 'FINALIZADA')")
        if not recursos:
            return res_fin

        inc_raw = get_list(
            "SELECT id_recurso, SUM(valor_incorporado) as total_girado FROM ser_incorporacion GROUP BY id_recurso")
        map_inc = {str(r["id_recurso"]).strip(): clean_currency(r["total_girado"]) for r in inc_raw}

        ren_raw = get_list(
            "SELECT id_recurso, SUM(valor_reintegrado) as total_rendimientos FROM ser_reintegro_rendimientos GROUP BY id_recurso")
        map_ren = {str(r["id_recurso"]).strip(): clean_currency(r["total_rendimientos"]) for r in ren_raw}

        contratos = get_list("SELECT id_recurso, valor_contrato, objeto FROM ser_contratos")

        for rec in recursos:
            id_rec = str(rec.get("id_recurso", "")).strip()
            if not id_rec: continue

            girado = map_inc.get(id_rec, 0.0)
            rendimientos = map_ren.get(id_rec, 0.0)
            ejecutado = 0.0

            med, enf, psi, esp, tec = 0.0, 0.0, 0.0, 0.0, 0.0

            contratos_rec = [c for c in contratos if str(c.get("id_recurso", "")).strip() == id_rec]

            for c in contratos_rec:
                val_contrato = clean_currency(c.get("valor_contrato", 0))
                ejecutado += val_contrato

                obj_up = str(c.get("objeto", "")).upper()

                if any(x in obj_up for x in ["MEDICINA", "MEDICO", "MÉDICO", "MEDICA", "MÉDICA"]):
                    med += val_contrato
                elif any(x in obj_up for x in ["ENFERMERIA", "ENFERMERÍA", "ENFERMERO", "ENFERMERA"]):
                    enf += val_contrato
                elif any(x in obj_up for x in
                         ["PSICOLOGIA", "PSICOLOGÍA", "PSICOLOGO", "PSICÓLOGO", "PSICOLOGA", "PSICÓLOGA"]):
                    psi += val_contrato
                elif any(x in obj_up for x in ["TECNICO", "TÉCNICO", "AUXILIAR", "PROMOTOR", "TECNOLOGO", "TECNÓLOGO"]):
                    tec += val_contrato
                else:
                    esp += val_contrato

            saldo = (girado - ejecutado) if (girado - ejecutado) > 0 else 0.0

            res_fin["global"]["girado"] += girado
            res_fin["global"]["ejecutado"] += ejecutado
            res_fin["global"]["rendimientos"] += rendimientos

            res_fin["resoluciones"].append({
                "id": id_rec,
                "descripcion": str(rec.get("descripcion", "Sin descripción")),
                "estado": str(rec.get("estado", "ACTIVA")),
                "girado": girado,
                "ejecutado": ejecutado,
                "rendimientos": rendimientos,
                "saldo": saldo,
                "perfiles": {"med": med, "enf": enf, "psi": psi, "esp": esp, "tec": tec}
            })

    except Exception as e:
        print(f"[*] Falla en Extracción Financiera: {e}")

    return res_fin