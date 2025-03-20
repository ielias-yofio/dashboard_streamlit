"# Aplicación de KPIs de Riesgo - YoFio

Esta aplicación de Streamlit está diseñada para mostrar los KPIs de riesgo de YoFio, proporcionando visualizaciones y análisis útiles para la gestión del riesgo.

## Autor
**Erick Santillan**

## Estructura del Proyecto

El proyecto está organizado de la siguiente manera:

yofio/
│
├── metrics.py # Fórmulas de las métricas
├── utils.py # Funciones utilitarias para no repetir código
│
├── KPIS.py # Página principal con los KPIs generales
│
└── pages/
├── Cortes.py # Saldo por bucket
├── Rolls.py # Métricas de los rodamientos de saldos entre buckets
└── Cosechas.py # Métricas vistas por cohort

markdown


### Descripción de los Módulos

- **`yofio/metrics.py`**: Contiene las fórmulas de las métricas utilizadas en la aplicación para calcular diversos indicadores de riesgo.

- **`yofio/utils.py`**: Incluye funciones utilitarias que se usan en varias páginas para evitar la repetición de código.

### Descripción de las Páginas

1. **Página Principal (`KPIS.py`)**: Muestra un resumen de los KPIs generales relacionados con el riesgo de YoFio.

2. **Página de Cortes (`pages/Cortes.py`)**: Presenta el saldo por bucket, proporcionando una visión clara de la distribución de saldos.

3. **Página de Rolls (`pages/Rolls.py`)**: Muestra las métricas de los rodamientos de saldos entre buckets, ayudando a entender las transiciones de los saldos.

4. **Página de Cosechas (`pages/Cosechas.py`)**: Proporciona métricas pero vistas por cohort, lo que permite analizar el desempeño a lo largo del tiempo para diferentes grupos.

## Cómo Ejecutar la Aplicación

Para ejecutar la aplicación, sigue estos pasos:

1. Clona el repositorio y navega al directorio del proyecto.
2. Instala las dependencias necesarias (puedes usar `pip install -r requirements.txt` si hay un archivo de requisitos).
3. Ejecuta la aplicación con el siguiente comando:
```bash
streamlit run KPIS.py
```

Abre tu navegador y navega a http://localhost:8501 para ver la aplicación en acción.

¡Esperamos que esta aplicación sea de gran utilidad para el análisis de los KPIs de riesgo en YoFio!"
