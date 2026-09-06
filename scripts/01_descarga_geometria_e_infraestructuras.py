# -*- coding: utf-8 -*-
"""
Script 01: Descarga de Geometría de Secciones Censales e Infraestructuras (POIs)
- Descarga y filtrado de secciones censales de Canarias (provincias 35 y 38) desde INE.
- Extracción de puntos de interés (hospitales, centros de salud, farmacias, colegios, paradas de autobús)
  isla por isla utilizando OSMnx (OpenStreetMap).
- Cálculo de distancias mínimas y disponibilidad de servicios por sección censal.
- Generación de dataset geespacial base (GPKG y CSV).
"""

import os
import time
import zipfile
import shutil
import warnings
from pathlib import Path
import pandas as pd
import geopandas as gpd

warnings.filterwarnings("ignore")

# Configuración de OSMnx para análisis espacial y red de transporte/servicios
try:
    import osmnx as ox
except ImportError:
    print("Instalando osmnx...")
    import subprocess
    subprocess.check_call(["pip", "install", "osmnx"])
    import osmnx as ox

print(f"OSMnx versión: {ox.__version__}")
ox.settings.requests_timeout = 180
ox.settings.log_console = False

DATA_DIR = Path("data")
RAW_DIR  = DATA_DIR / "raw"
GEO_DIR  = DATA_DIR / "geo"
for d in [RAW_DIR, GEO_DIR]:
    d.mkdir(parents=True, exist_ok=True)

ISLAS = [
    "Lanzarote, Canary Islands, Spain",
    "Fuerteventura, Canary Islands, Spain",
    "Gran Canaria, Canary Islands, Spain",
    "Tenerife, Canary Islands, Spain",
    "La Palma, Canary Islands, Spain",
    "La Gomera, Canary Islands, Spain",
    "El Hierro, Canary Islands, Spain",
]

def asignar_isla(cusec):
    """Asigna la isla correspondiente según el código INE de sección censal (CUSEC)."""
    cod = str(cusec).zfill(10)
    prov = cod[:2]
    if prov == "38":
        mapa = {
            "38001": "El Hierro", "38002": "El Hierro", "38003": "La Palma",
            "38004": "La Palma", "38005": "La Palma", "38006": "La Gomera",
            "38007": "La Gomera", "38008": "Tenerife", "38009": "Tenerife",
            "38010": "Tenerife"
        }
        return mapa.get(cod[:5], "Tenerife")
    
    mapa = {
        "35001": "Fuerteventura", "35002": "Lanzarote", "35003": "Lanzarote",
        "35004": "Lanzarote", "35005": "Gran Canaria", "35006": "Gran Canaria",
        "35007": "Fuerteventura", "35008": "Gran Canaria", "35009": "Lanzarote",
        "35010": "Gran Canaria", "35011": "Fuerteventura", "35012": "Fuerteventura",
        "35013": "Gran Canaria", "35014": "Fuerteventura", "35015": "Lanzarote",
        "35016": "Gran Canaria", "35017": "Gran Canaria", "35018": "Gran Canaria",
        "35019": "Lanzarote", "35020": "Gran Canaria", "35021": "Gran Canaria",
        "35022": "Gran Canaria", "35023": "Lanzarote", "35024": "Lanzarote",
        "35025": "Fuerteventura", "35026": "Gran Canaria", "35027": "Gran Canaria",
        "35028": "Gran Canaria", "35029": "Lanzarote",
    }
    return mapa.get(cod[:5], "Gran Canaria")

# ==========================================
# 1. Geometría — Secciones censales de Canarias
# ==========================================
GEO_PATH = GEO_DIR / "secciones_canarias.gpkg"

if GEO_PATH.exists():
    print(f"Geometría existente encontrada: {GEO_PATH}")
    gdf = gpd.read_file(GEO_PATH)
else:
    print("Procesando secciones censales de Canarias...")
    t0 = time.time()

    zip_src = Path("seccionado_2025.zip")
    if zip_src.exists():
        tmp = Path(os.environ.get("TMP", "tmp")) / "secciones_tmp"
        if tmp.exists():
            shutil.rmtree(tmp)
        with zipfile.ZipFile(zip_src) as z:
            z.extractall(tmp)
        shp = list(tmp.rglob("*.shp"))[0]
        gdf = gpd.read_file(shp)
        gdf = gdf[gdf["CPRO"].isin(["35", "38"])]
        shutil.rmtree(tmp)
        gdf = gdf.to_crs("EPSG:4326")
    else:
        print("Descargando secciones censales vía API OGC Features del INE...")
        import requests
        bbox = "-18.5,27.5,-13.0,29.5"
        url = (
            "https://www.ine.es/geoserver/ogc/features/v1/collections/"
            "WMS_INE_SECCIONES_G01:Secciones_2025/items"
            f"?f=application/json&bbox={bbox}&limit=1000"
        )
        features = []
        session = requests.Session()
        next_url = url
        while next_url:
            r = session.get(next_url, timeout=120)
            r.raise_for_status()
            data = r.json()
            features.extend(data.get("features", []))
            next_url = next(
                (l["href"] for l in data.get("links", []) if l.get("rel") == "next"),
                None,
            )
        gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
        gdf = gdf[gdf["CPRO"].isin(["35", "38"])].copy()

    gdf["isla"] = gdf["CUSEC"].apply(asignar_isla)
    gdf["centroid_lon"] = gdf.geometry.centroid.x
    gdf["centroid_lat"] = gdf.geometry.centroid.y
    gdf.to_file(GEO_PATH, driver="GPKG")
    print(f"  OK: {len(gdf)} secciones procesadas en {time.time()-t0:.1f}s")
    print(f"  Distribución por islas: {gdf['isla'].value_counts().to_dict()}")

