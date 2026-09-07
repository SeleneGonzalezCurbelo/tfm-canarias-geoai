# -*- coding: utf-8 -*-
"""
Script 01b: Fusión de POIs descargados manualmente (Overpass Turbo)
- Lee los GeoJSON manuales de data/raw/overpass_manual/ (uno por isla o uno por isla+categoría).
- Normaliza columnas a geometry, amenity, isla en EPSG:4326.
- Hace backup del pois_canarias.gpkg existente y genera el fusionado.
- El script 01 reutiliza el GPKG si existe y salta la descarga vía Overpass.
Uso:
    python scripts/01b_fusion_pois_manuales.py
    python scripts/01b_fusion_pois_manuales.py --check-only
"""

import argparse
import shutil
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
MANUAL_DIR = ROOT_DIR / "data" / "raw" / "overpass_manual"
POI_PATH = ROOT_DIR / "data" / "geo" / "pois_canarias.gpkg"

WANTED = {"hospital", "clinic", "doctors", "pharmacy", "school", "bus_stop"}


def normalizar(gdf: gpd.GeoDataFrame, isla: str) -> gpd.GeoDataFrame:
    gdf = gdf.to_crs("EPSG:4326")
    amenity = gdf.get("amenity")
    highway = gdf.get("highway")
    if highway is not None:
        norm = highway.where(highway == "bus_stop", amenity)
    else:
        norm = amenity
    gdf = gdf.assign(isla=isla, amenity=norm)
    gdf = gdf[gdf["amenity"].isin(WANTED)]
    return gdf[["geometry", "amenity", "isla"]]


def isla_desde_nombre(path: Path) -> str:
    stem = path.stem
    for sep in ["__", "--", "_-_", "__TAG__"]:
        if sep in stem:
            stem = stem.split(sep)[0]
            break
    if "_" in stem and " " not in stem:
        candidato = stem.split("_")[0]
        if len(stem.split("_")) > 2 or candidato.lower() in {
            "tenerife", "palma", "gomera", "hierro", "lanzarote",
            "fuerteventura", "canaria",
        }:
            return candidato
    return stem


def main() -> None:
    ap = argparse.ArgumentParser(description="Fusiona POIs manuales de Overpass a pois_canarias.gpkg.")
    ap.add_argument("--check-only", action="store_true", help="Solo valida los GeoJSON sin escribir el GPKG.")
    ap.add_argument("--no-backup", action="store_true", help="No crea copia de seguridad del GPKG existente.")
    args = ap.parse_args()

    files = sorted(MANUAL_DIR.glob("*.geojson"))
    if not files:
        print(f"[ERROR] Sin GeoJSON en {MANUAL_DIR}. Esperado: <Isla>.geojson", file=sys.stderr)
        sys.exit(1)

    todos = []
    for p in files:
        isla = isla_desde_nombre(p)
        gdf = gpd.read_file(p)
        n_in = len(gdf)
        gdf = normalizar(gdf, isla)
        print(f"  [INFO] {p.name}: isla={isla} {n_in} -> {len(gdf)} POIs")
        todos.append(gdf)

    pois = pd.concat(todos, ignore_index=True)
    pois = pois[pois.geometry.notna() & pois.geometry.is_valid]
    pois = pois[~pois.geometry.duplicated()].copy()
    pois = gpd.GeoDataFrame(pois, crs="EPSG:4326")

    print(f"[INFO] Total: {len(pois)} POIs")
    print(f"  amenity: {pois['amenity'].value_counts().to_dict()}")
    print(f"  isla: {pois['isla'].value_counts().to_dict()}")

    if args.check_only:
        print("[OK] Validación correcta (sin escritura).")
        return

    if POI_PATH.exists() and not args.no_backup:
        backup = POI_PATH.with_name("pois_canarias_auto_backup.gpkg")
        shutil.copy2(POI_PATH, backup)
        print(f"[OK] Backup: {backup}")

    POI_PATH.parent.mkdir(parents=True, exist_ok=True)
    pois.to_file(POI_PATH, driver="GPKG")
    print(f"[OK] GPKG generado: {POI_PATH} ({len(pois)} registros)")


if __name__ == "__main__":
    main()
