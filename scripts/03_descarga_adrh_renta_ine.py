# -*- coding: utf-8 -*-
"""
Script 03: Descarga de Indicadores de Renta y Desigualdad (ADRH INE)
- Descarga capas del Atlas de Distribución de Renta de los Hogares (ADRH) del INE.
- Capas analizadas: Porcentaje de salario sobre renta bruta, Índice de Gini, 
  Porcentaje de pensiones sobre renta bruta y Distribución de renta P80/P20.
- Exportación en formatos GeoPackage y CSV para análisis geoespacial y estadístico.
"""

import os
import warnings
import requests
import geopandas as gpd

warnings.filterwarnings("ignore")

OUTPUT_DIR = "./adrh_canarias"
os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE_URL = (
    "https://www.ine.es/servergis/rest/services/"
    "Hosted/{layer}/FeatureServer/3/query"
)

# Capas del Atlas de Distribución de Renta de los Hogares (ADRH)
LAYERS = {
    "salario_renta": "ADRH_2023_Porcentaje_salario_sobre_renta_bruta",
    "indice_gini": "ADRH_2023_Indice_de_Gini",
    "pensiones_renta": "ADRH_2023_Porcentaje_pensiones_sobre_renta_bruta",
    "p80p20": "ADRH_2023_Distribucion_renta_P80P20"
}

print("Iniciando descarga de indicadores ADRH (INE) para Canarias...")

for nombre, layer in LAYERS.items():
    print(f"\nDescargando capa: {nombre} ({layer})...")

    url = BASE_URL.format(layer=layer)
    params = {
        "where": "cpro IN ('35','38')", # Provincias de Las Palmas y S/C de Tenerife
        "outFields": "*",
        "f": "geojson"
    }
    r = requests.get(url, params=params)
    r.raise_for_status()

    geojson_path = f"{OUTPUT_DIR}/{nombre}.geojson"
    with open(geojson_path, "wb") as f:
        f.write(r.content)

    gdf = gpd.read_file(geojson_path)
    print(f"  Registros obtenidos: {len(gdf)}")

    if len(gdf) == 0:
        print("  Aviso: Sin datos para Canarias en esta capa.")
        continue

    # Proyección UTM zona 28N para Canarias y cálculo de centroides
    gdf_proj = gdf.to_crs("EPSG:32628")
    gdf["lon"] = gdf_proj.geometry.centroid.x
    gdf["lat"] = gdf_proj.geometry.centroid.y

    gpkg_path = f"{OUTPUT_DIR}/{nombre}_canarias.gpkg"
    gdf.to_file(gpkg_path, driver="GPKG")

    csv_path = f"{OUTPUT_DIR}/{nombre}_canarias.csv"
    gdf.drop(columns="geometry").to_csv(csv_path, index=False)
    print(f"  OK Exportado GeoPackage y CSV para {nombre}")

print("\n" + "=" * 50)
print("SCRIPT 03 FINALIZADO CORRECTAMENTE")
print("=" * 50)
