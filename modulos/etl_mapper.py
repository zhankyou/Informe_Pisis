# -*- coding: utf-8 -*-
import unicodedata
import re


def sanitizar_pisis(texto, max_len=None):
    if texto is None or str(texto).strip() in ("nan", "null", "None", ""):
        return ""
    val = str(texto).upper()
    val = ''.join(c for c in unicodedata.normalize('NFD', val) if unicodedata.category(c) != 'Mn')
    val = val.replace('N°', 'NO').replace('°', 'NO').replace('"', '')
    val = re.sub(r'[^A-Z0-9\s/.,-]', '', val)
    val = re.sub(r'\s{2,}', ' ', val).strip()
    return val[:max_len] if max_len else val


def extraer_codigo(texto, max_len=None):
    if not texto or str(texto).strip() in ("nan", "null", "None", ""):
        return ""
    val = str(texto).strip()
    match = re.match(r'^([A-Z0-9]+)[\s.-]', val)
    codigo = match.group(1) if match else sanitizar_pisis(val)
    return codigo[:max_len] if max_len else codigo


def extraer_multiples_codigos(texto, max_len_total=None):
    if not texto or str(texto).strip() in ("nan", "null", "None", ""):
        return ""
    elementos = str(texto).split(',')
    codigos = [extraer_codigo(e.strip()) for e in elementos if e.strip()]
    res = ",".join(filter(None, codigos))
    return res[:max_len_total] if max_len_total else res


def get_val(row, aliases):
    """Busca un valor en el registro iterando sobre variaciones de nombres de columna (2024, 2025, 2026)."""
    for k, v in row.items():
        if str(v).strip() in ("", "nan", "None", "null"):
            continue
        k_lower = str(k).lower()
        for alias in aliases:
            # Coincidencia exacta o que contenga el alias
            if k_lower == alias.lower() or k_lower.startswith(f"{alias.lower()}_") or f"_{alias.lower()}_" in k_lower:
                return v
    return ""


