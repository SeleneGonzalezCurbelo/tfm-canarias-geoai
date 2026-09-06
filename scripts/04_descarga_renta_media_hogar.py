# -*- coding: utf-8 -*-
"""
Script 04: Descarga de Renta Media del Hogar e Indicadores de Pobreza (INE ADRH)
- Descarga de datos de renta neta media por persona y por hogar desde el servicio ArcGIS del INE.
- Indicadores adicionales: porcentaje de ingresos bajos, riesgo de pobreza, índice de Gini y estructura de edad.
- Procesamiento y exportación para la identificación de zonas vulnerables en el archipiélago.
"""

import os
import warnings
import requests
import geopandas as gpd
import pandas as pd

warnings.filterwarnings("ignore")

OUTPUT_DIR = "./renta_hogar"
os.makedirs(OUTPUT_DIR, exist_ok=True)

URL = (
    "https://www.ine.es/servergis/rest/services/"
    "Hosted/ADRH_2023_Renta_media_por_hogar/FeatureServer/3/query"
)

print("Descargando datos de renta media del hogar e indicadores socioeconómicos (INE)...")

params = {
    "where": "cpro IN ('35','38')",
    "outFields": "*",
    "f": "geojson"
}
r = requests.get(URL, params=params)
r.raise_for_status()
print(f"  Datos descargados: {len(r.content)} bytes")

gdf = gpd.read_file(r.text)
print(f"  Registros obtenidos: {len(gdf)}")

if len(gdf) == 0:
    raise SystemExit("AVISO: Sin datos de renta para Canarias.")

# Mapeo de campos del servicio INE a nombres normalizados para el TFM
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

print(f"  Columnas procesadas: {[c for c in gdf.columns if c != 'geometry']}")

# Proyección a UTM 28N para Canarias y cálculo de coordenadas de centroide
gdf_proj = gdf.to_crs("EPSG:32628")
gdf["lon"] = gdf_proj.geometry.centroid.x
gdf["lat"] = gdf_proj.geometry.centroid.y

gpkg_path = f"{OUTPUT_DIR}/renta_media_hogar_canarias.gpkg"
gdf.to_file(gpkg_path, driver="GPKG")
print(f"  GeoPackage exportado: {gpkg_path}")

csv_path = f"{OUTPUT_DIR}/renta_media_hogar_canarias.csv"
gdf.drop(columns="geometry").to_csv(csv_path, index=False)
print(f"  CSV exportado: {csv_path}")

print("\nResumen descriptivo de renta y desigualdad:")
num_cols = ["renta_neta_media_persona", "renta_neta_media_hogar", "indice_gini"]
num_cols = [c for c in num_cols if c in gdf.columns]
print(gdf[num_cols].describe())

print("\n" + "=" * 50)
print("SCRIPT 04 FINALIZADO CORRECTAMENTE")
print("=" * 50)
