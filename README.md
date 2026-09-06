# Análisis de Accesibilidad a Recursos Públicos en Canarias y Propuesta de Mejora en Zonas Vulnerables

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![GeoPandas](https://img.shields.io/badge/GeoPandas-Spatial-green.svg)
![OSMnx](https://img.shields.io/badge/OSMnx-OpenStreetMap-orange.svg)
![INE API](https://img.shields.io/badge/INE-OpenData-red.svg)
![TFE](https://img.shields.io/badge/TFE-Trabajo%20Fin%20de%20Estudios-purple.svg)

## 📌 Descripción del Proyecto
Este repositorio contiene el desarrollo técnico y metodológico correspondiente al **Trabajo Fin de Estudios (TFE)** enfocado en analizar el acceso espacial a recursos y servicios públicos (sanidad, educación, transporte y bienestar social) en el archipiélago canario, identificando áreas vulnerables y proponiendo optimizaciones basadas en datos geoespaciales y sociodemográficos.

---

## ⚙️ Entorno y Requisitos

Para la ejecución de los scripts de procesamiento y análisis, se recomienda utilizar un entorno virtual de Python con las siguientes librerías geoespaciales y de análisis de datos:

### Dependencias Principales
* `python` (>= 3.10)
* `geopandas`
* `pandas`
* `osmnx`
* `requests`

### Instalación del Entorno
```bash
# Crear y activar entorno virtual
python -m venv venv
# En Windows:
.\venv\Scripts\Activate

# Instalar dependencias necesarias
pip install pandas geopandas osmnx requests
```

---

## 🛠️ Pipeline de Datos (`scripts/`)

La carpeta `scripts/` contiene los scripts modulares en orden secuencial (`01` a `06`) encargados de la adquisición, limpieza y enriquecimiento de los datos geoespaciales y sociodemográficos de Canarias (Provincias 35 y 38):

| Orden | Script | Descripción Funcional |
| :---: | :--- | :--- |
| **01** | `01_descarga_geometria_e_infraestructuras.py` | Descarga la geometría oficial de secciones censales de Canarias y extrae Puntos de Interés (POIs) de OpenStreetMap (hospitales, centros de salud, farmacias, colegios, paradas de autobús) calculando distancias mínimas y accesibilidad. |
| **02** | `02_descarga_censo_2021_ine.py` | Descarga indicadores socioeconómicos detallados del Censo 2021 (empleo, actividad, paro, educación superior y características de vivienda) a nivel de sección censal mediante la API del INE. |
| **03** | `03_descarga_adrh_renta_ine.py` | Descarga capas del Atlas de Distribución de Renta de los Hogares (ADRH INE), incluyendo índice de Gini, porcentaje de salario sobre renta bruta, pensiones y distribución de renta P80/P20. |
| **04** | `04_descarga_renta_media_hogar.py` | Obtiene la renta neta media por persona y hogar, así como indicadores de riesgo de pobreza e ingresos bajos. |
| **05** | `05_poblacion_demografia.py` | Obtiene la población total, densidad demográfica, porcentaje de población extranjera, índice de envejecimiento y tasa de dependencia. |
| **06** | `06_calculo_areas_y_tasa_paro.py` | Calcula la superficie territorial en $km^2$ de cada sección censal mediante proyección UTM 28N e integra la tasa de desempleo oficial del Censo INE. |

---

## 📁 Estructura de Datos e Inputs (`data/` y directorios de salida)

Durante la ejecución del pipeline de scripts, se generan y almacenan los siguientes recursos geoespaciales y tabulares para el análisis del TFE:

* **`data/geo/`**: Almacena las capas vectoriales base, destacando `secciones_canarias.gpkg` (delimitación oficial de secciones censales con metadatos insulares y centroides) y `pois_canarias.gpkg` (infraestructuras públicas y servicios extraídos de OpenStreetMap).
* **`data/raw/`**: Contiene ficheros intermedios de métricas y distancias calculadas a recursos (p.ej., `distancias_servicios.csv`).
* **Directorios temáticos (`adrh_canarias/`, `renta_hogar/`, `poblacion_canarias/`, `data/outputs/`)**: Almacenan los datasets descargados y procesados de fuentes oficiales (INE, Censo 2021, ADRH) en formatos `.csv`, `.gpkg` y `.geojson` listos para el análisis espacial y modelado estadístico.

---

## 🚀 Instrucciones de Ejecución

Los scripts deben ejecutarse de forma secuencial para garantizar la correcta generación de las dependencias de datos espaciales:

```bash
python scripts/01_descarga_geometria_e_infraestructuras.py
python scripts/02_descarga_censo_2021_ine.py
python scripts/03_descarga_adrh_renta_ine.py
python scripts/04_descarga_renta_media_hogar.py
python scripts/05_poblacion_demografia.py
python scripts/06_calculo_areas_y_tasa_paro.py
```
