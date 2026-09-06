# -*- coding: utf-8 -*-
"""
Script 05: Descarga de Población, Densidad y Demografía (INE)
- Descarga de datos de población total, porcentaje de extranjeros, población nacida en el extranjero,
  índice de envejecimiento y tasa de dependencia a nivel de sección censal desde el servicio ArcGIS del INE.
- Cálculo de superficie territorial y densidad de población por sección censal.
- Exportación unificada en data/processed/poblacion/ y reporte en data/reports/.
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
OUTPUT_DIR = ROOT_DIR / "data" / "processed" / "poblacion"
REPORTS_DIR = ROOT_DIR / "data" / "reports"
for d in [OUTPUT_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

url = (
    "https://www.ine.es/servergis/rest/services/Hosted/"
    "Censo_2025___N%C3%BAmero_de_personas/FeatureServer/2/query"
)

params = {
    "where": "cpro IN ('35','38')",
    "outFields": "*",
    "f": "geojson",
    "returnGeometry": "true",
    "outSR": "4326",
}

t_start = time.time()
stats: Dict[str, Any] = {"script": "05_poblacion_demografia"}


def main() -> None:
    try:
        print("[INFO] Descargando datos de población y demografía para Canarias (INE)...")
        resp = requests.get(url, params=params, timeout=300)
        resp.raise_for_status()

        gdf = gpd.read_file(resp.text)
        print(f"  [OK] Registros descargados: {len(gdf):,}")

        if len(gdf) == 0:
            raise ValueError("Sin datos de población para Canarias.")

        cusec_col = next((c for c in gdf.columns if c.lower() in ["cusec", "id_residencia_n5", "seccion"]), "cusec")
        if cusec_col in gdf.columns:
            gdf["cusec"] = gdf[cusec_col].astype(str).str.zfill(10)

        column_map = {
            "cusec": "cusec",
            "n_personas": "poblacion_total",
            "porc_ext": "pct_extranjeros",
            "porc_nac_ext": "pct_nacidos_extranjero",
            "ind_envejecimiento": "indice_envejecimiento",
            "tasa_dependencia": "tasa_dependencia",
            "cpro": "cpro",
            "npro": "npro",
            "nca": "nca",
            "nmun": "nmun",
        }

        keep = [c for c in column_map if c in gdf.columns] + ['geometry']
        gdf = gdf[keep].rename(columns={k: v for k, v in column_map.items() if k in keep})
        print(f"  [INFO] Columnas seleccionadas: {list(gdf.columns)}")

        # Cálculo de densidad de población utilizando proyección UTM 28N (Canarias)
        gdf_proj = gdf.to_crs("EPSG:32628")
        gdf_proj["area_km2"] = gdf_proj.geometry.area / 1e6
        gdf_proj["densidad_hab_km2"] = gdf_proj["poblacion_total"] / gdf_proj["area_km2"]
        gdf["densidad_hab_km2"] = gdf_proj["densidad_hab_km2"]

        gdf["centroid_lon"] = gdf_proj.geometry.centroid.x
        gdf["centroid_lat"] = gdf_proj.geometry.centroid.y

        gpkg_path = OUTPUT_DIR / "poblacion_canarias.gpkg"
        gdf.to_file(gpkg_path, layer="poblacion", driver="GPKG")
        print(f"  [OK] GeoPackage exportado: {gpkg_path}")

        csv_path = OUTPUT_DIR / "poblacion_canarias.csv"
        gdf.drop(columns="geometry").to_csv(csv_path, index=False, encoding="utf-8")
        print(f"  [OK] CSV exportado: {csv_path}")

        print("\nResumen demográfico:")
        if 'cpro' in gdf.columns:
            print(f"  Provincias: {sorted(gdf['cpro'].unique())}")
        if 'nmun' in gdf.columns:
            print(f"  Municipios analizados: {gdf['nmun'].nunique()}")
        print(f"  Secciones censales: {len(gdf):,}")
        print(f"  Población total Canarias: {gdf['poblacion_total'].sum():,.0f}")
        print(f"  Densidad media: {gdf['densidad_hab_km2'].mean():.1f} hab/km²")

        stats["total_duration_sec"] = round(time.time() - t_start, 2)
        stats["secciones_count"] = len(gdf)
        stats["poblacion_total"] = float(gdf["poblacion_total"].sum())
        stats["densidad_media"] = float(gdf["densidad_hab_km2"].mean())
        stats["gpkg_path"] = str(gpkg_path)
        stats["csv_path"] = str(csv_path)

        meta_path = REPORTS_DIR / "05_metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=4, ensure_ascii=False)

        print("\n" + "=" * 60)
        print("RESUMEN DE VALIDACIÓN - SCRIPT 05")
        print("=" * 60)
        print(f"• Secciones con datos demográficos: {len(gdf):,}")
        print(f"• Población total: {stats['poblacion_total']:,.0f}")
        print(f"• Ficheros generados en {OUTPUT_DIR}")
        print(f"• Tiempo total de ejecución: {stats['total_duration_sec']}s")
        print("=" * 60)
        print("SCRIPT 05 FINALIZADO CORRECTAMENTE")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] El script 05 ha fallado: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
