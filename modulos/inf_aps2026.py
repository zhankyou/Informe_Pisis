# -*- coding: utf-8 -*-
from modulos.inf_db_utils import table_exists, find_column, get_count, get_list


def extraer_datos_2026():
    res = {"kpis": {"familias": 0, "personas": 0, "gestantes": 0, "discapacidad": 0}, "charts": {"sexo": [], "eps": []}}
    t_fam, t_ind = "caracterizacion_si_aps_familiar_2026", "caracterizacion_si_aps_individual_2026"

    if table_exists(t_fam):
        res["kpis"]["familias"] = get_count(f"SELECT COUNT(*) FROM {t_fam}")
        c_gest_fam = find_column(t_fam, ["gestante_en_la", "gestante"])
        if c_gest_fam:
            res["kpis"]["gestantes"] += get_count(
                f"SELECT COUNT(*) FROM {t_fam} WHERE CAST({c_gest_fam} AS TEXT) ILIKE '%SI%'")

    if table_exists(t_ind):
        res["kpis"]["personas"] = get_count(f"SELECT COUNT(*) FROM {t_ind}")
        c_gest_ind = find_column(t_ind, ["encuentra_e", "gestante"])

        if c_gest_ind and res["kpis"]["gestantes"] == 0:
            res["kpis"]["gestantes"] = get_count(
                f"SELECT COUNT(*) FROM {t_ind} WHERE CAST({c_gest_ind} AS TEXT) ILIKE '%SI%'")

        c_disc = find_column(t_ind, ["reconoce_algu", "discapacidad"])
        if c_disc:
            res["kpis"]["discapacidad"] = get_count(
                f"SELECT COUNT(*) FROM {t_ind} WHERE {c_disc} IS NOT NULL AND CAST({c_disc} AS TEXT) NOT ILIKE '%Sin discapacidad%' AND CAST({c_disc} AS TEXT) NOT ILIKE '%Ninguna%'")

        c_sexo = find_column(t_ind, ["sexo_al_nacer", "sexo"])
        if c_sexo:
            raw_sex = get_list(
                f"SELECT {c_sexo} as label, COUNT(*) as total FROM {t_ind} WHERE {c_sexo} IS NOT NULL GROUP BY 1 ORDER BY 2 DESC")
            res["charts"]["sexo"] = [
                {"label": str(r["label"]).replace('1. ', '').replace('2. ', '')[:15], "total": r["total"]} for r in
                raw_sex]

        c_eps = find_column(t_ind, ["eapb", "aseguradora"])
        if c_eps:
            raw_eps = get_list(
                f"SELECT {c_eps} as label, COUNT(*) as total FROM {t_ind} WHERE {c_eps} IS NOT NULL AND CAST({c_eps} AS TEXT) != 'None' AND TRIM(CAST({c_eps} AS TEXT)) != '' GROUP BY 1 ORDER BY 2 DESC LIMIT 5")
            res["charts"]["eps"] = [{"label": str(r["label"])[:25], "total": r["total"]} for r in raw_eps]

    return res