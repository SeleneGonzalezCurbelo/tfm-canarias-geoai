# -*- coding: utf-8 -*-
"""
Script 04: Descarga de Renta Media del Hogar e Indicadores de Pobreza (INE ADRH)
- Descarga de datos de renta neta media por persona y por hogar desde el servicio ArcGIS del INE.
- Indicadores adicionales: porcentaje de ingresos bajos, riesgo de pobreza, índice de Gini, etc.
- Exportación unificada en data/processed/renta/ y reporte en data/reports/.
"""

import os
import time
import json
import warnings
from pathlib import Path
import requests
import geopandas as gpd
import pandas as pd

warnings.filterwarnings("ignore")

OUTPUT_DIR = Path("data/processed/renta")
REPORTS_DIR = Path("data/reports")
for d in [OUTPUT_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

URL = (
    "https://www.ine.es/servergis/rest/services/"
    "Hosted/ADRH_2023_Renta_media_por_hogar/FeatureServer/3/query"
)

t_start = time.time()
stats = {"script": "04_descarga_renta_media_hogar"}

print("[INFO] Descargando datos de renta media del hogar e indicadores socioeconómicos (INE)...")

params = {
    "where": "cpro IN ('35','38')",
    "outFields": "*",
    "f": "geojson"
}
r = requests.get(URL, params=params)
r.raise_for_status()
print(f"  [OK] Datos descargados: {len(r.content):,} bytes")

gdf = gpd.read_file(r.text)
print(f"  [OK] Registros obtenidos: {len(gdf):,}")

if len(gdf) == 0:
    raise SystemExit("[ERROR] AVISO: Sin datos de renta para Canarias.")

RENAME_MAP = {
    "dato1": "renta_neta_media_persona",
    "dato2": "renta_neta_media_hogar",
    "dato3": "pct_ingresos_bajos_7500",
    "dato4": "pct_riesgo_pobreza_60",
    "dato5": "pct_ingresos_altos_200",
    "dato7": "pct_menor_18",
    "dato8": "pct_mayor_65",
    "dato9": "indice_gini"
}

KEEP_COLS = ["cusec", "cpro", "npro", "nca", "nmun"] + list(RENAME_MAP.keys())
available = [c for c in KEEP_COLS if c in gdf.columns]
gdf = gdf[available + ["geometry"]]
gdf = gdf.rename(columns=RENAME_MAP)

print(f"  [INFO] Columnas procesadas: {[c for c in gdf.columns if c != 'geometry']}")

gdf_proj = gdf.to_crs("EPSG:32628")
gdf["lon"] = gdf_proj.geometry.centroid.x
gdf["lat"] = gdf_proj.geometry.centroid.y

gpkg_path = OUTPUT_DIR / "renta_media_hogar_canarias.gpkg"
gdf.to_file(gpkg_path, driver="GPKG")
print(f"  [OK] GeoPackage exportado: {gpkg_path}")

csv_path = OUTPUT_DIR / "renta_media_hogar_canarias.csv"
gdf.drop(columns="geometry").to_csv(csv_path, index=False)
print(f"  [OK] CSV exportado: {csv_path}")

print("\nResumen descriptivo de renta y desigualdad:")
num_cols = ["renta_neta_media_persona", "renta_neta_media_hogar", "indice_gini"]
num_cols = [c for c in num_cols if c in gdf.columns]
print(gdf[num_cols].describe())

stats["total_duration_sec"] = round(time.time() - t_start, 2)
stats["secciones_count"] = len(gdf)
stats["nulls_summary"] = gdf.drop(columns="geometry").isna().sum().to_dict()
stats["gpkg_path"] = str(gpkg_path)
stats["csv_path"] = str(csv_path)

meta_path = REPORTS_DIR / "04_metadata.json"
with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(stats, f, indent=4, ensure_ascii=False)

print("\n" + "=" * 60)
print("RESUMEN DE VALIDACIÓN - SCRIPT 04")
print("=" * 60)
print(f"• Secciones con datos de renta: {len(gdf):,}")
print(f"• Ficheros generados: GPKG y CSV en {OUTPUT_DIR}")
print(f"• Tiempo total de ejecución: {stats['total_duration_sec']}s")
print("=" * 60)
print("SCRIPT 04 FINALIZADO CORRECTAMENTE")
print("=" * 60)
