# Análisis de Accesibilidad a Recursos Públicos en Canarias y Propuesta de Mejora en Zonas Vulnerables

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![GeoPandas](https://img.shields.io/badge/GeoPandas-Spatial-green.svg)
![OSMnx](https://img.shields.io/badge/OSMnx-OpenStreetMap-orange.svg)
![INE API](https://img.shields.io/badge/INE-OpenData-red.svg)
![CRS](https://img.shields.io/badge/CRS-ETRS89%20%2F%20UTM%2028N-yellow.svg)
![License](https://img.shields.io/badge/License-MIT-blue.svg)
![TFE](https://img.shields.io/badge/TFE-Trabajo%20Fin%20de%20Estudios-purple.svg)

---

## 📌 Descripción del Proyecto

Este repositorio contiene el desarrollo técnico, metodológico y analítico correspondiente al **Trabajo Fin de Estudios (TFE)** enfocado en el **análisis de la accesibilidad espacial a los recursos y servicios públicos esenciales** (sanidad, educación, transporte y bienestar social) en el archipiélago canario.

El proyecto integra datos geoespaciales de alta resolución a nivel de **sección censal** (Provincias de Las Palmas - 35 y Santa Cruz de Tenerife - 38) combinados con indicadores sociodemográficos del **INE (Censo 2021)** y del **Atlas de Distribución de Renta de los Hogares (ADRH)**, con el objetivo de identificar áreas vulnerables, brechas territoriales y proponer optimizaciones basadas en ciencia de datos geoespaciales.

Fuente única autoritativa para análisis y modelado: `data/outputs/dataset_final.csv` (1581 secciones × 36 cols, 0 nulos, CUSEC 10 dígitos, imputación por mediana en `scripts/07_fusion_dataset_final.py`). Trazabilidad en `data/reports/07_metadata.json`.

---

## 📑 Tabla de Contenidos

- [📌 Descripción del Proyecto](#-descripción-del-proyecto)
- [📂 Estructura del Repositorio](#-estructura-del-repositorio)
- [⚙️ Requisitos del Sistema y Dependencias](#️-requisitos-del-sistema-y-dependencias)
- [📥 Guía de Instalación](#-guía-de-instalación)
- [🛠️ Pipeline Metodológico (`scripts/`)](#️-pipeline-metodológico-scripts)
- [📓 Notebooks (`notebooks/`)](#-notebooks-notebooks)
- [🚀 Guía de Uso y Ejecución](#-guía-de-uso-y-ejecución)
- [🤝 Contribución](#-contribución)
- [📄 Licencia](#-licencia)

---

## 📂 Estructura del Repositorio

```text
cap4-planteamiento/
│
├── data/
│   ├── outputs/
│   │   ├── dataset_final.csv / .gpkg  # Dataset autoritativo 1581×36, 0 nulos (script 07)
│   │   ├── resultados_modelado.csv    # merged_df + clusters AE/PCA + cuadrantes LISA (nb 02)
│   │   ├── latent_space_autoencoder.csv / pca_components.csv
│   │   ├── tabla_comparativa_final.csv / analisis_ablacion.csv
│   │   ├── busqueda_hiperparametros_ae.csv / mejores_hiperparametros_ae.json
│   │   ├── rfe_ranking_variables.csv / xgboost_spatial_island_kfold.csv
│   │   └── secciones_area_censo2021.gpkg / .csv
│   ├── reports/
│   │   └── 07_metadata.json           # Trazabilidad script 07 (imputación, vars modelo, joins)
│   ├── geo/
│   │   ├── secciones_canarias.gpkg     # Delimitación oficial de secciones censales y centroides
│   │   └── pois_canarias.gpkg          # Infraestructuras y Puntos de Interés (OSM)
│   └── raw/
│       ├── distancias_servicios.csv    # Distancias mínimas calculadas a servicios
│       └── overpass_manual/            # GeoJSON manuales de Overpass Turbo (<Isla>.geojson)
│
├── notebooks/
│   ├── 01_eda.ipynb                   # EDA sobre dataset_final + feature-set 18 + K-Means K=4
│   └── 02_modelado_benchmark.ipynb    # Benchmark AE vs PCA vs K-Means vs XGBoost + validación espacial
│
├── scripts/
│   ├── 01_descarga_geometria_e_infraestructuras.py # Geometrías censales y POIs (OSMnx)
│   ├── 01b_fusion_pois_manuales.py               # Fusiona GeoJSON manuales a pois_canarias.gpkg
│   ├── 02_descarga_censo_2021_ine.py             # Variables censales INE 2021
│   ├── 03_descarga_adrh_renta_ine.py             # Indicadores ADRH (Gini, P80/P20, salarios)
│   ├── 04_descarga_renta_media_hogar.py          # Renta neta media y pobreza
│   ├── 05_poblacion_demografia.py                # Demografía, envejecimiento y dependencia
│   ├── 06_calculo_areas_e_integracion_censo2021.py # Superficies UTM 28N y tasa de paro
│   ├── 07_fusion_dataset_final.py              # Fusión final del dataset para EDA y entrenamiento
│   ├── adrh_canarias/                          # Outputs parciales ADRH (.gpkg, .csv, .geojson)
│   ├── poblacion_canarias/                     # Outputs parciales demografía (.gpkg, .csv)
│   └── renta_hogar/                            # Outputs parciales renta hogares (.gpkg, .csv)
│
├── cache/                                      # Caché de peticiones API y descargas
├── venv/                                       # Entorno virtual de Python
├── requirements.txt                            # Dependencias del proyecto
├── LICENSE                                     # Licencia del proyecto (MIT)
└── README.md                                   # Documentación principal del proyecto
```

---

## ⚙️ Requisitos del Sistema y Dependencias

### Prerrequisitos
* **Python** `>= 3.10` instalado en el sistema.
* Conexión a internet activa para la descarga de datos desde la API del INE y OpenStreetMap (`OSMnx`).
* GPU (CUDA) opcional: el Autoencoder (PyTorch) y XGBoost (`tree_method='hist', device='cuda'`) la usan si está disponible, con fallback a CPU.

### Dependencias Principales (`requirements.txt`)
* `pandas` `>= 2.0.0` (entorno fijado: 3.0.3)
* `geopandas` `>= 0.12.0` (fijado: 1.1.3)
* `osmnx` `>= 1.3.0` (fijado: 2.1.1)
* `requests` `>= 2.28.0`
* `shapely` `>= 2.0.0`
* `pyogrio` `>= 0.5.0`
* `scikit-learn` `>= 1.2.0` (fijado: 1.9.0 — StandardScaler, PCA, K-Means, RFE, RandomForest)
* `scipy` / `seaborn` / `folium` `>= 0.15.0` (fijado: 0.20.0 — mapas)
* Modelado/validación espacial (ver `notebooks/02`): `torch`, `xgboost`, `libpysal`, `esda`, `branca`, `scikit-fuzzy` (opcional, §7.6), `mapclassify` (opcional Colab)

---

## 📥 Guía de Instalación

Sigue estos pasos para clonar y configurar el entorno de desarrollo en tu equipo local:

1. **Clonar el repositorio** (o acceder al directorio de trabajo):
   ```bash
   git clone <url-del-repositorio>
   cd cap4-planteamiento
   ```

2. **Crear el entorno virtual** en la raíz del proyecto:
   ```bash
   python -m venv venv
   ```

3. **Activar el entorno virtual**:
   * En **Windows (PowerShell o CMD)**:
     ```bash
     .\venv\Scripts\Activate
     ```
   * En **Linux / macOS**:
     ```bash
     source venv/bin/activate
     ```

4. **Actualizar pip e instalar las dependencias**:
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   # En Colab, además (opcional): %pip install -q libpysal esda mapclassify scikit-fuzzy
   ```

---

## 🛠️ Pipeline Metodológico (`scripts/`)

El pipeline consta de 7 scripts modulares secuenciales ubicados en `scripts/`, diseñados para la adquisición, preprocesamiento, cálculo espacial y enriquecimiento sociodemográfico:

| Orden | Script | Descripción Funcional & Outputs Principales |
| :---: | :--- | :--- |
| **01** | `01_descarga_geometria_e_infraestructuras.py` | Descarga el seccionado censal oficial de Canarias y extrae POIs de OpenStreetMap (hospitales, centros de salud, farmacias, colegios, paradas de autobús) isla por isla. Calcula distancias mínimas. <br>**Outputs:** `data/geo/secciones_canarias.gpkg`, `data/geo/pois_canarias.gpkg`. |
| **01b** *(opcional)* | `01b_fusion_pois_manuales.py` | Fusiona los GeoJSON descargados manualmente en Overpass Turbo (`data/raw/overpass_manual/<Isla>.geojson`) a `data/geo/pois_canarias.gpkg` (`EPSG:4326`, columnas `geometry,amenity,isla`; con backup automático). Úsalo solo si `01` falla por `timeout` de Overpass. |
| **02** | `02_descarga_censo_2021_ine.py` | Consulta la API del INE para extraer variables clave del Censo 2021 (población activa, ocupados, parados, estudios superiores y tipología de viviendas) a nivel de sección censal. <br>**Outputs:** `data/censo2021_canarias.csv`. |
| **03** | `03_descarga_adrh_renta_ine.py` | Obtiene indicadores del Atlas de Distribución de Renta de los Hogares (ADRH INE): Gini, P80/P20, peso de salarios y pensiones. <br>**Outputs:** `scripts/adrh_canarias/*`. |
| **04** | `04_descarga_renta_media_hogar.py` | Extrae la renta neta media por persona y hogar, así como umbrales de riesgo de pobreza. <br>**Outputs:** `scripts/renta_hogar/*`. |
| **05** | `05_poblacion_demografia.py` | Calcula población total, densidad demográfica, población extranjera, índice de envejecimiento y tasa de dependencia. <br>**Outputs:** `scripts/poblacion_canarias/*`. |
| **06** | `06_calculo_areas_e_integracion_censo2021.py` | Proyecta las secciones censales a **ETRS89 / UTM Zona 28N (EPSG:32628)** para calcular superficie en $km^2$ e integra la tasa de desempleo del Censo INE. <br>**Outputs:** `data/outputs/secciones_area_censo2021.gpkg`. |
| **07** | `07_fusion_dataset_final.py` | Fusiona todas las fuentes previas (geometría, distancias, demografía, censo, renta y ADRH) en un dataset integrado final, aplicando imputación por mediana y cálculo de densidades (`densidad_real = poblacion_total / area_km2`, `area` vía `to_crs(EPSG:32628).area/1e6`). Join `one_to_one` validado. <br>**Outputs:** `data/outputs/dataset_final.gpkg`, `data/outputs/dataset_final.csv` (1581×36, 0 nulos), `data/reports/07_metadata.json`. |

---

> [!WARNING]
> **Disponibilidad de la API (Overpass / OSM)**
>
> La descarga de POIs del script `01` depende de la API pública de Overpass (`overpass-api.de/api/interpreter`, `timeout=180s`). En momentos de carga puede fallar por isla, p. ej.:
>
> ```text
> [INFO] Descargando Fuerteventura... Error: HTTPSConnectionPool(host='overpass-api.de', port=443): Max retries exceeded with url: /api/interpreter (Caused by ConnectTimeoutError(... 'Connection to overpass-api.de timed out. (connect timeout=180)'))
> ```
>
> No es un error del código: el script captura el fallo por isla y continúa, pero `data/geo/pois_canarias.gpkg` quedará incompleto. Basta con reintentar `python scripts/01_descarga_geometria_e_infraestructuras.py` más tarde (reutiliza la caché en `data/geo/`); verifica la cobertura por `isla` antes de seguir al paso 02.
>
> **Descarga manual (si el error persiste):** usa [Overpass Turbo](https://overpass-turbo.eu/) con 1 consulta por categoría, `Exportar > GeoJSON`, y guarda cada isla como `data/raw/overpass_manual/<Isla>.geojson`. Ejemplo:
>
> ```ql
> [out:json][timeout:60];
> (node["amenity"="school"]({{bbox}});way["amenity"="school"]({{bbox}});relation["amenity"="school"]({{bbox}}););out center;
> ```
>
> Repite con `hospital, clinic, doctors, pharmacy` y `highway=bus_stop`, y fusiona con:
>
> ```bash
> python scripts/01b_fusion_pois_manuales.py --check-only  # valida sin escribir
> python scripts/01b_fusion_pois_manuales.py              # genera data/geo/pois_canarias.gpkg (con backup)
> ```
>
> El script `01` lo reutilizará (`[OK] POIs existentes`).

---

## 📓 Notebooks (`notebooks/`)

Sin montaje de Google Drive: ambos notebooks leen el dataset local versionado `data/outputs/dataset_final.csv`. Ejecutar en orden `01 → 02`.

### 01 — EDA sobre `dataset_final` autoritativo (`notebooks/01_eda.ipynb`)

Solo EDA + feature-set + K-Means exploratorio K=4. **No reconstruye merges ni reimputa** (merge `outer` legacy 1581×243 desactivado; normalización no aplica; `add_legacy_aliases()` deprecated).

* **Carga validada (§1–5):** 1581×36, 0 nulos, CUSEC 10 dígitos sin duplicados. Cobertura: Tenerife 713, Gran Canaria 576, Lanzarote 160, Fuerteventura 60, La Gomera 37, El Hierro 21, La Palma 14.
* **Rangos (§4, §9) y densidad (§8):** `pct_extranjeros ∈ [0,100]` (0 fuera, max 87.2 enclaves turísticos), `pct_menor_18+pct_mayor_65 ≤ 100` (0 casos), `dist_min_* > 0`, `area_km2 > 0`, `densidad_real = pob/area` coherente (discrepancias >5% solo por redondeo en secciones <0.2 km², EPSG:32628).
* **Descriptiva (§6):** pob μ1593 σ672, renta hogar μ36.2k σ8.9k, Gini μ29.2, envejecimiento μ175.5, densidad μ8849 σ11927 (cola urbana → justifica `log1p`).
* **Skew + `log1p` (§10, §13, §15–16):** umbral skew >1.0 sobre 29 analíticas (excluye `area/perimetro/densidad_hab` duplicada); ~20 transformadas (top `total_viviendas`, `dens_paradas`, `dens_hospitales`, `dist_parada`).
* **KPIs (§11):** 4 válidos — `estimated_persons_per_household` (renta_hogar/renta_persona), `relative_island_density`, `relative_island_household_wealth` (relativos a media de isla), `healthcare_offer_demand_ratio` (con fix /100). Excluidos `isolation_index_normalized`, `wealth_access_mismatch_score` (unidades incompatibles).
* **Correlación Spearman (§14):** sin `_log1p`, |ρ|>0.95; 1 sola versión por concepto (solo `densidad_real`, 1 renta/educación/extranjería) para evitar multicolinealidad.
* **Feature-set §17 (canónico, 18 vars):** 14 temáticas (salud 4, transporte 2, demografía 7, educación 1 — 10 en versión `_log1p` si existe) + 4 KPIs, `StandardScaler` → `X_scaled (1581,18)`. Excluye economía directa, OHE `isla` (leakage identidad), IDs/geometría. Sin nulos.
* **K-Means exploratorio (§17b–17c, §20–24):** codo K3–K4; Sil/DB K=2 0.2368/1.5476 · K=3 0.2048/1.6168 · **K=4 0.1807/1.7022** · K=5 0.1596/1.8649. **Decisión K=4 por criterio territorial** (K=2/3 colapsan periferias; K=5 deja <10 secciones en Hierro/Gomera/La Palma; OCDE 2008/Eurostat 2018: núcleo/periurbano/rural-envejecido/periferia-aislada). Perfiles §21 + radar §23 = hipótesis PG1/PG2 para el benchmark. AE/PCA sobre latente = plantillas (viven en nb 02).

### 02 — Modelado y benchmark AE vs PCA vs K-Means vs XGBoost (`notebooks/02_modelado_benchmark.ipynb`)

Parte de `dataset_final.csv` + **réplica exacta** de derivaciones EDA (4 KPIs + `log1p` skew>1.0) y mismo feature-set 18. Comparativa principal **AE vs PCA** (mismo `X_scaled`, misma dimensión latente); K-Means post-hoc sobre cada latente; XGBoost solo como techo supervisado.

* **Setup (§0–1):** `RANDOM_STATE=42`, `DEVICE cuda/cpu` (PyTorch) + `XGB_DEVICE`, `StandardScaler`, etiqueta proxy XGBoost `renta_neta_media_persona[_log1p]`, sin leakage (renta/gini/pobreza fuera de X).
* **Pesos espaciales island-aware (§2):** k-NN k=5 con distancia infinita inter-islas + verificación; base de todo Moran/LISA (contigüidad estándar no válida en archipiélago).
* **Autoencoder (§3–3.1, modelo central):** encoder 18→hidden→latente + decoder simétrico, BatchNorm, ReLU parametrizable, MSE. **Random Search** 15 combos (`latent_dim [2,3,5]`, `hidden [8,16,32]`, `activation [relu,tanh,leaky_relu]`, `lr [1e-2,1e-3,5e-4]`, 250 epochs) con **criterio Moran's I medio** (no MSE), reentreno final 500 epochs + curva pérdida.
* **PCA (§4, baseline lineal):** mismo `n_components=LATENT_DIM_FINAL`; PC1 como Índice de Acceso de referencia + varianza explicada.
* **K-Means (§5):** K óptimo por Silhouette independiente por espacio (rango 2–8) + Silhouette/DB finales → `cluster_ae`, `cluster_pca`.
* **XGBoost (§6–6.3):** RFE (DecisionTree, conserva ~mitad vars) para probar si accesibilidad/demografía predicen renta sin pobreza; **Spatial Island K-Fold** (cada isla ≥15 secciones = fold test nunca visto; Roberts et al. 2017) + contraste split aleatorio (cuantifica inflación por autocorrelación) + importancia variables. GPU `hist/cuda` si disponible.
* **Validación comparativa (§7):** Moran global medio por dimensión AE vs PCA + test permutación; **LISA** (High-High/Low-Low/atípicos, p<0.05) sobre dim-0 AE/PCA → `lisa_cuadrante_ae/pca`; Silhouette/DB secundarios; **bootstrap** 100×80% (Spearman entre iteraciones; AE reducido a 30×100 epochs por coste); **ablación** por dimensión temática (caída Moran al retirar salud/transporte/demografía/educación/KPIs); sesgo-varianza §10.1; Random Forest valida predictibilidad clusters (§7.5); Fuzzy C-Means + `zona_transicion` (max_memb<0.7) para bordes difusos (§7.6).
* **Mapas (§8):** Folium archipiélago + **Lanzarote** (zoom 11, filtro exacto `isla==`) por estrategia, mapa LISA, mapa renta continua, paneles estáticos `panel_comparativo_ae_pca.png` / `panel_comparativo_lanzarote.png` + radares por clúster (1 var por dimensión + perfiles).
* **Tablas finales (§9) y exports (§10):** `tabla_comparativa_final.csv` (AE vs PCA: Moran, K, Sil, DB, estabilidad + p-permutación), tabla XGBoost aparte (RMSE/R², no comparable), resumen ejecutivo + discusión honesta (si p>0.05, equivalencia espacial = resultado publicable; PCA puede ganar en subgeografías lineales). Guarda en `data/outputs/`: `resultados_modelado.csv`, `latent_space_autoencoder.csv`, `pca_components.csv`, `tabla_comparativa_final.csv`, `analisis_ablacion.csv`, `busqueda_hiperparametros_ae.csv`, `mejores_hiperparametros_ae.json`, `rfe_ranking_variables.csv`, `xgboost_spatial_island_kfold.csv` + PNGs. Limitaciones §12: R² negativo en islas menores (insularidad = límite estructural), paradoja ablación (renta/demografía = ruido espacial vs accesibilidad suave), island-aware imperativo, AE optimizado por Moran no MSE.

---

## 🚀 Guía de Uso y Ejecución

Los scripts deben ejecutarse de forma **estrictamente secuencial** para garantizar la correcta propagación de dependencias espaciales y tabulares:

```bash
python scripts/01_descarga_geometria_e_infraestructuras.py
python scripts/02_descarga_censo_2021_ine.py
python scripts/03_descarga_adrh_renta_ine.py
python scripts/04_descarga_renta_media_hogar.py
python scripts/05_poblacion_demografia.py
python scripts/06_calculo_areas_e_integracion_censo2021.py
python scripts/07_fusion_dataset_final.py
```

Después, análisis y modelado en orden:

```bash
# 01_eda.ipynb → valida dataset_final, genera feature-set 18 (X_scaled) + hipótesis K=4
# 02_modelado_benchmark.ipynb → Random Search AE, PCA, K-Means, XGBoost + Moran/LISA/bootstrap/ablación + mapas + exports a data/outputs/
```

### Verificación de Resultados
Para validar rápidamente la integridad de los datos generados:

```python
import pandas as pd
from pathlib import Path

csv_path = Path("data/outputs/dataset_final.csv")
df = pd.read_csv(csv_path, dtype={"CUSEC": str})
assert df.shape == (1581, 36) and df.isna().sum().sum() == 0
assert df["CUSEC"].str.len().eq(10).all() and not df["CUSEC"].duplicated().any()
print(f"✅ dataset_final OK: {df.shape} nulos=0")
```

---

## 🤝 Contribución

Las contribuciones al proyecto son bienvenidas. Si deseas proponer mejoras, correcciones metodológicas o nuevas capas analíticas:

1. **Haz un Fork** del repositorio.
2. **Crea una rama** para tu nueva funcionalidad (`git checkout -b feature/nueva-mejora`).
3. **Realiza tus commits** asegurando la modularidad y buenas prácticas (`git commit -m 'Añadida nueva métrica de accesibilidad'`).
4. **Sube los cambios** a tu rama (`git push origin feature/nueva-mejora`).
5. Abre un **Pull Request** detallando los cambios introducidos.

---

## 📄 Licencia

Este proyecto se encuentra distribuido bajo los términos de la **Licencia MIT**. Consulta el fichero [LICENSE](LICENSE) para más detalles.