def transformar_registro_vivienda(row):
    """Transformación Anexo Técnico PISIS - Tipo 2 (Vivienda/Familia) - 125 Campos"""
    p = {f"c{i}": "" for i in range(125)}

    # -------------------------------------------------------------------------
    # LLAVES MAESTRAS DE RELACIÓN EPICOLLECT -> PISIS
    # Se usa el UUID nativo de Epicollect para garantizar que no se pierdan datos.
    # -------------------------------------------------------------------------
    id_familia = sanitizar_pisis(get_val(row, ['ec5_uuid']), 31)
    id_hogar = sanitizar_pisis(get_val(row, ['10_codigo_hogar', '10_1_codigo_hogar', '10_numero_de_identif']), 26)

    # Fallbacks de seguridad si el hogar viene vacío
    if not id_hogar: id_hogar = id_familia[:26]

    if not id_familia:
        return p  # Registro huérfano irrecuperable

    p["c0"] = "2"
    p["c1"] = sanitizar_pisis(get_val(row, ['consecutivo', '1_consecutivo', 'id']), 10)
    p["c2"] = extraer_codigo(get_val(row, ['1_consentimiento', 'consentimiento']), 1)
    p["c3"] = extraer_codigo(get_val(row, ['2_departamento', 'departamento']), 2)
    p["c4"] = extraer_codigo(get_val(row, ['3_unidad_zonal', 'subregion']), 3)
    p["c5"] = extraer_codigo(get_val(row, ['3_municipio', 'municipio']), 5)
    p["c6"] = extraer_codigo(get_val(row, ['4_territorio', 'territorio']), 3)
    p["c7"] = extraer_codigo(get_val(row, ['5_microterritorio', 'microterritorio']), 4)
    p["c8"] = extraer_codigo(get_val(row, ['8_tipo_de_ubicacion', 'tipo_ubicacion']), 1)
    p["c9"] = sanitizar_pisis(get_val(row, ['9_nombre_tipo', 'nombre_ubicacion', 'ubicacion_del_hoga']), 200)
    p["c10"] = extraer_codigo(get_val(row, ['10_area_de_ubicacion', 'area_ubicacion', 'area']), 1)
    p["c11"] = sanitizar_pisis(get_val(row, ['11_punto_de_referenc', '9_ubicacion_del_hoga', 'punto_referencia']), 200)
    p["c12"] = sanitizar_pisis(get_val(row, ['12_geopunto_longitud', '8_geo_punto_georrefe_lon']), 10)
    p["c13"] = sanitizar_pisis(get_val(row, ['13_geopunto_latitud', '8_geo_punto_georrefe_lat']), 10)
    p["c14"] = sanitizar_pisis(get_val(row, ['14_direccion', '7_direccion', 'direccion']), 200)
    p["c15"] = sanitizar_pisis(get_val(row, ['15_telefono', 'telefono']), 10)
    p["c16"] = extraer_codigo(get_val(row, ['12_estrato', 'estrato']), 1)
    p["c17"] = sanitizar_pisis(get_val(row, ['14_numero_de_familia', '13_numero_de_hogares', 'familias_vivienda']), 2)
    p["c18"] = sanitizar_pisis(get_val(row, ['15_numero_de_persona', 'personas_vivienda']), 3)
    p["c19"] = sanitizar_pisis(get_val(row, ['19_no_habitaciones', '28_de_cuantos_cuartos', 'habitaciones']), 2)
    p["c20"] = sanitizar_pisis(get_val(row, ['20_no_personas_por_h', 'personas_habitacion']), 3)
    p["c21"] = extraer_codigo(get_val(row, ['29_hacinamiento', '21_hacinamiento', 'hacinamiento']), 1)
    p["c22"] = sanitizar_pisis(get_val(row, ['22_elementos_para_do', 'elementos_dormir']), 2)
    p["c23"] = extraer_codigo(get_val(row, ['23_tipo_de_situacion', 'tipo_situacion']), 5)
    p["c24"] = sanitizar_pisis(get_val(row, ['24_observaciones_sit', 'obs_situacion', '44_observaciones']), 200)
    p["c25"] = extraer_codigo(get_val(row, ['16_numero_de_identif', 'numero_de_identificacion_del_e', 'ebs']), 10)
    p["c26"] = sanitizar_pisis(get_val(row, ['17_prestador_primari', 'nit_prestador']), 9)
    p["c27"] = extraer_codigo(get_val(row, ['18_tipo_de_identific', 'tipo_identificacion_res']), 2)
    p["c28"] = sanitizar_pisis(get_val(row, ['19_numero_de_identif', 'numero_identificacion_res']), 20)
    p["c29"] = sanitizar_pisis(get_val(row, ['21_perfil_de_quien', '20_responsable_de_la', 'perfil_res']), 200)
    p["c30"] = sanitizar_pisis(get_val(row, ['23_fecha_diligenciam', 'fecha_diligenciamiento']), 10)
    p["c31"] = extraer_codigo(get_val(row, ['24_tipo_de_la_vivien', 'tipo_vivienda']), 2)
    p["c32"] = extraer_multiples_codigos(
        get_val(row, ['30_se_identifican_al', '32_escenarios_de_rie', 'escenarios_riesgo']), 20)
    p["c33"] = extraer_multiples_codigos(
        get_val(row, ['34_observe_si_cerca', '33_cerca_de_la_vivienda', 'cerca_vivienda']), 56)
    p["c34"] = extraer_multiples_codigos(get_val(row, ['34_ambientes_luz_nat', 'luz_natural']), 11)
    p["c35"] = extraer_multiples_codigos(get_val(row, ['35_ambientes_ventila', 'ventilacion']), 11)
    p["c36"] = extraer_multiples_codigos(get_val(row, ['36_elementos_viviend', 'elementos_vivienda']), 5)
    p["c37"] = extraer_codigo(get_val(row, ['37_alumbrado_predomi', 'alumbrado']), 1)
    p["c38"] = extraer_codigo(get_val(row, ['31_desde_la_vivienda', 'acceso_vivienda']), 1)
    p["c39"] = sanitizar_pisis(get_val(row, ['39_otros_accesos', 'otros_accesos']), 200)
    p["c40"] = extraer_codigo(get_val(row, ['27_cual_es_el_materi', '25_cual_es_el_materi_pared', 'material_techo']), 2)
    p["c41"] = extraer_codigo(get_val(row, ['41_cocina_separada', 'cocina_separada']), 1)
    p["c42"] = extraer_codigo(get_val(row, ['42_bano_separado', 'bano_separado']), 1)
    p["c43"] = extraer_codigo(get_val(row, ['43_dormitorios_separ', 'dormitorios_separados']), 1)
    p["c44"] = extraer_multiples_codigos(get_val(row, ['44_medio_transporte', 'transporte_habitual']), 20)
    p["c45"] = sanitizar_pisis(get_val(row, ['45_otros_medios_tran', 'otros_transportes']), 200)
    p["c46"] = extraer_multiples_codigos(get_val(row, ['46_seguridad_desplaz', 'seguridad_desplazamiento']), 13)
    p["c47"] = sanitizar_pisis(get_val(row, ['47_otros_elementos_s', 'otros_elementos_seguridad']), 200)
    p["c48"] = extraer_multiples_codigos(get_val(row, ['48_desplazamiento_ma', 'tiempo_desplazamiento']), 11)
    p["c49"] = sanitizar_pisis(get_val(row, ['49_otros_factores_ti', 'otros_factores_tiempo']), 200)
    p["c50"] = extraer_codigo(get_val(row, ['35_al_interior_de_la', 'actividad_economica', '50_se_realiza_activi']), 1)
    p["c51"] = extraer_codigo(get_val(row, ['51_area_trabajo_inde', 'area_independiente']), 1)
    p["c52"] = extraer_codigo(get_val(row, ['52_familiar_afectado', 'familiar_afectado']), 1)
    p["c53"] = extraer_multiples_codigos(get_val(row, ['37_cual_es_la_princi', '53_fuente_principal_']), 32)
    p["c54"] = extraer_codigo(get_val(row, ['54_horas_suministro', 'horas_suministro_agua']), 1)
    p["c55"] = extraer_codigo(get_val(row, ['55_tanque_almacenami', 'tanque_agua']), 1)
    p["c56"] = extraer_codigo(get_val(row, ['56_frecuencia_limpie', 'frecuencia_limpieza']), 1)
    p["c57"] = extraer_codigo(get_val(row, ['57_distancia_tanque', 'distancia_tanque_pozo']), 1)
    p["c58"] = extraer_multiples_codigos(get_val(row, ['38_cual_es_el_sistem', 'disposicion_excretas']), 13)
    p["c59"] = extraer_multiples_codigos(get_val(row, ['39_cual_es_el_sistem', 'disposicion_aguas_residuales']), 11)
    p["c60"] = extraer_multiples_codigos(get_val(row, ['60_almacenamiento_re', 'almacenamiento_residuos']), 9)
    p["c61"] = sanitizar_pisis(get_val(row, ['61_otros_sistemas_al', 'otros_sistemas_residuos']), 200)
    p["c62"] = extraer_multiples_codigos(get_val(row, ['40_como_se_realiza_l', 'disposicion_basura']), 9)
    p["c63"] = extraer_codigo(get_val(row, ['63_conoce_practicas', 'conoce_practicas_residuos']), 1)
    p["c64"] = extraer_codigo(get_val(row, ['64_realiza_practicas', 'realiza_practicas_reduccion']), 1)
    p["c65"] = extraer_multiples_codigos(get_val(row, ['65_como_reduce_gener', 'como_reduce_residuos']), 11)
    p["c66"] = sanitizar_pisis(get_val(row, ['66_otras_practicas_r', 'otras_practicas_reduccion']), 200)
    p["c67"] = extraer_codigo(get_val(row, ['67_realiza_practicas', 'realiza_aprovechamiento']), 1)
    p["c68"] = sanitizar_pisis(get_val(row, ['68_que_otras_practic', 'otras_practicas_aprovechamiento']), 200)
    p["c69"] = extraer_multiples_codigos(get_val(row, ['69_como_realiza_disp', 'disposicion_peligrosos']), 17)
    p["c70"] = sanitizar_pisis(get_val(row, ['70_otras_practicas_d', 'otras_practicas_peligrosos']), 200)
    p["c71"] = extraer_codigo(get_val(row, ['71_realiza_procesos', 'procesos_residuos_rurales']), 1)
    p["c72"] = extraer_multiples_codigos(get_val(row, ['72_que_practicas_apr', 'practicas_aprovechamiento_rurales']), 9)
    p["c73"] = sanitizar_pisis(get_val(row, ['73_otras_practicas_a', 'otras_practicas_rurales']), 200)
    p["c74"] = extraer_multiples_codigos(get_val(row, ['74_que_practicas_sep', 'practicas_separacion_rurales']), 7)
    p["c75"] = sanitizar_pisis(get_val(row, ['75_otras_practicas_s', 'otras_separacion_rurales']), 200)
    p["c76"] = extraer_codigo(get_val(row, ['76_limpieza_superfic', 'limpieza_superficies']), 1)
    p["c77"] = sanitizar_pisis(get_val(row, ['77_otras_practicas_l', 'otras_limpieza_superficies']), 200)
    p["c78"] = extraer_multiples_codigos(get_val(row, ['32_cual_fuente_de_en', '78_fuente_de_energia']), 15)
    p["c79"] = sanitizar_pisis(get_val(row, ['79_otras_fuentes_ene', 'otras_fuentes_energia']), 200)
    p["c80"] = extraer_multiples_codigos(get_val(row, ['80_fuentes_frecuente', 'fuentes_humo']), 13)
    p["c81"] = sanitizar_pisis(get_val(row, ['81_otras_fuentes_fre', 'otras_fuentes_humo']), 200)
    p["c82"] = extraer_multiples_codigos(get_val(row, ['82_practicas_calidad', 'practicas_calidad_aire']), 9)
    p["c83"] = extraer_multiples_codigos(get_val(row, ['83_tipo_estufa', 'tipo_estufa']), 7)
    p["c84"] = extraer_codigo(get_val(row, ['33_se_observa_cerca_', '84_criaderos_que_fav', 'criaderos_vectores']), 1)
    p["c85"] = extraer_multiples_codigos(get_val(row, ['85_vectores_transmis', 'vectores_enfermedades']), 23)
    p["c86"] = sanitizar_pisis(get_val(row, ['86_otros_vectores_tr', 'otros_vectores']), 200)
    p["c87"] = extraer_multiples_codigos(get_val(row, ['87_medidas_control_v', 'medidas_control_vectores']), 32)
    p["c88"] = sanitizar_pisis(get_val(row, ['88_otras_medidas_con', 'otras_medidas_vectores']), 200)
    p["c89"] = extraer_multiples_codigos(get_val(row, ['89_animales_ponzonos', 'animales_ponzonosos']), 13)
    p["c90"] = sanitizar_pisis(get_val(row, ['90_otros_animales_po', 'otros_animales_ponzonosos']), 200)
    p["c91"] = extraer_multiples_codigos(get_val(row, ['91_medidas_reducir_r', 'medidas_reducir_riesgo_animales']), 20)
    p["c92"] = extraer_multiples_codigos(
        get_val(row, ['36_senale_los_animal', '92_animales_que_conv', 'animales_conviven']), 26)
    p["c93"] = sanitizar_pisis(get_val(row, ['93_cantidad_de_perro', 'cantidad_perros']), 3)
    p["c94"] = sanitizar_pisis(get_val(row, ['94_cantidad_de_perro', 'perros_vacunados']), 3)
    p["c95"] = sanitizar_pisis(get_val(row, ['95_cantidad_de_gatos', 'cantidad_gatos']), 3)
    p["c96"] = sanitizar_pisis(get_val(row, ['96_cantidad_de_gatos', 'gatos_vacunados']), 3)
    p["c97"] = extraer_multiples_codigos(get_val(row, ['97_finalidad_de_tene', 'finalidad_animales']), 7)
    p["c98"] = extraer_multiples_codigos(get_val(row, ['98_confinamiento_de_', 'confinamiento_animales']), 5)
    p["c99"] = extraer_codigo(get_val(row, ['99_se_desparasita_a_', 'desparasita_animales']), 1)
    p["c100"] = extraer_codigo(get_val(row, ['100_instalaciones_se', 'instalaciones_seguras']), 1)
    p["c101"] = extraer_codigo(get_val(row, ['101_excretas_de_los_', 'excretas_recogidas']), 1)
    p["c102"] = extraer_codigo(get_val(row, ['102_vivienda_con_bar', 'barreras_contacto_animales']), 1)
    p["c103"] = extraer_codigo(get_val(row, ['103_medidas_para_el_', 'medidas_vectores']), 1)
    p["c104"] = extraer_codigo(get_val(row, ['104_lugar_donde_adqu', 'lugar_adquiere_quimicos']), 1)
    p["c105"] = extraer_multiples_codigos(get_val(row, ['105_disposicion_fina', 'disposicion_quimicos']), 15)
    p["c106"] = sanitizar_pisis(get_val(row, ['106_otras_practicas_', 'otras_disposicion_quimicos']), 200)
    p["c107"] = extraer_codigo(get_val(row, ['107_seguimiento_de_i', 'seguimiento_instrucciones_quimicos']), 1)
    p["c108"] = extraer_codigo(get_val(row, ['108_productos_en_env', 'productos_envase_original']), 1)
    p["c109"] = extraer_codigo(get_val(row, ['109_proteccion_y_ven', 'proteccion_ventilacion']), 1)
    p["c110"] = sanitizar_pisis(get_val(row, ['42_numero_de_persona', '110_no_personas']), 2)
    p["c111"] = sanitizar_pisis(get_val(row, ['111_alias_familia', 'alias_familia']), 200)
    p["c112"] = extraer_codigo(get_val(row, ['41_tipo_de_familia', '112_tipo_de_familia', 'tipo_familia']), 1)
    p["c113"] = extraer_codigo(get_val(row, ['45_funcionalidad_de', '113_apgar_familiar', 'apgar_familiar', 'apgar']),
                               1)
    p["c114"] = extraer_codigo(
        get_val(row, ['46_en_la_familia_se', '114_cuidador_princip', 'cuidador_principal', 'cuidador']), 1)
    p["c115"] = extraer_codigo(get_val(row, ['47_si_la_respuesta_a', '115_escala_zarit', 'escala_zarit', 'zarit']), 3)
    p["c116"] = extraer_multiples_codigos(get_val(row, ['116_familia_con_situ', 'riesgos_familia']), 50)
    p["c117"] = extraer_multiples_codigos(get_val(row, ['117_practicas_que_fa', 'practicas_vinculos']), 11)
    p["c118"] = extraer_codigo(get_val(row, ['118_redes_de_apoyo_s', 'redes_apoyo']), 1)
    p["c119"] = extraer_multiples_codigos(get_val(row, ['119_practicas_para_e', 'practicas_cuidado_hogar']), 15)
    p["c120"] = extraer_multiples_codigos(get_val(row, ['120_medidas_ante_enf', 'medidas_enfermedades_respiratorias']),
                                          1)
    p["c121"] = sanitizar_pisis(get_val(row, ['121_otras_medidas_an', 'otras_medidas_respiratorias']), 200)
    p["c122"] = extraer_codigo(get_val(row, ['122_implementos_de_h', 'higiene_compartida']), 1)

    p["c123"] = id_hogar
    p["c124"] = id_familia

    return p


