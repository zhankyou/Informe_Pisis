# -*- coding: utf-8 -*-
from modulos.inf_db_utils import table_exists, find_column, get_count, get_list

def extraer_datos_2025():
    data = {"hogares": 0, "poblacion": 0, "gestantes": 0, "sexo": [], "aseguramiento": []}
    
    tabla_ind = 'aps_2025_integrantes' if table_exists('aps_2025_integrantes') else 'caracterizacion_si_aps_individual_2025'
        
    if table_exists(tabla_ind):
        data["poblacion"] = get_count(f'SELECT COUNT(*) FROM "{tabla_ind}"')
        
        col_sexo = find_column(tabla_ind, ['sexo', '8_sexo', 'sexo_al_nacer'])
        if col_sexo:
            data["sexo"] = get_list(f'SELECT CAST("{col_sexo}" AS VARCHAR) as label, COUNT(*) as value FROM "{tabla_ind}" WHERE "{col_sexo}" IS NOT NULL AND TRIM(CAST("{col_sexo}" AS VARCHAR)) != \'\' GROUP BY "{col_sexo}"')
            
        col_eps = find_column(tabla_ind, ['eapb', 'eps', 'aseguradora', '14_eapb'])
        if col_eps:
            data["aseguramiento"] = get_list(f'SELECT CAST("{col_eps}" AS VARCHAR) as label, COUNT(*) as value FROM "{tabla_ind}" WHERE "{col_eps}" IS NOT NULL AND TRIM(CAST("{col_eps}" AS VARCHAR)) != \'\' GROUP BY "{col_eps}" ORDER BY value DESC LIMIT 5')
            
        col_gest = find_column(tabla_ind, ['gestante', 'encuentra_e', 'gestante_en_la'])
        if col_gest:
            data["gestantes"] += get_count(f'SELECT COUNT(*) FROM "{tabla_ind}" WHERE UPPER(CAST("{col_gest}" AS VARCHAR)) IN (\'1\', \'SI\', \'SÍ\', \'TRUE\')')
            
    tabla_fam = 'aps_2025_familias' if table_exists('aps_2025_familias') else 'caracterizacion_si_aps_familiar_2025'
    
    if table_exists(tabla_fam):
        data["hogares"] = get_count(f'SELECT COUNT(*) FROM "{tabla_fam}"')
        
        col_gest_fam = find_column(tabla_fam, ['gestante_en_la', 'gestante', 'encuentra_e'])
        if col_gest_fam:
            data["gestantes"] += get_count(f'SELECT COUNT(*) FROM "{tabla_fam}" WHERE UPPER(CAST("{col_gest_fam}" AS VARCHAR)) IN (\'1\', \'SI\', \'SÍ\', \'TRUE\')')

    return data
