# -*- coding: utf-8 -*-
"""
Script 07: Fusion final del dataset de Canarias para EDA y entrenamiento.
Une las salidas de los pasos 01-06 en data/outputs/dataset_final.csv/.gpkg.
Modo prototipo: cada fuente es opcional salvo la geometria de secciones;
las ausentes se registran como warnings sin detener la fusion.
"""

import json
import sys
import time
import warnings
from pathlib import Path
from typing import Any, Dict, List

import geopandas as gpd
import pandas as pd

warnings.filterwarnings("ignore")

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = DATA_DIR / "outputs"
REPORTS_DIR = DATA_DIR / "reports"
for d in [OUTPUT_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

GEO_PATH = DATA_DIR / "geo" / "secciones_canarias.gpkg"
BASE_CSV = DATA_DIR / "dataset_canarias_raw.csv"
DIST_CSV = DATA_DIR / "raw" / "distancias_servicios.csv"
POB_CSV = DATA_DIR / "processed" / "poblacion" / "poblacion_canarias.csv"
RENTA_CSV = DATA_DIR / "processed" / "renta" / "renta_media_hogar_canarias.csv"
CENSO_CSV = DATA_DIR / "processed" / "censo" / "censo2021_canarias.csv"
ADRH_DIR = DATA_DIR / "processed" / "adrh"

ADRH_FILES = {
    "salario_renta": ("salario_renta_canarias.csv", "sal"),
    "indice_gini": ("indice_gini_canarias.csv", "gini"),
    "pensiones_renta": ("pensiones_renta_canarias.csv", "pen"),
    "p80p20": ("p80p20_canarias.csv", "p80"),
}

DROP_ADMIN = {"cpro", "npro", "nca", "nmun", "lon", "lat",
              "centroid_lon", "centroid_lat", "geometry", "lon32628", "lat32628"}

VARS_MODELO_ORDEN = [
    "dist_min_hospital_km", "dist_min_cs_km", "dist_min_farmacia_km",
    "dist_min_colegio_km", "dist_min_parada_km",
    "n_paradas_500m", "n_hospitales_5km",
    "poblacion_total", "pct_extranjeros", "pct_nacidos_extranjero",
    "indice_envejecimiento", "tasa_dependencia", "pct_menor_18", "pct_mayor_65",
    "densidad_hab_km2", "densidad_real_hab_km2",
    "renta_neta_media_hogar", "renta_neta_media_persona",
    "pct_ingresos_bajos_7500", "pct_riesgo_pobreza_60", "pct_ingresos_altos_200",
    "indice_gini",
    "pct_activos", "pct_estudios_superiores", "nivel_estudios_medio",
    "total_viviendas", "total_hogares", "tamano_medio_hogar",
    "area_km2", "perimetro_km",
    "dens_hospitales_km2", "dens_paradas_km2",
]

t_start = time.time()
stats: Dict[str, Any] = {"script": "07_fusion_dataset_final", "fuentes": {}}


def norm_cusec(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.zfill(10)


def load_csv_keyed(path: Path, label: str) -> pd.DataFrame | None:
    if not path.exists():
        stats["fuentes"][label] = {"path": str(path), "estado": "ausente"}
        print(f"  [WARN] {label}: ausente ({path.relative_to(ROOT_DIR)})")
        return None
    df = pd.read_csv(path, dtype=str)
    key = next((c for c in df.columns if c.lower() == "cusec"), None)
    if key is None and df.index.name is not None and str(df.index.name).lower() == "cusec":
        df = df.reset_index()
        key = df.columns[0]
    if key is None:
        stats["fuentes"][label] = {"path": str(path), "estado": "sin_clave_cusec"}
        print(f"  [WARN] {label}: sin columna cusec, se omite")
        return None
    df = df.rename(columns={key: "CUSEC"})
    df["CUSEC"] = norm_cusec(df["CUSEC"])
    df = df.drop_duplicates(subset="CUSEC", keep="first")
    for c in list(df.columns):
        if c != "CUSEC":
            try:
                df[c] = pd.to_numeric(df[c], errors="raise")
            except (ValueError, TypeError):
                pass
    stats["fuentes"][label] = {"path": str(path), "estado": "ok", "filas": len(df)}
    print(f"  [OK] {label}: {len(df)} filas")
    return df


def merge_left(df: pd.DataFrame, aux: pd.DataFrame | None, cols: List[str], label: str) -> pd.DataFrame:
    if aux is None:
        return df
    use = ["CUSEC"] + [c for c in cols if c in aux.columns and c != "CUSEC"]
    if len(use) == 1:
        print(f"  [WARN] {label}: sin columnas nuevas, se omite")
        return df
    use = list(dict.fromkeys(use))
    out = df.merge(aux[use], on="CUSEC", how="left", validate="one_to_one")
    con = int(out[use[1]].notna().sum()) if len(use) > 1 else 0
    print(f"  [OK] {label}: {con}/{len(out)} ({100 * con / len(out):.1f}%) cols={use[1:]}")
    stats["fuentes"][label]["integradas"] = con
    stats["fuentes"][label]["columnas"] = use[1:]
    return out


def main() -> None:
    try:
        if not GEO_PATH.exists():
            raise FileNotFoundError(f"Sin geometria base: {GEO_PATH}. Ejecute el paso 01 primero.")

        print("[1/6] Geometria y area...")
        gdf_sec = gpd.read_file(GEO_PATH)
        key = next((c for c in gdf_sec.columns if c.lower() == "cusec"), None)
        if key is None:
            raise KeyError("Sin columna CUSEC/cusec en secciones_canarias.gpkg")
        gdf_sec = gdf_sec.rename(columns={key: "CUSEC"})
        gdf_sec["CUSEC"] = norm_cusec(gdf_sec["CUSEC"])
        print(f"  Secciones: {len(gdf_sec)} | CRS: {gdf_sec.crs}")
        gdf_utm = gdf_sec.to_crs("EPSG:32628")
        gdf_sec["area_km2"] = (gdf_utm.geometry.area / 1e6).round(4)
        gdf_sec["perimetro_km"] = (gdf_utm.geometry.length / 1000).round(4)
        stats["fuentes"]["geometria"] = {"path": str(GEO_PATH), "estado": "ok", "filas": len(gdf_sec)}
        stats["secciones_base"] = len(gdf_sec)

        print("[2/6] Base 01 + distancias...")
        df_base = load_csv_keyed(BASE_CSV, "base_01")
        if df_base is None:
            cols = ["CUSEC", "isla", "centroid_lon", "centroid_lat"]
            df = gdf_sec[[c for c in cols if c in gdf_sec.columns]].copy()
            df = df.drop_duplicates(subset="CUSEC", keep="first")
            stats["fuentes"]["base_01"] = {"estado": "reconstruida_desde_geometria", "filas": len(df)}
            print(f"  [OK] base reconstruida desde geometria: {len(df)} filas")
        else:
            df = df_base
        df_dist = load_csv_keyed(DIST_CSV, "distancias_01")
        if df_dist is not None:
            nuevas = [c for c in df_dist.columns if c not in df.columns and c != "CUSEC"]
            df = merge_left(df, df_dist, nuevas, "distancias_01")

        print("[3/6] Demografia 05 + censo 02...")
        df_pob = load_csv_keyed(POB_CSV, "poblacion_05")
        if df_pob is not None:
            cols = [c for c in df_pob.columns if c.lower() not in DROP_ADMIN or c == "CUSEC"]
            df = merge_left(df, df_pob, cols, "poblacion_05")
        df_censo = load_csv_keyed(CENSO_CSV, "censo_02")
        if df_censo is not None:
            cols = [c for c in df_censo.columns if c != "CUSEC"]
            df = merge_left(df, df_censo, cols, "censo_02")

        print("[4/6] Renta 04 + ADRH 03...")
        df_renta = load_csv_keyed(RENTA_CSV, "renta_04")
        if df_renta is not None:
            cols = [c for c in df_renta.columns if c.lower() not in DROP_ADMIN or c == "CUSEC"]
            df = merge_left(df, df_renta, cols, "renta_04")
        for layer, (fname, prefix) in ADRH_FILES.items():
            aux = load_csv_keyed(ADRH_DIR / fname, f"adrh_{layer}")
            if aux is None:
                continue
            rename = {}
            for c in list(aux.columns):
                if c == "CUSEC" or c.lower() in DROP_ADMIN:
                    continue
                if not c.startswith(prefix + "_"):
                    rename[c] = f"{prefix}_{c}"
            aux = aux.rename(columns=rename)
            cols = [c for c in aux.columns if c.lower() not in DROP_ADMIN or c == "CUSEC"]
            df = merge_left(df, aux, cols, f"adrh_{layer}")

        print("[5/6] Area y densidades...")
        df = df.merge(gdf_sec[["CUSEC", "area_km2", "perimetro_km"]].drop_duplicates("CUSEC"),
                      on="CUSEC", how="left", validate="one_to_one")
        if "poblacion_total" in df.columns:
            df["densidad_real_hab_km2"] = (pd.to_numeric(df["poblacion_total"], errors="coerce")
                                           / pd.to_numeric(df["area_km2"], errors="coerce")).round(2)
        if "n_hospitales_5km" in df.columns:
            df["dens_hospitales_km2"] = (pd.to_numeric(df["n_hospitales_5km"], errors="coerce")
                                         / pd.to_numeric(df["area_km2"], errors="coerce")).round(4)
        if "n_paradas_500m" in df.columns:
            df["dens_paradas_km2"] = (pd.to_numeric(df["n_paradas_500m"], errors="coerce")
                                      / pd.to_numeric(df["area_km2"], errors="coerce")).round(4)

        print("[6/6] Imputacion y guardado...")
        vars_modelo = [v for v in VARS_MODELO_ORDEN if v in df.columns]
        falt = df[vars_modelo].isna().sum() if vars_modelo else pd.Series(dtype=int)
        falt = falt[falt > 0]
        stats["imputacion"] = {str(k): int(v) for k, v in falt.items()}
        if len(falt) > 0:
            for col in falt.index:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(df[col].median())
            print(f"  Imputados por mediana: {list(falt.index)}")
        else:
            print("  Sin faltantes en vars de modelado")

        ids = ["CUSEC", "isla", "centroid_lon", "centroid_lat"]
        cols_out = [c for c in ids if c in df.columns] + [v for v in vars_modelo if v not in ids]
        df_out = df[cols_out].copy()
        assert df_out["CUSEC"].str.len().eq(10).all(), "CUSEC no normalizado a 10 digitos"
        assert not df_out["CUSEC"].duplicated().any(), "CUSEC duplicados en dataset final"

        csv_path = OUTPUT_DIR / "dataset_final.csv"
        gpkg_path = OUTPUT_DIR / "dataset_final.gpkg"
        df_out.to_csv(csv_path, index=False)
        gdf_out = gdf_sec[["CUSEC", "geometry"]].drop_duplicates("CUSEC").merge(
            df_out, on="CUSEC", how="inner", validate="one_to_one")
        gdf_out.to_file(gpkg_path, driver="GPKG")
        print(f"  [OK] {csv_path.name}: {len(df_out)} x {len(df_out.columns)}")
        print(f"  [OK] {gpkg_path.name}: {len(gdf_out)} con geometria")

        stats["total_duration_sec"] = round(time.time() - t_start, 2)
        stats["secciones_final"] = len(df_out)
        stats["variables_modelo"] = vars_modelo
        stats["nulls_restantes"] = int(df_out[vars_modelo].isna().sum().sum()) if vars_modelo else 0
        stats["outputs"] = [str(csv_path), str(gpkg_path)]
        with open(REPORTS_DIR / "07_metadata.json", "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=4, ensure_ascii=False)

        print("=" * 60)
        print(f"SCRIPT 07 OK: {len(df_out)} secciones x {len(df_out.columns)} cols en {stats['total_duration_sec']}s")
        if "isla" in df_out.columns:
            print(df_out["isla"].value_counts().to_dict())
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] El script 07 ha fallado: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
