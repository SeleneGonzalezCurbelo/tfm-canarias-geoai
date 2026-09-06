# -*- coding: utf-8 -*-
"""
Script 02: Descarga de Indicadores del Censo 2021 (INE)
- Descarga indicadores socioeconómicos a nivel de sección censal para Canarias (provincias 35 y 38).
- Variables de empleo (actividad, paro, ocupación), educación (estudios superiores) y vivienda (superficie, antigüedad, régimen).
- Almacenamiento en CSV para su posterior integración en el modelo analítico del TFM.
"""

import requests
import pandas as pd
import warnings
import time

warnings.filterwarnings('ignore')

URL_API = 'https://www.ine.es/Censo2021/api'

# Definición de consultas al Censo 2021 (Tabla, Métrica, Columna Destino, Descripción)
# Nota: Métricas como desempleo, inactividad, ocupación, superficie y antigüedad de vivienda
# no están disponibles a nivel de sección censal (ID_RESIDENCIA_N5) en la API del INE y han sido omitidas.
QUERIES = [
    # === Empleo ===
    ('per.ppal', 'PCT_SACTIVOS',   'pct_activos',      'Porcentaje población activa'),
    # === Educación ===
    ('per.ppal', 'PCT_SESTSUP',       'pct_estudios_superiores', 'Porcentaje con estudios superiores'),
    ('per.ppal', 'MEDIA_SNIVEL_ESTU', 'nivel_estudios_medio',    'Nivel medio de estudios'),
    # === Vivienda ===
    ('viv.fam', 'SVIVIENDAS',         'total_viviendas',              'Número total de viviendas'),
    # === Hogares ===
    ('hog', 'SHOGARES',          'total_hogares',       'Número total de hogares'),
    ('hog', 'STAM_HOG',          'tamano_medio_hogar',  'Tamaño medio del hogar'),
]

PROVINCIAS_CANARIAS = ('35 ', '38 ')  # Las Palmas y Santa Cruz de Tenerife

def query_metric(table, metric, max_retries=3):
    """Consulta una métrica específica a través de la API del Censo 2021 del INE."""
    body = {
        'idioma': 'ES',
        'metrica': [metric],
        'tabla': table,
        'variables': ['ID_RESIDENCIA_N2', 'ID_RESIDENCIA_N5']
    }
    for attempt in range(max_retries):
        try:
            r = requests.post(URL_API, json=body, timeout=300)
            if r.status_code == 200:
                return r.json().get('data', [])
            else:
                print(f'  HTTP {r.status_code}, reintentando {attempt+1}/{max_retries}...')
                time.sleep(5)
        except Exception as e:
            print(f'  Error: {e}, reintentando {attempt+1}/{max_retries}...')
            time.sleep(10)
    return []

def parse_section_id(section_str):
    """Extrae el código CUSEC normalizado desde el identificador de sección."""
    if section_str and section_str.startswith('Secci'):
        return section_str.split()[-1]
    return section_str

print("Iniciando descarga de indicadores del Censo 2021 (INE)...")
all_data = {}

for table, metric, col_name, desc in QUERIES:
    print(f'Descargando {desc} ({metric})...')
    rows = query_metric(table, metric)
    if not rows:
        print(f'  Aviso: No se obtuvieron datos para {metric}')
        continue

    # Filtrar exclusivamente para las provincias de Canarias
    can_rows = [d for d in rows if str(d.get('ID_RESIDENCIA_N2', '')).startswith(PROVINCIAS_CANARIAS)]
    print(f'  Registros totales España: {len(rows)} | Canarias: {len(can_rows)}')

    for d in can_rows:
        cusec = parse_section_id(d.get('ID_RESIDENCIA_N5', ''))
        if cusec not in all_data:
            all_data[cusec] = {'cusec': cusec}
        val = d.get(metric) or d.get(f'MEDIA_{metric}')
        all_data[cusec][col_name] = val

    time.sleep(1)

# Conversión a DataFrame de Pandas
df = pd.DataFrame.from_records(list(all_data.values())).set_index('cusec')
print(f'\nTotal secciones censales de Canarias procesadas: {len(df)}')
print(f'Variables recopiladas: {list(df.columns)}')

# Guardar resultados
output_path = 'data/censo2021_canarias.csv'
import os
os.makedirs('data', exist_ok=True)
df.to_csv(output_path)
print(f'Datos del Censo 2021 guardados exitosamente en {output_path}')
print("=" * 50)
print("SCRIPT 02 FINALIZADO CORRECTAMENTE")
print("=" * 50)
