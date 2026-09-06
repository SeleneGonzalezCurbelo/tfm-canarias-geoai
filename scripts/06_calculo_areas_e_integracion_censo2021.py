# -*- coding: utf-8 -*-
"""
Script 06: Cálculo de Superficie (Área) por Sección Censal e Integración de Indicadores del Censo 2021
- Cálculo preciso del área geográfica de cada sección censal en kilómetros cuadrados (proyección UTM 28N).
- Integración de los indicadores socioeconómicos del Censo 2021 desde data/processed/censo/.
- Exportación consolidada unificada en data/outputs/ y reporte en data/reports/.
"""

import os
import time
import json
import warnings
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import geopandas as gpd
import pandas as pd

warnings.filterwarnings("ignore")

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "data" / "outputs"
REPORTS_DIR = ROOT_DIR / "data" / "reports"
for d in [OUTPUT_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

t_start = time.time()
stats: Dict[str, Any] = {"script": "06_calculo_areas_e_integracion_censo2021"}


def main() -> None:
    try:
        # Buscar geometría de secciones
        GEO_PATH = ROOT_DIR / "data" / "processed" / "poblacion" / "poblacion_canarias.gpkg"
        if not GEO_PATH.exists():
            GEO_PATH = ROOT_DIR / "data" / "geo" / "secciones_canarias.gpkg"

        if not GEO_PATH.exists():
            raise FileNotFoundError(
                f"No se encuentra la geometría de secciones en {GEO_PATH}. "
                "Ejecute primero los scripts 01 y 05."
            )

        print("[INFO] Cargando geometría de secciones censales de Canarias...")
        gdf = gpd.read_file(GEO_PATH)
        print(f"  [OK] Secciones cargadas: {len(gdf):,}")

        # Normalizar columna CUSEC / cusec
        cusec_col = next((c for c in gdf.columns if c.lower() == "cusec"), None)
        if cusec_col:
            gdf = gdf.rename(columns={cusec_col: "cusec"})
            gdf["cusec"] = gdf["cusec"].astype(str).str.zfill(10)
        else:
            raise KeyError("No se encontró la columna 'cusec' o 'CUSEC' en la geometría de secciones.")

        # Calcular área en km² usando proyección UTM 28N (adecuada para Canarias)
        gdf_proj = gdf.to_crs("EPSG:32628")
        gdf["area_km2"] = gdf_proj.geometry.area / 1e6

        print(f"  [OK] Área total Canarias: {gdf['area_km2'].sum():,.0f} km²")
        print(f"  [OK] Área media por sección: {gdf['area_km2'].mean():.2f} km²")

        # Cargar datos del Censo 2021 (Script 02 unificado)
        CENSO_PATH = ROOT_DIR / "data" / "processed" / "censo" / "censo2021_canarias.csv"
        if not CENSO_PATH.exists():
            CENSO_PATH = ROOT_DIR / "data" / "censo2021_canarias.csv"  # fallback

        if CENSO_PATH.exists():
            print("[INFO] Cargando indicadores del Censo 2021 desde ruta unificada...")
            df_censo = pd.read_csv(CENSO_PATH, dtype={"cusec": str})
            df_censo["cusec"] = df_censo["cusec"].str.zfill(10)
            print(f"  [OK] Registros del Censo 2021 cargados: {len(df_censo):,}")

            cols_to_merge = [c for c in df_censo.columns if c != "cusec"]
            gdf_merge = gdf.merge(
                df_censo[["cusec"] + cols_to_merge],
                on="cusec",
                how="left",
                validate="one_to_one"
            )
        else:
            print("  [WARN] No se encontró el fichero del Censo 2021. Ejecute el script 02 primero.")
            gdf_merge = gdf

        print(f"  [OK] Secciones totales consolidadas: {len(gdf_merge):,}")

        # Exportar resultados en GeoPackage y CSV en data/outputs/
        gpkg_path = OUTPUT_DIR / "secciones_area_censo2021.gpkg"
        gdf_merge.to_file(gpkg_path, layer="secciones", driver="GPKG")
        print(f"  [OK] GeoPackage exportado: {gpkg_path}")

        csv_path = OUTPUT_DIR / "secciones_area_censo2021.csv"
        gdf_merge.drop(columns="geometry", errors="ignore").to_csv(csv_path, index=False, encoding="utf-8")
        print(f"  [OK] CSV exportado: {csv_path}")

        stats["total_duration_sec"] = round(time.time() - t_start, 2)
        stats["secciones_count"] = len(gdf_merge)
        stats["total_area_km2"] = float(gdf["area_km2"].sum())
        stats["nulls_summary"] = gdf_merge.drop(columns="geometry", errors="ignore").isna().sum().to_dict()
        stats["gpkg_path"] = str(gpkg_path)
        stats["csv_path"] = str(csv_path)

        meta_path = REPORTS_DIR / "06_metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=4, ensure_ascii=False)

        print("\n" + "=" * 60)
        print("RESUMEN DE VALIDACIÓN - SCRIPT 06")
        print("=" * 60)
        print(f"• Secciones consolidadas: {len(gdf_merge):,}")
        print(f"• Área total cubierta: {stats['total_area_km2']:,.0f} km²")
        print(f"• Ficheros maestros generados en {OUTPUT_DIR}")
        print(f"• Tiempo total de ejecución: {stats['total_duration_sec']}s")
        print("=" * 60)
        print("SCRIPT 06 FINALIZADO CORRECTAMENTE")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] El script 06 ha fallado: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