# ==========================================
# 2. POIs — Infraestructuras y recursos (OSMnx)
# ==========================================
POI_PATH = GEO_DIR / "pois_canarias.gpkg"

if POI_PATH.exists():
    print(f"POIs existentes encontrados: {POI_PATH}")
    pois = gpd.read_file(POI_PATH)
else:
    print("Descargando puntos de interés (POIs) isla por isla desde OpenStreetMap...")
    t0_all = time.time()
    todos = []
    tags = {
        "hospital": "amenity", "clinic": "amenity", "doctors": "amenity",
        "pharmacy": "amenity", "school": "amenity", "bus_stop": "highway"
    }

    for isla in ISLAS:
        nombre = isla.split(",")[0]
        print(f"  Descargando {nombre}...", end=" ", flush=True)
        t0 = time.time()
        try:
            for valor, clave in tags.items():
                gdf_poi = ox.features_from_place(isla, tags={clave: valor})
                if len(gdf_poi):
                    gdf_poi["amenity"] = valor
                    gdf_poi["isla"] = nombre
                    todos.append(gdf_poi)
            print(f"OK ({time.time()-t0:.1f}s)")
        except Exception as e:
            print(f"Error: {e}")

    if todos:
        pois = pd.concat(todos, ignore_index=True)
        pois = pois[pois.geometry.notna() & pois.geometry.is_valid]
        pois = pois[~pois.geometry.duplicated()]
        pois.to_file(POI_PATH, driver="GPKG")
        print(f"  OK Total POIs: {len(pois)} en {time.time()-t0_all:.1f}s")
    else:
        pois = gpd.GeoDataFrame(columns=["geometry", "amenity", "isla"], crs="EPSG:4326")

# ==========================================
# 3. Cálculo de Distancias a Servicios
# ==========================================
DIST_PATH = RAW_DIR / "distancias_servicios.csv"

if DIST_PATH.exists():
    print(f"Distancias existentes encontradas: {DIST_PATH}")
    df_dist = pd.read_csv(DIST_PATH, dtype={"CUSEC": str})
else:
    print("Calculando distancias espaciales a recursos públicos...")
    t0 = time.time()
    sec_utm = gdf.to_crs("EPSG:32628")
    poi_utm = pois.to_crs("EPSG:32628")

    grupos = {
        "hospitales": poi_utm[poi_utm["amenity"] == "hospital"],
        "clinicas":   poi_utm[poi_utm["amenity"].isin(["clinic", "doctors"])],
        "farmacias":  poi_utm[poi_utm["amenity"] == "pharmacy"],
        "colegios":   poi_utm[poi_utm["amenity"] == "school"],
        "paradas":    poi_utm[poi_utm["amenity"] == "bus_stop"],
    }

    resultados = []
    for _, sec in sec_utm.iterrows():
        c = sec.geometry.centroid
        def dmin(g): 
            if len(g) == 0:
                return None
            d = g.geometry.distance(c)
            return round(d.min() / 1000, 3) if len(d) else None
        def cnt(g, r): 
            if len(g) == 0:
                return 0
            return int((g.geometry.distance(c) <= r).sum())
            
        resultados.append({
            "CUSEC": sec["CUSEC"],
            "dist_min_hospital_km": dmin(grupos["hospitales"]),
            "dist_min_cs_km": dmin(grupos["clinicas"]),
            "dist_min_farmacia_km": dmin(grupos["farmacias"]),
            "dist_min_colegio_km": dmin(grupos["colegios"]),
            "dist_min_parada_km": dmin(grupos["paradas"]),
            "n_paradas_500m": cnt(grupos["paradas"], 500),
            "n_hospitales_5km": cnt(grupos["hospitales"], 5000),
        })

    df_dist = pd.DataFrame(resultados)
    df_dist.to_csv(DIST_PATH, index=False)
    print(f"  OK Cálculo completado en {time.time()-t0:.1f}s")

# ==========================================
# 4. Consolidación de Dataset Base
# ==========================================
OUT_CSV  = DATA_DIR / "dataset_canarias_raw.csv"
OUT_GPKG = DATA_DIR / "dataset_canarias.gpkg"

print("Fusionando datos geográficos y distancias...")
df = gdf[["CUSEC", "isla", "centroid_lon", "centroid_lat"]].copy()
df = df.merge(df_dist, on="CUSEC", how="left")

df.to_csv(OUT_CSV, index=False)
print(f"  CSV generado: {OUT_CSV} ({len(df)} registros)")

gdf_out = gdf[["CUSEC", "geometry"]].merge(df, on="CUSEC", how="left")
gdf_out.to_file(OUT_GPKG, driver="GPKG")
print(f"  GeoPackage generado: {OUT_GPKG}")

print("=" * 50)
print("SCRIPT 01 FINALIZADO CORRECTAMENTE")
print("=" * 50)
