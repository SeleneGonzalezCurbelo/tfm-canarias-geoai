# -*- coding: utf-8 -*-
"""
Script 01: Descarga de Geometría de Secciones Censales e Infraestructuras (POIs)
- Descarga y filtrado de secciones censales de Canarias (provincias 35 y 38) desde INE.
- Extracción de puntos de interés (hospitales, centros de salud, farmacias, colegios, paradas de autobús)
  isla por isla utilizando OSMnx (OpenStreetMap).
- Cálculo de distancias mínimas y disponibilidad de servicios por sección censal usando cKDTree vectorizado.
- Generación de dataset geoespacial base unificado (GPKG y CSV) en data/geo/, data/raw/ y data/.
"""

import os
import time
import json
import zipfile
import shutil
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.spatial import cKDTree

warnings.filterwarnings("ignore")

# Configuración de rutas raíz
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR  = DATA_DIR / "raw"
GEO_DIR  = DATA_DIR / "geo"
REP_DIR  = DATA_DIR / "reports"

for d in [RAW_DIR, GEO_DIR, REP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Configuración de OSMnx
try:
    import osmnx as ox
except ImportError:
    print("[INFO] Instalando osmnx...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "osmnx"])
        import osmnx as ox
    except Exception as e:
        print(f"[ERROR] No se pudo instalar osmnx: {e}")
        sys.exit(1)

print(f"[INFO] OSMnx versión: {ox.__version__}")
ox.settings.requests_timeout = 180
ox.settings.log_console = False

ISLAS: List[str] = [
    "Lanzarote, Canary Islands, Spain",
    "Fuerteventura, Canary Islands, Spain",
    "Gran Canaria, Canary Islands, Spain",
    "Tenerife, Canary Islands, Spain",
    "La Palma, Canary Islands, Spain",
    "La Gomera, Canary Islands, Spain",
    "El Hierro, Canary Islands, Spain",
]

t_start_total = time.time()
execution_stats: Dict[str, Any] = {"script": "01_descarga_geometria_e_infraestructuras"}


def asignar_isla(cusec: Union[str, int]) -> str:
    """Asigna la isla correspondiente según el código INE de sección censal (CUSEC).

    CUSEC (10 dígitos) = CPRO(2) + CMUN(3) + CDIS(2) + CSEC(3).
    Los códigos de municipio NO son contiguos por isla (orden alfabético
    provincial), así que se usa el diccionario oficial completo.
    Fuente de verdad para nmun: data/processed/poblacion/poblacion_canarias.csv.
    """
    cod = str(cusec).zfill(10)
    cmun = cod[:5]
    # Provincia 38 Santa Cruz de Tenerife (54 municipios + 38901 El Pinar)
    mapa_38 = {
        "38001": "Tenerife", "38002": "La Gomera", "38003": "La Gomera",
        "38004": "Tenerife", "38005": "Tenerife", "38006": "Tenerife",
        "38007": "La Palma", "38008": "La Palma", "38009": "La Palma",
        "38010": "Tenerife", "38011": "Tenerife", "38012": "Tenerife",
        "38013": "El Hierro", "38014": "La Palma", "38015": "Tenerife",
        "38016": "La Palma", "38017": "Tenerife", "38018": "Tenerife",
        "38019": "Tenerife", "38020": "Tenerife", "38021": "La Gomera",
        "38022": "Tenerife", "38023": "Tenerife", "38024": "La Palma",
        "38025": "Tenerife", "38026": "Tenerife", "38027": "La Palma",
        "38028": "Tenerife", "38029": "La Palma", "38030": "La Palma",
        "38031": "Tenerife", "38032": "Tenerife", "38033": "La Palma",
        "38034": "Tenerife", "38035": "Tenerife", "38036": "La Gomera",
        "38037": "La Palma", "38038": "Tenerife", "38039": "Tenerife",
        "38040": "Tenerife", "38041": "Tenerife", "38042": "Tenerife",
        "38043": "Tenerife", "38044": "Tenerife", "38045": "La Palma",
        "38046": "Tenerife", "38047": "La Palma", "38048": "El Hierro",
        "38049": "La Gomera", "38050": "La Gomera", "38051": "Tenerife",
        "38052": "Tenerife", "38053": "La Palma", "38901": "El Hierro",
    }
    if cod[:2] == "38":
        return mapa_38.get(cmun, "Tenerife")

    # Provincia 35 Las Palmas (34 municipios)
    mapa_35 = {
        "35001": "Gran Canaria", "35002": "Gran Canaria",
        "35003": "Fuerteventura", "35004": "Lanzarote",
        "35005": "Gran Canaria", "35006": "Gran Canaria",
        "35007": "Fuerteventura", "35008": "Gran Canaria",
        "35009": "Gran Canaria", "35010": "Lanzarote",
        "35011": "Gran Canaria", "35012": "Gran Canaria",
        "35013": "Gran Canaria", "35014": "Fuerteventura",
        "35015": "Fuerteventura", "35016": "Gran Canaria",
        "35017": "Fuerteventura", "35018": "Lanzarote",
        "35019": "Gran Canaria", "35020": "Gran Canaria",
        "35021": "Gran Canaria", "35022": "Gran Canaria",
        "35023": "Gran Canaria", "35024": "Lanzarote",
        "35025": "Gran Canaria", "35026": "Gran Canaria",
        "35027": "Gran Canaria", "35028": "Lanzarote",
        "35029": "Lanzarote", "35030": "Fuerteventura",
        "35031": "Gran Canaria", "35032": "Gran Canaria",
        "35033": "Gran Canaria", "35034": "Lanzarote",
    }
    return mapa_35.get(cmun, "Gran Canaria")


def main() -> None:
    try:
        # ==========================================
        # 1. Geometría — Secciones censales de Canarias
        # ==========================================
        GEO_PATH = GEO_DIR / "secciones_canarias.gpkg"

        if GEO_PATH.exists():
            print(f"[OK] Geometría existente encontrada: {GEO_PATH}")
            gdf = gpd.read_file(GEO_PATH)
        else:
            print("[INFO] Procesando secciones censales de Canarias...")
            t0 = time.time()

            zip_src = ROOT_DIR / "seccionado_2025.zip"
            if zip_src.exists():
                tmp = Path(os.environ.get("TMP", "tmp")) / "secciones_tmp"
                if tmp.exists():
                    shutil.rmtree(tmp)
                with zipfile.ZipFile(zip_src) as z:
                    z.extractall(tmp)
                shp_list = list(tmp.rglob("*.shp"))
                if not shp_list:
                    raise FileNotFoundError("No se encontró ningún archivo .shp en el ZIP de secciones.")
                shp = shp_list[0]
                gdf = gpd.read_file(shp)
                gdf = gdf[gdf["CPRO"].isin(["35", "38"])]
                shutil.rmtree(tmp)
                gdf = gdf.to_crs("EPSG:4326")
            else:
                print("[INFO] Descargando secciones censales vía API OGC Features del INE...")
                import requests
                bbox = "-18.5,27.5,-13.0,29.5"
                url = (
                    "https://www.ine.es/geoserver/ogc/features/v1/collections/"
                    "WMS_INE_SECCIONES_G01:Secciones_2025/items"
                    f"?f=application/json&bbox={bbox}&limit=1000"
                )
                features: List[Dict[str, Any]] = []
                session = requests.Session()
                next_url: Optional[str] = url
                while next_url:
                    r = session.get(next_url, timeout=120)
                    r.raise_for_status()
                    data = r.json()
                    features.extend(data.get("features", []))
                    links = data.get("links", [])
                    next_url = next(
                        (l["href"] for l in links if l.get("rel") == "next"),
                        None,
                    )
                gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
                gdf = gdf[gdf["CPRO"].isin(["35", "38"])].copy()

            gdf["isla"] = gdf["CUSEC"].apply(asignar_isla)
            gdf["centroid_lon"] = gdf.geometry.centroid.x
            gdf["centroid_lat"] = gdf.geometry.centroid.y
            gdf.to_file(GEO_PATH, driver="GPKG")
            print(f"  [OK] {len(gdf)} secciones procesadas en {time.time()-t0:.1f}s")
            print(f"  [INFO] Distribución por islas: {gdf['isla'].value_counts().to_dict()}")

        execution_stats["secciones_count"] = len(gdf)

        # ==========================================
        # 2. POIs — Infraestructuras y recursos (OSMnx)
        # ==========================================
        POI_PATH = GEO_DIR / "pois_canarias.gpkg"

        if POI_PATH.exists():
            print(f"[OK] POIs existentes encontrados: {POI_PATH}")
            pois = gpd.read_file(POI_PATH)
        else:
            print("[INFO] Descargando puntos de interés (POIs) isla por isla desde OpenStreetMap...")
            t0_all = time.time()
            todos: List[gpd.GeoDataFrame] = []
            tags = {
                "hospital": "amenity", "clinic": "amenity", "doctors": "amenity",
                "pharmacy": "amenity", "school": "amenity", "bus_stop": "highway"
            }

            for isla in ISLAS:
                nombre = isla.split(",")[0]
                print(f"  [INFO] Descargando {nombre}...", end=" ", flush=True)
                t0 = time.time()
                try:
                    for valor, clave in tags.items():
                        gdf_poi = ox.features_from_place(isla, tags={clave: valor})
                        if not gdf_poi.empty:
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
                print(f"  [OK] Total POIs: {len(pois)} en {time.time()-t0_all:.1f}s")
            else:
                pois = gpd.GeoDataFrame(columns=["geometry", "amenity", "isla"], crs="EPSG:4326")

        execution_stats["pois_count"] = len(pois)

        # ==========================================
        # 3. Cálculo de Distancias a Servicios
        # ==========================================
        DIST_PATH = RAW_DIR / "distancias_servicios.csv"

        if DIST_PATH.exists():
            print(f"[OK] Distancias existentes encontradas: {DIST_PATH}")
            df_dist = pd.read_csv(DIST_PATH, dtype={"CUSEC": str})
            df_dist["CUSEC"] = df_dist["CUSEC"].astype(str).str.zfill(10)
        else:
            print("[INFO] Calculando distancias espaciales a recursos públicos (Vectorizado con cKDTree)...")
            t0 = time.time()
            sec_utm = gdf.to_crs("EPSG:32628")
            poi_utm = pois.to_crs("EPSG:32628")

            centroids = sec_utm.geometry.centroid
            sec_coords = np.column_stack((centroids.x, centroids.y))

            grupos = {
                "hospitales": poi_utm[poi_utm["amenity"] == "hospital"],
                "clinicas":   poi_utm[poi_utm["amenity"].isin(["clinic", "doctors"])],
                "farmacias":  poi_utm[poi_utm["amenity"] == "pharmacy"],
                "colegios":   poi_utm[poi_utm["amenity"] == "school"],
                "paradas":    poi_utm[poi_utm["amenity"] == "bus_stop"],
            }

            dist_data: Dict[str, Any] = {"CUSEC": sec_utm["CUSEC"].astype(str).str.zfill(10)}

            for key, g in grupos.items():
                col_name = {
                    "hospitales": "dist_min_hospital_km",
                    "clinicas": "dist_min_cs_km",
                    "farmacias": "dist_min_farmacia_km",
                    "colegios": "dist_min_colegio_km",
                    "paradas": "dist_min_parada_km"
                }[key]

                if len(g) == 0:
                    dist_data[col_name] = None
                    if key == "paradas":
                        dist_data["n_paradas_500m"] = 0
                    elif key == "hospitales":
                        dist_data["n_hospitales_5km"] = 0
                    continue

                poi_coords = np.column_stack((g.geometry.x, g.geometry.y))
                tree = cKDTree(poi_coords)

                # Distancia mínima vectorizada (en km, redondeada a 3 decimales)
                dists, _ = tree.query(sec_coords, k=1)
                dist_data[col_name] = np.round(dists / 1000.0, 3)

                # Conteos en radio vectorizados
                if key == "paradas":
                    dist_data["n_paradas_500m"] = tree.query_ball_point(sec_coords, r=500, p=2, return_length=True)
                elif key == "hospitales":
                    dist_data["n_hospitales_5km"] = tree.query_ball_point(sec_coords, r=5000, p=2, return_length=True)

            df_dist = pd.DataFrame(dist_data)
            df_dist.to_csv(DIST_PATH, index=False)
            print(f"  [OK] Cálculo vectorizado completado en {time.time()-t0:.1f}s")

        # ==========================================
        # 4. Consolidación de Dataset Base
        # ==========================================
        OUT_CSV  = DATA_DIR / "dataset_canarias_raw.csv"
        OUT_GPKG = DATA_DIR / "dataset_canarias.gpkg"

        print("[INFO] Fusionando datos geográficos y distancias con validación estricta...")
        gdf["CUSEC"] = gdf["CUSEC"].astype(str).str.zfill(10)
        df_dist["CUSEC"] = df_dist["CUSEC"].astype(str).str.zfill(10)

        df = gdf[["CUSEC", "isla", "centroid_lon", "centroid_lat"]].copy()
        df = df.merge(df_dist, on="CUSEC", how="left", validate="one_to_one")

        # Validación post-merge y de tipos/nulos
        assert df.shape[0] == len(gdf), f"Error de filas tras merge: {df.shape[0]} vs {len(gdf)}"
        assert df["CUSEC"].str.len().eq(10).all(), "Existen códigos CUSEC que no tienen 10 dígitos"

        df.to_csv(OUT_CSV, index=False)
        print(f"  [OK] CSV generado: {OUT_CSV} ({len(df)} registros)")

        gdf_out = gdf[["CUSEC", "geometry"]].copy()
        gdf_out["CUSEC"] = gdf_out["CUSEC"].astype(str).str.zfill(10)
        gdf_out = gdf_out.merge(df, on="CUSEC", how="left", validate="one_to_one")
        gdf_out.to_file(OUT_GPKG, driver="GPKG")
        print(f"  [OK] GeoPackage generado: {OUT_GPKG}")

        # Resumen de validación y calidad
        execution_stats["total_duration_sec"] = round(time.time() - t_start_total, 2)
        execution_stats["nulls_summary"] = df.isna().sum().to_dict()
        execution_stats["outputs"] = [str(GEO_PATH), str(POI_PATH), str(DIST_PATH), str(OUT_CSV), str(OUT_GPKG)]

        meta_path = REP_DIR / "01_metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(execution_stats, f, indent=4, ensure_ascii=False)

        print("\n" + "=" * 60)
        print("RESUMEN DE VALIDACIÓN - SCRIPT 01")
        print("=" * 60)
        print(f"• Secciones procesadas: {len(df):,}")
        print(f"• POIs extraídos: {len(pois):,}")
        print(f"• Ficheros generados:")
        for out in execution_stats["outputs"]:
            sz = Path(out).stat().st_size / (1024 * 1024)
            print(f"  - {out} ({sz:.2f} MB)")
        print(f"• Tiempo total de ejecución: {execution_stats['total_duration_sec']}s")
        print("=" * 60)
        print("SCRIPT 01 FINALIZADO CORRECTAMENTE")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] El script 01 ha fallado: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