def transformar_registro_integrante(row):
    """Transformación Anexo Técnico PISIS - Tipo 3 (Integrante) - 119 Campos"""
    p = {f"c{i}": "" for i in range(119)}

    # -------------------------------------------------------------------------
    # LLAVES MAESTRAS DE RELACIÓN EPICOLLECT -> PISIS
    # Se extrae el ID del Padre desde la columna nativa generada por Epicollect.
    # -------------------------------------------------------------------------
    id_familia = sanitizar_pisis(get_val(row, ['ec5_branch_owner_uuid', 'caracterizacion_uuid']), 31)

    tipo_id = extraer_codigo(get_val(row, ['5_tipo_de_identifica', 'tipo_identificacion']), 2)
    num_id = sanitizar_pisis(get_val(row, ['6_numero_de_identifi', 'numero_identificacion']), 20)

    # Si falta la relación con la tabla padre, se omite (regla estricta base de datos)
    if not id_familia:
        return p

    p["c0"] = "3"
    p["c1"] = sanitizar_pisis(get_val(row, ['consecutivo', '1_consecutivo', 'id']), 10)
    p["c2"] = sanitizar_pisis(get_val(row, ['1_primer_nombre', 'primer_nombre']), 60)
    p["c3"] = sanitizar_pisis(get_val(row, ['2_segundo_nombre', 'segundo_nombre']), 60)
    p["c4"] = sanitizar_pisis(get_val(row, ['3_primer_apellido', 'primer_apellido']), 60)
    p["c5"] = sanitizar_pisis(get_val(row, ['4_segundo_apellido', 'segundo_apellido']), 60)
    p["c6"] = tipo_id
    p["c7"] = num_id
    p["c8"] = sanitizar_pisis(get_val(row, ['7_fecha_de_nacimient', 'fecha_nacimiento']), 10)
    p["c9"] = extraer_codigo(get_val(row, ['9_pais_de_origen', 'pais_origen']), 3)
    p["c10"] = extraer_codigo(get_val(row, ['10_estatus_migratori', 'estatus_migratorio']), 1)
    p["c11"] = extraer_codigo(get_val(row, ['8_sexo', '11_sexo_al_nacer', 'sexo_nacer']), 1)
    p["c12"] = extraer_codigo(get_val(row, ['12_genero', 'genero']), 1)
    p["c13"] = extraer_codigo(get_val(row, ['13_genero_que_se_ide', 'identidad_genero']), 1)
    p["c14"] = extraer_codigo(get_val(row, ['14_cual_es_la_orient', 'orientacion_sexual']), 1)
    p["c15"] = sanitizar_pisis(
        get_val(row, ['numero_celular', '15_telefono_principa', 'telefono_principal', 'telefono']), 20)
    p["c16"] = sanitizar_pisis(get_val(row, ['16_telefono_secundar', 'telefono_secundario']), 20)
    p["c17"] = extraer_codigo(get_val(row, ['10_rol_dentro_de_la', '17_rol_dentro_de_la_', 'rol_familia']), 1)
    p["c18"] = extraer_codigo(get_val(row, ['11_ocupacion', '18_ocupacion', 'ocupacion']), 4)
    p["c19"] = extraer_codigo(get_val(row, ['12_nivel_educativo', '19_nivel_educativo', 'nivel_educativo']), 2)
    p["c20"] = extraer_codigo(get_val(row, ['13_regimen_de_afilia', '20_regimen_de_afilia', 'regimen_afiliacion']), 1)
    p["c21"] = extraer_codigo(get_val(row, ['14_eapb', '21_eapb', 'eapb']), 8)
    p["c22"] = extraer_multiples_codigos(
        get_val(row, ['15_pertenencia_a_un', '22_es_sujeto_de_prot', 'condicion_especial']), 32)
    p["c23"] = extraer_multiples_codigos(get_val(row, ['23_modalidad_violenc', 'modalidad_violencia']), 200)
    p["c24"] = extraer_codigo(get_val(row, ['16_pertenencia_etnic', '24_pertenencia_etnic', 'pertenencia_etnica']), 2)
    p["c25"] = sanitizar_pisis(
        get_val(row, ['25_pueblo_comunidad', '18_comunidad_o_puebl', '25_a_que_pueblo_o_co', 'pueblo_indigena']), 60)
    p["c26"] = extraer_multiples_codigos(get_val(row, ['26_practicas_de_cuid', 'saberes_ancestrales']), 11)
    p["c27"] = extraer_multiples_codigos(get_val(row, ['27_practicas_para_el', 'exigibilidad_derecho']), 7)
    p["c28"] = extraer_multiples_codigos(get_val(row, ['28_realiza_rutinari', 'practicas_cuidado']), 15)
    p["c29"] = extraer_multiples_codigos(get_val(row, ['29_atenciones_pendie', 'atenciones_pendientes']), 81)
    p["c30"] = extraer_multiples_codigos(get_val(row, ['19_reconoce_alguna_d', '30_es_persona_con_di', 'discapacidad']),
                                         13)
    p["c31"] = extraer_codigo(get_val(row, ['31_tiene_certificaci', 'certificado_discapacidad']), 1)
    p["c32"] = extraer_codigo(get_val(row, ['32_intencion_reprodu', 'intencion_reproductiva']), 1)
    p["c33"] = extraer_codigo(get_val(row, ['9_se_encuentra_en_pe', '33_gestacion_actual_', 'gestacion_confirmada']), 1)
    p["c34"] = extraer_multiples_codigos(get_val(row, ['34_atenciones_pendie', 'atenciones_materno']), 15)
    p["c35"] = extraer_multiples_codigos(get_val(row, ['35_motivos_por_el_l', 'motivo_no_atencion']), 32)
    p["c36"] = extraer_codigo(get_val(row, ['29_si_es_menor_de_6', '36_menores_de_6_mese', 'lactancia_exclusiva']), 1)
    p["c37"] = sanitizar_pisis(get_val(row, ['20_peso_en_kilogramo', '37_peso_en_kilogramo', 'peso']), 5)
    p["c38"] = sanitizar_pisis(get_val(row, ['21_talla_en_centimet', '38_talla_en_centimet', 'talla']), 5)
    p["c39"] = sanitizar_pisis(get_val(row, ['39_mayores_de_5_anos', 'imc']), 4)
    p["c40"] = sanitizar_pisis(get_val(row, ['40_mayores_de_18_ano', 'cintura']), 3)
    p["c41"] = extraer_multiples_codigos(
        get_val(row, ['31_se_identifican_si', '41_hay_signos_fisico', 'signos_desnutricion']), 13)
    p["c42"] = extraer_codigo(
        get_val(row, ['22_diagnostico_nutri', '42_clasificacion_ant', 'clasificacion_antropometrica']), 2)
    p["c43"] = extraer_codigo(get_val(row, ['43_se_lava_las_manos', 'lavado_manos', 'se_lava_las_manos']), 1)
    p["c44"] = sanitizar_pisis(get_val(row, ['44_tension_arterial_', 'tension_sistolica']), 3)
    p["c45"] = sanitizar_pisis(get_val(row, ['45_tension_arterial_', 'tension_diastolica']), 3)
    p["c46"] = extraer_codigo(get_val(row, ['46_clasificacion_ten', 'clasificacion_tension']), 1)
    p["c47"] = extraer_multiples_codigos(get_val(row, ['47_alguien_de_la_fam', 'urgencias_accidentes']), 20)
    p["c48"] = extraer_multiples_codigos(
        get_val(row, ['32_actualmente_prese', '48_enfermedades_sufr', 'enfermedad_ultimo_mes']), 47)
    p["c49"] = sanitizar_pisis(get_val(row, ['32_1_cuales', '49_otras_enfermedade', 'otras_enfermedades']), 200)
    p["c50"] = extraer_codigo(get_val(row, ['50_que_hizo_si_la_pe', 'accion_enfermedad']), 1)
    p["c51"] = sanitizar_pisis(get_val(row, ['51_otras_enfermedade', 'otras_acciones']), 200)
    p["c52"] = extraer_multiples_codigos(get_val(row, ['52_mayores_de_14_ano', 'trastornos_animo']), 5)
    p["c53"] = extraer_codigo(get_val(row, ['53_para_mayores_de_1', 'estado_animo']), 1)
    p["c54"] = extraer_multiples_codigos(get_val(row, ['54_identifica_riesgo', 'riesgos_salud_mental']), 50)
    p["c55"] = extraer_codigo(get_val(row, ['55_situacion_de_salu', 'limite_actividades']), 1)
    p["c56"] = extraer_codigo(get_val(row, ['56_tiene_diagnostico', 'tiene_diagnostico']), 1)
    p["c57"] = extraer_codigo(get_val(row, ['57_tiene_signos_y_si', 'sintomas_sin_diagnostico']), 1)
    p["c58"] = extraer_multiples_codigos(get_val(row, ['58_presenta_alguna_c', 'condicion_transmisible']), 32)
    p["c59"] = extraer_multiples_codigos(get_val(row, ['59_tiene_alguna_enfe', 'enfermedad_no_transmisible']), 35)
    p["c60"] = extraer_codigo(get_val(row, ['60_vive_en_zona_ende', 'zona_endemica']), 1)
    p["c61"] = extraer_codigo(get_val(row, ['33_esta_recibiendo_a', '61_recibe_atencion_y', 'atencion_actual']), 1)
    p["c62"] = extraer_multiples_codigos(
        get_val(row, ['34_si_la_respuesta_a', '62_motivos_por_el_l', 'motivo_no_atencion_enfermedad']), 32)
    p["c63"] = extraer_codigo(get_val(row, ['63_mayores_de_14_ano', 'consume_spa']), 1)
    p["c64"] = extraer_codigo(get_val(row, ['64_consume_tabaco', 'consume_tabaco']), 1)
    p["c65"] = sanitizar_pisis(get_val(row, ['65_consumo_maximo_de', 'cigarrillos_diarios']), 2)
    p["c66"] = sanitizar_pisis(get_val(row, ['66_anos_fumando', 'anos_fumando']), 2)
    p["c67"] = sanitizar_pisis(get_val(row, ['67_puntaje_riesgo_as', 'puntaje_assist']), 2)
    p["c68"] = sanitizar_pisis(get_val(row, ['68_puntaje_riesgo_au', 'puntaje_audit']), 2)
    p["c69"] = sanitizar_pisis(get_val(row, ['69_puntaje_riesgo_ca', 'puntaje_crafft']), 2)
    p["c70"] = sanitizar_pisis(get_val(row, ['70_fecha_de_la_ultim', 'fum']), 10)
    p["c71"] = extraer_codigo(get_val(row, ['71_mujer_en_edad_fer', 'mujer_edad_fertil']), 1)
    p["c72"] = extraer_codigo(get_val(row, ['72_se_encuentra_en_e', 'embarazo_actual']), 1)
    p["c73"] = extraer_codigo(get_val(row, ['73_conoce_los_signos', 'conoce_signos_alarma']), 1)
    p["c74"] = extraer_codigo(get_val(row, ['74_conoce_sobre_inte', 'conoce_ive']), 1)
    p["c75"] = extraer_codigo(get_val(row, ['75_inicio_atenciones', 'inicio_controles']), 1)
    p["c76"] = extraer_codigo(get_val(row, ['76_inicio_oportuname', 'inicio_oportuno']), 1)
    p["c77"] = extraer_codigo(get_val(row, ['77_tiene_acceso_a_me', 'acceso_metodos']), 1)
    p["c78"] = extraer_codigo(get_val(row, ['78_clasificacion_del', 'riesgo_gestacional']), 1)
    p["c79"] = extraer_codigo(get_val(row, ['79_clasificacion_del', 'riesgo_preeclampsia']), 1)
    p["c80"] = sanitizar_pisis(get_val(row, ['80_numero_de_atencio', 'numero_atenciones']), 2)
    p["c81"] = extraer_codigo(get_val(row, ['81_atencion_para_el_', 'cuidado_preconcepcional']), 1)
    p["c82"] = extraer_codigo(get_val(row, ['82_atencion_para_el_', 'cuidado_prenatal']), 1)
    p["c83"] = sanitizar_pisis(get_val(row, ['83_preparacion_para_', 'sesiones_maternidad']), 2)
    p["c84"] = sanitizar_pisis(get_val(row, ['84_fecha_de_atencion', 'fecha_evento']), 10)
    p["c85"] = extraer_codigo(get_val(row, ['85_atencion_del_puer', 'atencion_puerperio']), 1)
    p["c86"] = extraer_codigo(get_val(row, ['86_consulta_de_segui', 'seguimiento_puerperio']), 1)
    p["c87"] = extraer_codigo(get_val(row, ['87_apoyo_a_la_lactan', 'apoyo_lactancia']), 1)
    p["c88"] = extraer_codigo(get_val(row, ['88_atencion_durante_', 'atencion_24h_rn']), 1)
    p["c89"] = extraer_codigo(get_val(row, ['89_control_entre_3_y', 'control_3a5_rn']), 1)
    p["c90"] = extraer_codigo(get_val(row, ['90_vacunacion_del_re', 'vacunacion_rn']), 1)
    p["c91"] = extraer_codigo(get_val(row, ['91_provision_del_met', 'metodo_postparto']), 2)
    p["c92"] = extraer_codigo(get_val(row, ['92_cuenta_con_histor', 'historial_laboral']), 1)
    p["c93"] = sanitizar_pisis(get_val(row, ['93_lugar_de_trabajo_', 'lugar_trabajo']), 200)
    p["c94"] = sanitizar_pisis(get_val(row, ['94_nombre_del_emplea', 'nombre_empleador']), 200)
    p["c95"] = sanitizar_pisis(get_val(row, ['95_periodo_laboral_m', 'periodo_laboral']), 2)
    p["c96"] = extraer_codigo(get_val(row, ['96_cuenta_con_mas_em', 'mas_empleos']), 1)
    p["c97"] = sanitizar_pisis(get_val(row, ['97_lugar_de_trabajo_', 'lugar_trabajo_2']), 200)
    p["c98"] = sanitizar_pisis(get_val(row, ['98_nombre_del_emplea', 'nombre_empleador_2']), 200)
    p["c99"] = sanitizar_pisis(get_val(row, ['99_periodo_laboral_m', 'periodo_laboral_2']), 2)
    p["c100"] = sanitizar_pisis(get_val(row, ['100_lugar_de_trabajo', 'lugar_trabajo_3']), 200)
    p["c101"] = sanitizar_pisis(get_val(row, ['101_nombre_del_emple', 'nombre_empleador_3']), 200)
    p["c102"] = sanitizar_pisis(get_val(row, ['102_periodo_laboral_', 'periodo_laboral_3']), 2)
    p["c103"] = extraer_codigo(get_val(row, ['103_en_alguno_de_los', 'actividad_asbesto']), 1)
    p["c104"] = extraer_codigo(get_val(row, ['104_en_alguno_de_los', 'actividad_relacionada_asbesto']), 1)
    p["c105"] = extraer_multiples_codigos(get_val(row, ['105_cuales_son_las_a', 'cuales_actividades_asbesto']), 135)
    p["c106"] = extraer_codigo(get_val(row, ['106_ha_interactuado_', 'interactuado_materiales']), 1)
    p["c107"] = extraer_multiples_codigos(get_val(row, ['107_cuales_son_los_m', 'cuales_materiales']), 5)
    p["c108"] = extraer_codigo(get_val(row, ['108_en_que_modalidad', 'modalidad_empleo']), 1)
    p["c109"] = extraer_codigo(get_val(row, ['109_en_su_hogar_ha_', 'hogar_materiales_asbesto']), 1)
    p["c110"] = extraer_multiples_codigos(get_val(row, ['110_cuales_son_los_e', 'elementos_hogar_asbesto']), 20)
    p["c111"] = extraer_codigo(get_val(row, ['111_en_que_estado_se', 'estado_materiales']), 1)
    p["c112"] = extraer_codigo(get_val(row, ['112_en_su_hogar_conv', 'convive_trabajador_asbesto']), 1)
    p["c113"] = extraer_codigo(get_val(row, ['113_ha_realizado_en_', 'reparaciones_asbesto']), 1)
    p["c114"] = extraer_codigo(get_val(row, ['114_recuerda_alguna_', 'actividad_cerca_hogar']), 1)
    p["c115"] = extraer_multiples_codigos(get_val(row, ['115_cuales_son_las_a', 'cuales_actividades_cerca']), 1)
    p["c116"] = extraer_codigo(get_val(row, ['116_ha_tenido_famili', 'familiares_enfermedades_asbesto']), 1)

    p["c117"] = id_familia

    # ID Único Integrante según la normativa: c117 + c6 + c7.
    # Fallback seguro: Si faltara tipo o número ID, usamos el UUID hijo para no perder el dato.
    if tipo_id and num_id:
        p["c118"] = sanitizar_pisis(f"{id_familia}{tipo_id}{num_id}", 53)
    else:
        # En caso de error de digitador en terreno (ID vacío), usamos la rama hija
        p["c118"] = sanitizar_pisis(get_val(row, ['ec5_branch_uuid']), 53)

    return p