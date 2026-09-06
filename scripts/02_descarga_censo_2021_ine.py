# -*- coding: utf-8 -*-
"""
Script 02: Descarga de Indicadores del Censo 2021 (INE)
- Descarga indicadores socioeconómicos a nivel de sección censal para Canarias (provincias 35 y 38).
- Variables de empleo, educación y vivienda.
- Almacenamiento unificado en data/processed/censo/ y reporte en data/reports/.
"""

import os
import time
import json
import warnings
from pathlib import Path
import requests
import pandas as pd

warnings.filterwarnings('ignore')

URL_API = 'https://www.ine.es/Censo2021/api'

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

PROVINCIAS_CANARIAS = ('35 ', '38 ')

PROCESSED_DIR = Path("data/processed/censo")
REPORTS_DIR = Path("data/reports")
for d in [PROCESSED_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

t_start = time.time()
stats = {"script": "02_descarga_censo_2021_ine"}

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
                print(f'  [WARN] HTTP {r.status_code}, reintentando {attempt+1}/{max_retries}...')
                time.sleep(5)
        except Exception as e:
            print(f'  [WARN] Error: {e}, reintentando {attempt+1}/{max_retries}...')
            time.sleep(10)
    return []

def parse_section_id(section_str):
    """Extrae el código CUSEC normalizado desde el identificador de sección."""
    if section_str and section_str.startswith('Secci'):
        return section_str.split()[-1]
    return section_str

print("[INFO] Iniciando descarga de indicadores del Censo 2021 (INE)...")
all_data = {}

for table, metric, col_name, desc in QUERIES:
    print(f'[INFO] Descargando {desc} ({metric})...')
    rows = query_metric(table, metric)
    if not rows:
        print(f'  [WARN] No se obtuvieron datos para {metric}')
        continue

    can_rows = [d for d in rows if str(d.get('ID_RESIDENCIA_N2', '')).startswith(PROVINCIAS_CANARIAS)]
    print(f'  [OK] Registros totales España: {len(rows)} | Canarias: {len(can_rows)}')

    for d in can_rows:
        cusec = parse_section_id(d.get('ID_RESIDENCIA_N5', ''))
        if cusec not in all_data:
            all_data[cusec] = {'cusec': cusec}
        val = d.get(metric) or d.get(f'MEDIA_{metric}')
        all_data[cusec][col_name] = val

    time.sleep(1)

# Conversión a DataFrame de Pandas
df = pd.DataFrame.from_records(list(all_data.values())).set_index('cusec')
print(f'\n[OK] Total secciones censales de Canarias procesadas: {len(df)}')
print(f'[INFO] Variables recopiladas: {list(df.columns)}')

# Guardar resultados unificados
output_path = PROCESSED_DIR / "censo2021_canarias.csv"
df.to_csv(output_path)
print(f'[OK] Datos del Censo 2021 guardados exitosamente en {output_path}')

stats["total_duration_sec"] = round(time.time() - t_start, 2)
stats["secciones_count"] = len(df)
stats["variables"] = list(df.columns)
stats["nulls_summary"] = df.isna().sum().to_dict()
stats["output_file"] = str(output_path)

meta_path = REPORTS_DIR / "02_metadata.json"
with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(stats, f, indent=4, ensure_ascii=False)

print("\n" + "=" * 60)
print("RESUMEN DE VALIDACIÓN - SCRIPT 02")
print("=" * 60)
print(f"• Secciones procesadas: {len(df):,}")
print(f"• Fichero generado: {output_path} ({output_path.stat().st_size / 1024:.2f} KB)")
print(f"• Tiempo total de ejecución: {stats['total_duration_sec']}s")
print("=" * 60)
print("SCRIPT 02 FINALIZADO CORRECTAMENTE")
print("=" * 60)
