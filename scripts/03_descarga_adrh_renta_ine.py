# -*- coding: utf-8 -*-
"""
Script 03: Descarga de Indicadores de Renta y Desigualdad (ADRH INE)
- Descarga capas del Atlas de Distribución de Renta de los Hogares (ADRH) del INE.
- Capas analizadas: Porcentaje de salario sobre renta bruta, Índice de Gini, 
  Porcentaje de pensiones sobre renta bruta y Distribución de renta P80/P20.
- Exportación unificada en data/processed/adrh/ y reporte en data/reports/.
"""

import os
import time
import json
import warnings
from pathlib import Path
import requests
import geopandas as gpd

warnings.filterwarnings("ignore")

OUTPUT_DIR = Path("data/processed/adrh")
REPORTS_DIR = Path("data/reports")
for d in [OUTPUT_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

BASE_URL = (
    "https://www.ine.es/servergis/rest/services/"
    "Hosted/{layer}/FeatureServer/3/query"
)

LAYERS = {
    "salario_renta": "ADRH_2023_Porcentaje_salario_sobre_renta_bruta",
    "indice_gini": "ADRH_2023_Indice_de_Gini",
    "pensiones_renta": "ADRH_2023_Porcentaje_pensiones_sobre_renta_bruta",
    "p80p20": "ADRH_2023_Distribucion_renta_P80P20"
}

t_start = time.time()
stats = {"script": "03_descarga_adrh_renta_ine", "layers": {}}

print("[INFO] Iniciando descarga de indicadores ADRH (INE) para Canarias...")

for nombre, layer in LAYERS.items():
    print(f"\n[INFO] Descargando capa: {nombre} ({layer})...")
    url = BASE_URL.format(layer=layer)
    params = {
        "where": "cpro IN ('35','38')",
        "outFields": "*",
        "f": "geojson"
    }
    r = requests.get(url, params=params)
    r.raise_for_status()

    geojson_path = OUTPUT_DIR / f"{nombre}.geojson"
    with open(geojson_path, "wb") as f:
        f.write(r.content)

    gdf = gpd.read_file(geojson_path)
    print(f"  [OK] Registros obtenidos: {len(gdf)}")

    if len(gdf) == 0:
        print("  [WARN] Sin datos para Canarias en esta capa.")
        continue

    gdf_proj = gdf.to_crs("EPSG:32628")
    gdf["lon"] = gdf_proj.geometry.centroid.x
    gdf["lat"] = gdf_proj.geometry.centroid.y

    gpkg_path = OUTPUT_DIR / f"{nombre}_canarias.gpkg"
    gdf.to_file(gpkg_path, driver="GPKG")

    csv_path = OUTPUT_DIR / f"{nombre}_canarias.csv"
    gdf.drop(columns="geometry").to_csv(csv_path, index=False)
    print(f"  [OK] Exportado GeoPackage y CSV para {nombre}")

    stats["layers"][nombre] = {
        "records": len(gdf),
        "gpkg": str(gpkg_path),
        "csv": str(csv_path)
    }

stats["total_duration_sec"] = round(time.time() - t_start, 2)
meta_path = REPORTS_DIR / "03_metadata.json"
with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(stats, f, indent=4, ensure_ascii=False)

print("\n" + "=" * 60)
print("RESUMEN DE VALIDACIÓN - SCRIPT 03")
print("=" * 60)
for layer_name, info in stats["layers"].items():
    print(f"• Capa {layer_name}: {info['records']:,} registros")
print(f"• Tiempo total de ejecución: {stats['total_duration_sec']}s")
print("=" * 60)
print("SCRIPT 03 FINALIZADO CORRECTAMENTE")
print("=" * 60)
