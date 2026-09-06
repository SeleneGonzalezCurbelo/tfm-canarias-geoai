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
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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

ROOT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT_DIR / "data" / "processed" / "censo"
REPORTS_DIR = ROOT_DIR / "data" / "reports"
for d in [PROCESSED_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

t_start = time.time()
stats: Dict[str, Any] = {"script": "02_descarga_censo_2021_ine"}


def query_metric(table: str, metric: str, max_retries: int = 3) -> List[Dict[str, Any]]:
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


def parse_section_id(section_str: Optional[str]) -> Optional[str]:
    """Extrae el código CUSEC normalizado desde el identificador de sección."""
    if section_str and str(section_str).startswith('Secci'):
        parts = str(section_str).split()
        if parts:
            return parts[-1]
    return str(section_str) if section_str else None


def main() -> None:
    try:
        print("[INFO] Iniciando descarga de indicadores del Censo 2021 (INE)...")
        dfs = []

        for table, metric, col_name, desc in QUERIES:
            print(f'[INFO] Descargando {desc} ({metric})...')
            rows = query_metric(table, metric)
            if not rows:
                print(f'  [WARN] No se obtuvieron datos para {metric}')
                continue

            df_raw = pd.DataFrame(rows)
            n2_col = 'ID_RESIDENCIA_N2'
            if n2_col in df_raw.columns:
                mask = df_raw[n2_col].astype(str).str.startswith(PROVINCIAS_CANARIAS)
                df_can = df_raw.loc[mask].copy()
            else:
                df_can = pd.DataFrame()

            print(f'  [OK] Registros totales España: {len(df_raw)} | Canarias: {len(df_can)}')

            if df_can.empty:
                continue

            n5_col = 'ID_RESIDENCIA_N5'
            val_col = metric if metric in df_can.columns else f'MEDIA_{metric}'
            if val_col not in df_can.columns and len(df_can.columns) > 2:
                val_col = [c for c in df_can.columns if c not in [n2_col, n5_col]][0]

            df_can['cusec'] = df_can[n5_col].apply(parse_section_id)
            df_can['cusec'] = df_can['cusec'].astype(str).str.zfill(10)
            
            df_metric = df_can[['cusec', val_col]].rename(columns={val_col: col_name})
            df_metric = df_metric.groupby('cusec', as_index=False).first()
            dfs.append(df_metric)

            time.sleep(1)

        if not dfs:
            raise ValueError("No se pudieron descargar indicadores del censo para Canarias.")

        df_final = dfs[0]
        for d in dfs[1:]:
            df_final = df_final.merge(d, on='cusec', how='outer', validate='one_to_one')

        df_final = df_final.set_index('cusec')

        print(f'\n[OK] Total secciones censales de Canarias procesadas: {len(df_final)}')
        print(f'[INFO] Variables recopiladas: {list(df_final.columns)}')

        assert df_final.index.str.len().eq(10).all(), "Existen códigos CUSEC que no tienen 10 dígitos"
        assert not df_final.index.duplicated().any(), "Existen CUSEC duplicados en el índice"

        output_path = PROCESSED_DIR / "censo2021_canarias.csv"
        df_final.to_csv(output_path)
        print(f'[OK] Datos del Censo 2021 guardados exitosamente en {output_path}')

        stats["total_duration_sec"] = round(time.time() - t_start, 2)
        stats["secciones_count"] = len(df_final)
        stats["variables"] = list(df_final.columns)
        stats["nulls_summary"] = df_final.isna().sum().to_dict()
        stats["output_file"] = str(output_path)

        meta_path = REPORTS_DIR / "02_metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=4, ensure_ascii=False)

        print("\n" + "=" * 60)
        print("RESUMEN DE VALIDACIÓN - SCRIPT 02")
        print("=" * 60)
        print(f"• Secciones procesadas: {len(df_final):,}")
        print(f"• Fichero generado: {output_path} ({output_path.stat().st_size / 1024:.2f} KB)")
        print(f"• Tiempo total de ejecución: {stats['total_duration_sec']}s")
        print("=" * 60)
        print("SCRIPT 02 FINALIZADO CORRECTAMENTE")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] El script 02 ha fallado: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
