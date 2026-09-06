# -*- coding: utf-8 -*-
"""
Script 05: Descarga de Población, Densidad y Demografía (INE)
- Descarga de datos de población total, porcentaje de extranjeros, población nacida en el extranjero,
  índice de envejecimiento y tasa de dependencia a nivel de sección censal desde el servicio ArcGIS del INE.
- Cálculo de superficie territorial y densidad de población por sección censal.
- Exportación en formato GeoPackage y CSV.
"""

import os
import warnings
import requests
import geopandas as gpd
import pandas as pd

warnings.filterwarnings("ignore")

OUTPUT_DIR = "./poblacion_canarias"
os.makedirs(OUTPUT_DIR, exist_ok=True)

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

print("Descargando datos de población y demografía para Canarias (INE)...")
resp = requests.get(url, params=params, timeout=300)
resp.raise_for_status()

gdf = gpd.read_file(resp.text)
print(f"  Registros descargados: {len(gdf)}")

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
print(f"  Columnas seleccionadas: {list(gdf.columns)}")

# Cálculo de densidad de población utilizando proyección UTM 28N (Canarias)
gdf_proj = gdf.to_crs("EPSG:32628")
gdf_proj["area_km2"] = gdf_proj.geometry.area / 1e6
gdf_proj["densidad_hab_km2"] = gdf_proj["poblacion_total"] / gdf_proj["area_km2"]
gdf["densidad_hab_km2"] = gdf_proj["densidad_hab_km2"]

gdf["centroid_lon"] = gdf_proj.geometry.centroid.x
gdf["centroid_lat"] = gdf_proj.geometry.centroid.y

gpkg_path = os.path.join(OUTPUT_DIR, "poblacion_canarias.gpkg")
gdf.to_file(gpkg_path, layer="poblacion", driver="GPKG")
print(f"  GeoPackage exportado: {gpkg_path}")

csv_path = os.path.join(OUTPUT_DIR, "poblacion_canarias.csv")
gdf.drop(columns="geometry").to_csv(csv_path, index=False, encoding="utf-8")
print(f"  CSV exportado: {csv_path}")

print("\nResumen demográfico:")
print(f"  Provincias: {sorted(gdf['cpro'].unique())}")
print(f"  Municipios analizados: {gdf['nmun'].nunique()}")
print(f"  Secciones censales: {len(gdf)}")
print(f"  Población total Canarias: {gdf['poblacion_total'].sum():,.0f}")
print(f"  Densidad media: {gdf['densidad_hab_km2'].mean():.1f} hab/km²")

print("\n" + "=" * 50)
print("SCRIPT 05 FINALIZADO CORRECTAMENTE")
print("=" * 50)
