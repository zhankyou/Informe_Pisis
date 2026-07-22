# -*- coding: utf-8 -*-
from modulos.inf_db_utils import table_exists, find_column, get_count, get_list


def extraer_datos_2024():
    res = {"kpis": {"familias": 0, "personas": 0, "gestantes": 0, "discapacidad": 0}, "charts": {"sexo": [], "eps": []}}
    t_fam, t_ind = "aps_2024_familias", "aps_2024_integrantes"

    if table_exists(t_fam):
        res["kpis"]["familias"] = get_count(f"SELECT COUNT(*) FROM {t_fam}")
        c_gest = find_column(t_fam, ["gestante", "embarazo"])
        if c_gest:
            res["kpis"]["gestantes"] = get_count(
                f"SELECT COUNT(*) FROM {t_fam} WHERE CAST({c_gest} AS TEXT) ILIKE '%SI%' OR CAST({c_gest} AS TEXT) = '1'")

    if table_exists(t_ind):
        res["kpis"]["personas"] = get_count(f"SELECT COUNT(*) FROM {t_ind}")

        c_disc = find_column(t_ind, ["discapacidad", "reconoce_algu", "limitacion"])
        if c_disc:
            res["kpis"]["discapacidad"] = get_count(
                f"SELECT COUNT(*) FROM {t_ind} WHERE {c_disc} IS NOT NULL AND CAST({c_disc} AS TEXT) NOT ILIKE '%Ninguna%' AND CAST({c_disc} AS TEXT) NOT ILIKE '%No aplica%' AND CAST({c_disc} AS TEXT) NOT ILIKE '%Sin discapacidad%'")

        c_sexo = find_column(t_ind, ["sexo", "genero"])
        if c_sexo:
            raw_sex = get_list(
                f"SELECT {c_sexo} as label, COUNT(*) as total FROM {t_ind} WHERE {c_sexo} IS NOT NULL GROUP BY 1 ORDER BY 2 DESC")
            res["charts"]["sexo"] = [
                {"label": str(r["label"]).replace('1. ', '').replace('2. ', '')[:15], "total": r["total"]} for r in
                raw_sex]

        c_eps = find_column(t_ind, ["eapb", "eps", "aseguradora"])
        if c_eps:
            raw_eps = get_list(
                f"SELECT {c_eps} as label, COUNT(*) as total FROM {t_ind} WHERE {c_eps} IS NOT NULL AND CAST({c_eps} AS TEXT) != 'None' AND TRIM(CAST({c_eps} AS TEXT)) != '' GROUP BY 1 ORDER BY 2 DESC LIMIT 5")
            res["charts"]["eps"] = [{"label": str(r["label"])[:25], "total": r["total"]} for r in raw_eps]

    return res