# -*- coding: utf-8 -*-
"""
Script 06: Cálculo de Superficie (Área) por Sección Censal e Integración de Indicadores del Censo 2021
- Cálculo preciso del área geográfica de cada sección censal en kilómetros cuadrados (proyección UTM 28N).
- Integración de los indicadores socioeconómicos del Censo 2021 (actividad, educación, vivienda y hogares).
- Exportación consolidada en formatos GeoPackage y CSV para el modelo analítico del TFM.
"""

import os
import warnings
from pathlib import Path
import geopandas as gpd
import pandas as pd

warnings.filterwarnings("ignore")

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "data" / "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Buscar geometría de secciones
GEO_PATH = Path("poblacion_canarias/poblacion_canarias.gpkg")
if not GEO_PATH.exists():
    GEO_PATH = Path("data/geo/secciones_canarias.gpkg")

if not GEO_PATH.exists():
    raise FileNotFoundError(
        f"No se encuentra la geometría de secciones en {GEO_PATH}. "
        "Ejecute primero los scripts 01 y 05."
    )

print("Cargando geometría de secciones censales de Canarias...")
gdf = gpd.read_file(GEO_PATH)
print(f"  Secciones cargadas: {len(gdf)}")

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

print(f"  Área total Canarias: {gdf['area_km2'].sum():.0f} km²")
print(f"  Área media por sección: {gdf['area_km2'].mean():.2f} km²")

# Cargar datos del Censo 2021 (Script 02)
CENSO_PATH = Path("data/censo2021_canarias.csv")
if CENSO_PATH.exists():
    print("Cargando indicadores del Censo 2021...")
    df_censo = pd.read_csv(CENSO_PATH, dtype={"cusec": str})
    df_censo["cusec"] = df_censo["cusec"].str.zfill(10)
    print(f"  Registros del Censo 2021 cargados: {len(df_censo)}")
    
    # Fusionar área con indicadores del Censo 2021
    cols_to_merge = [c for c in df_censo.columns if c != "cusec"]
    gdf_merge = gdf.merge(df_censo[["cusec"] + cols_to_merge], on="cusec", how="left")
else:
    print("  Aviso: No se encontró data/censo2021_canarias.csv. Ejecute el script 02 primero.")
    gdf_merge = gdf

print(f"  Secciones totales procesadas: {len(gdf_merge)}")

# Exportar resultados en GeoPackage y CSV
gpkg_path = str(OUTPUT_DIR / "secciones_area_censo2021.gpkg")
gdf_merge.to_file(gpkg_path, layer="secciones", driver="GPKG")
print(f"  GeoPackage exportado: {gpkg_path}")

csv_path = str(OUTPUT_DIR / "secciones_area_censo2021.csv")
gdf_merge.drop(columns="geometry", errors="ignore").to_csv(csv_path, index=False, encoding="utf-8")
print(f"  CSV exportado: {csv_path}")

print("\n" + "=" * 50)
print("SCRIPT 06 FINALIZADO CORRECTAMENTE")
print("=" * 50)
