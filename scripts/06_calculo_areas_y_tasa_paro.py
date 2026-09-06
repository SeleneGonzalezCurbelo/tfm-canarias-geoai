# -*- coding: utf-8 -*-
"""
Script 06: Cálculo de Superficie (Área) por Sección Censal y Descarga de Tasa de Paro (Censo 2021 INE)
- Cálculo preciso del área geográfica de cada sección censal en kilómetros cuadrados (proyección UTM 28N).
- Consulta a la API del Censo 2021 del INE para obtener la tasa de desempleo (PCT_SPARADOS).
- Integración y consolidación de área y tasa de paro en los datasets espaciales y tabulares del TFM.
"""

import os
import warnings
import requests
import geopandas as gpd
import pandas as pd

warnings.filterwarnings("ignore")

OUTPUT_DIR = "./data/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Ruta local de la geometría de secciones censales de Canarias
SECCIONES_PATH = "data/geo/secciones_canarias.gpkg"

if not os.path.exists(SECCIONES_PATH):
    raise FileNotFoundError(
        f"No se encuentra el fichero {SECCIONES_PATH}. "
        "Ejecute primero el script 01 para generar la geometría base."
    )

print("Cargando geometría de secciones censales de Canarias...")
gdf = gpd.read_file(SECCIONES_PATH)
print(f"  Secciones cargadas: {len(gdf)}")
print(f"  CRS original: {gdf.crs}")

# Calcular área en km² usando proyección UTM 28N (adecuada para Canarias)
gdf_proj = gdf.to_crs("EPSG:32628")
gdf["area_km2"] = gdf_proj.geometry.area / 1e6

print(f"  Área total Canarias: {gdf['area_km2'].sum():.0f} km²")
print(f"  Área media por sección: {gdf['area_km2'].mean():.2f} km²")

# Descargar tasa de paro (PCT_SPARADOS) del Censo 2021 vía API del INE
print("Descargando tasa de desempleo (Censo 2021 INE) a nivel de sección censal...")
url = "https://www.ine.es/Censo2021/api"
body = {
    "idioma": "ES",
    "metrica": ["PCT_SPARADOS"],
    "tabla": "per.ppal",
    "variables": ["ID_RESIDENCIA_N2", "ID_RESIDENCIA_N5"]
}

resp = requests.post(url, json=body, timeout=600)
resp.raise_for_status()

rows = resp.json().get("data", [])
print(f"  Registros totales obtenidos: {len(rows)}")

# Filtrar para Canarias (provincias 35 y 38)
canarias = [
    d for d in rows
    if str(d.get("ID_RESIDENCIA_N2", "")).startswith(("35 ", "38 "))
]
print(f"  Registros filtrados para Canarias: {len(canarias)}")

# Convertir a DataFrame y extraer código CUSEC normalizado
df_paro = pd.DataFrame(canarias)
df_paro["CUSEC"] = df_paro["ID_RESIDENCIA_N5"].str.extract(r"(\d+)", expand=False)
df_paro = df_paro.rename(columns={"PCT_SPARADOS": "tasa_paro"})
df_paro["tasa_paro"] = df_paro["tasa_paro"].astype(float)

print(f"  Tasa de paro media estimada en Canarias: {df_paro['tasa_paro'].mean():.2f}%")

# Fusionar área y tasa de paro con la geometría de secciones
gdf_merge = gdf.merge(df_paro[["CUSEC", "tasa_paro"]], on="CUSEC", how="left")
print(f"  Secciones con tasa de paro asignada: {gdf_merge['tasa_paro'].notna().sum()}")
print(f"  Secciones sin dato de paro: {gdf_merge['tasa_paro'].isna().sum()}")

# Exportar resultados en GeoPackage y CSV
gpkg_path = os.path.join(OUTPUT_DIR, "secciones_area_paro.gpkg")
gdf_merge.to_file(gpkg_path, layer="secciones", driver="GPKG")
print(f"  GeoPackage exportado: {gpkg_path}")

csv_path = os.path.join(OUTPUT_DIR, "secciones_area_paro.csv")
gdf_merge.drop(columns="geometry").to_csv(csv_path, index=False, encoding="utf-8")
print(f"  CSV exportado: {csv_path}")

print("\n" + "=" * 50)
print("SCRIPT 06 FINALIZADO CORRECTAMENTE")
print("=" * 50)
