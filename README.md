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

---

## 📑 Tabla de Contenidos

- [📌 Descripción del Proyecto](#-descripción-del-proyecto)
- [📂 Estructura del Repositorio](#-estructura-del-repositorio)
- [⚙️ Requisitos del Sistema y Dependencias](#️-requisitos-del-sistema-y-dependencias)
- [📥 Guía de Instalación](#-guía-de-instalación)
- [🛠️ Pipeline Metodológico (`scripts/`)](#️-pipeline-metodológico-scripts)
- [🚀 Guía de Uso y Ejecución](#-guía-de-uso-y-ejecución)
- [🤝 Contribución](#-contribución)
- [📄 Licencia](#-licencia)

---

## 📂 Estructura del Repositorio

```text
cap4-planteamiento/
│
├── data/
│   ├── censo2021_canarias.csv          # Datos crudos / procesados del Censo 2021 INE
│   ├── dataset_canarias.gpkg           # Capa vectorial unificada final
│   ├── dataset_canarias_raw.csv        # Dataset tabular integrado preliminar
│   ├── geo/
│   │   ├── secciones_canarias.gpkg     # Delimitación oficial de secciones censales y centroides
│   │   └── pois_canarias.gpkg          # Infraestructuras y Puntos de Interés (OSM)
│   ├── outputs/
│   │   ├── secciones_area_censo2021.gpkg / .csv # Áreas territoriales y tasas de paro
│   │   └── secciones_area_paro.gpkg / .csv     # Métricas de desempleo por sección
│   ├── raw/
│   │   ├── distancias_servicios.csv    # Distancias mínimas calculadas a servicios
│   │   └── overpass_manual/            # GeoJSON manuales de Overpass Turbo (<Isla>.geojson)
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

### Dependencias Principales (`requirements.txt`)
* `pandas` `>= 2.0.0`
* `geopandas` `>= 0.12.0`
* `osmnx` `>= 1.3.0`
* `requests` `>= 2.28.0`
* `shapely` `>= 2.0.0`
* `pyogrio` `>= 0.5.0`

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
| **06** | `06_calculo_areas_e_integracion_censo2021.py` | Proyecta las secciones censales a **ETRS89 / UTM Zona 28N** para calcular superficie en $km^2$ e integra la tasa de desempleo del Censo INE. <br>**Outputs:** `data/outputs/secciones_area_censo2021.gpkg`. |
| **07** | `07_fusion_dataset_final.py` | Fusiona todas las fuentes previas (geometría, distancias, demografía, censo, renta y ADRH) en un dataset integrado final, aplicando imputación de valores faltantes y cálculo de densidades. <br>**Outputs:** `data/outputs/dataset_final.gpkg`, `data/outputs/dataset_final.csv`. |

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

### Verificación de Resultados
Para validar rápidamente la integridad de los datos generados:

```python
import geopandas as gpd
from pathlib import Path

gpkg_path = Path("data/geo/secciones_canarias.gpkg")
if gpkg_path.exists():
    gdf = gpd.read_file(gpkg_path)
    print(f"✅ Capa cargada exitosamente.")
    print(f"📊 Total de secciones censales en Canarias: {len(gdf)}")
    print(f"🗺️ Sistema de Referencia de Coordenadas (CRS): {gdf.crs}")
else:
    print(f"❌ No se encontró el fichero en {gpkg_path}.")
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
