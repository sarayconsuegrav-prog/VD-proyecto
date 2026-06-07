# Explorador OBIS en Streamlit

Aplicación interactiva desarrollada en Streamlit para consultar, limpiar y visualizar registros de biodiversidad marina desde la API pública de OBIS (Ocean Biodiversity Information System).

El proyecto permite explorar ocurrencias marinas con filtros por región y período, analizar composición biológica, revisar tendencias temporales, comparar sectores biológicos y navegar especies destacadas dentro de una interfaz visual orientada a análisis.

## Objetivo del proyecto

Transformar una consulta técnica a la API de OBIS en un dashboard más claro, visual y útil para exploración académica. En lugar de trabajar directamente con respuestas crudas de la API, la aplicación organiza la información en vistas que apoyan tareas de comparación, localización espacial, análisis temporal e interpretación taxonómica.

## Funcionalidades principales

- Consulta de datos desde la API de OBIS
- Filtros por región marina y período temporal
- Limpieza de registros antes de visualizarlos
- Mapa interactivo de ocurrencias geográficas
- Visualizaciones de composición biológica y diversidad
- Exploración de especies con apoyo visual
- Resumen de la consulta aplicada a la API

## Tecnologías usadas

- `Python`
- `Streamlit`
- `Pandas`
- `Plotly`
- `Pydeck`
- `Requests`

## Estructura del proyecto

```text
app.py
requirements.txt
README.md
.streamlit/
  config.toml
work/
  species_images/
run_app.bat
```
## Datos y procesamiento

La aplicación consume registros de ocurrencia marina desde OBIS y realiza un preprocesamiento básico para mejorar la calidad visual y analítica del dashboard. Entre las operaciones aplicadas están:

- validación de coordenadas geográficas
- normalización de profundidad y año
- eliminación de duplicados
- descarte de registros incompletos
- generación de atributos derivados como `taxon_group` y `sector`

Esto permite que las visualizaciones trabajen sobre una muestra más consistente y legible.

## Diseño del dashboard

El dashboard está organizado en pestañas para separar tareas analíticas:

- `General`: panorama inicial de la consulta
- `Mapa`: distribución geográfica y capas biológicas
- `Distribución`: composición, diversidad y relaciones comparativas
- `Especies`: tarjetas y navegación por especies destacadas
- `Datos/API`: vista de la consulta y registros utilizados

La interfaz utiliza una paleta visual de tonos marinos y fondos oscuros para mantener coherencia temática con el dominio de biodiversidad oceánica.

## Fuentes de datos

- [OBIS Data Access](https://obis.org/data/access/)
- [OBIS API](https://api.obis.org/)

## Autoría

Proyecto elaborado por:

- Saray Consuegra
- Ángel Pérez
