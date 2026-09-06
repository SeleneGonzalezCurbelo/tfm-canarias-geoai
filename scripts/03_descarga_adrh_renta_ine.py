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
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import geopandas as gpd
import pandas as pd

warnings.filterwarnings("ignore")

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "data" / "processed" / "adrh"
REPORTS_DIR = ROOT_DIR / "data" / "reports"
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
stats: Dict[str, Any] = {"script": "03_descarga_adrh_renta_ine", "layers": {}}


def main() -> None:
    try:
        print("[INFO] Iniciando descarga de indicadores ADRH (INE) para Canarias...")

        for nombre, layer in LAYERS.items():
            print(f"\n[INFO] Descargando capa: {nombre} ({layer})...")
            url = BASE_URL.format(layer=layer)
            params = {
                "where": "cpro IN ('35','38')",
                "outFields": "*",
                "f": "geojson"
            }
            r = requests.get(url, params=params, timeout=120)
            r.raise_for_status()

            geojson_path = OUTPUT_DIR / f"{nombre}.geojson"
            with open(geojson_path, "wb") as f:
                f.write(r.content)

            gdf = gpd.read_file(geojson_path)
            print(f"  [OK] Registros obtenidos: {len(gdf):,}")

            if len(gdf) == 0:
                print("  [WARN] Sin datos para Canarias en esta capa.")
                continue

            cusec_col = next((c for c in gdf.columns if c.lower() in ["cusec", "id_residencia_n5", "seccion"]), None)
            if cusec_col:
                gdf["cusec"] = gdf[cusec_col].astype(str).str.zfill(10)

            gdf_proj = gdf.to_crs("EPSG:32628")
            gdf["lon"] = gdf_proj.geometry.centroid.x
            gdf["lat"] = gdf_proj.geometry.centroid.y

            gpkg_path = OUTPUT_DIR / f"{nombre}_canarias.gpkg"
            gdf.to_file(gpkg_path, driver="GPKG")

            csv_path = OUTPUT_DIR / f"{nombre}_canarias.csv"
            gdf.drop(columns="geometry", errors="ignore").to_csv(csv_path, index=False, encoding="utf-8")
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

    except Exception as e:
        print(f"\n[ERROR] El script 03 ha fallado: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
