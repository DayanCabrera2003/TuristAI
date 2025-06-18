# TuristIA: Asistente Inteligente para Planificación de Viajes Turísticos

## Introducción

El proyecto consiste en diseñar e implementar un sistema funcional que integre conocimientos de Inteligencia Artificial, Simulación y Sistemas de Recuperación de Información. El objetivo es aplicar los fundamentos teóricos y prácticos estudiados durante el semestre, utilizando tecnologías avanzadas como una arquitectura multiagente y el modelo Retrieve-Augmented Generation (RAG).

## Integrantes

- Nombre: Dayan Cabrera Corvo, Grupo: 311 
- Nombre: Eveliz Espinaco Milian, Grupo: 311  
- Nombre: Michell Viu Ramirez, Grupo: 311  

---

## Descripción del Proyecto

TuristIA es una plataforma inteligente que asiste a los usuarios en la planificación de viajes turísticos, proporcionando recomendaciones personalizadas mediante el uso de agentes inteligentes y técnicas de recuperación de información aumentada. El sistema simula escenarios turísticos y responde a consultas utilizando información relevante y actualizada.

### Contexto del Dominio

Nuestro sistema se enfoca en el dominio de **guía turístico**, con énfasis en la recomendación de lugares, actividades y rutas en Cuba. El asistente responde preguntas como un guía turístico profesional, integrando información de fuentes confiables y actualizadas.

---

## Tecnologías y APIs Utilizadas

- **Python 3.10+** (recomendado 3.10 o superior)
- **Streamlit**: Interfaz web interactiva para el usuario.
- **Selenium**: Automatización de navegación web para crawling dinámico.
- **spaCy**: Procesamiento de lenguaje natural (modelo `es_core_news_sm`).
- **NLTK**: Sinónimos y procesamiento semántico.
- **Sentence Transformers**: Embeddings para búsqueda semántica.
- **duckduckgo-search**: API para búsquedas web rápidas.
- **Google Generative AI (Gemini API)**: Generación de respuestas naturales.
- **APIs externas**:
    - **Google Gemini API**: Para generación de texto y respuestas enriquecidas.
    - **(Opcional) Google Maps API**: Para geolocalización y mapas (ver planner/mapaCuba.py).
    - **(Opcional) Weather.com API**: Para pronósticos del tiempo (puedes integrar si lo deseas).

---

## Estructura Técnica y Componentes
```
TuristAI/
├── project/
│   └── src/
│       └── agents/
│           ├── chat_bot.py
│           ├── rag/ 
│           ├── planner/
│           ├── pages/
│           ├── data/
│           ├── data_dynamic/
│           ├── data_formulario/
│           ├──utils/
│           ├── crawlers/
├── requirements.txt
└── README.md
|── .gitignore
|── startup.sh
```

### Arquitectura Multiagente

El sistema está compuesto por varios agentes especializados:
- **Agente de Recuperación (RAG)**: Recupera información relevante de la base de datos y de la web.
- **Agente de Planificación**: Genera itinerarios personalizados usando metaheurísticas.
- **Agente de Crawling**: Obtiene información actualizada de sitios turísticos y fuentes externas.
- **Agente de Interfaz**: Gestiona la interacción con el usuario vía Streamlit.

### Retrieve-Augmented Generation (RAG)

- Implementado en [`agents/rag/rag.py`](project/src/agents/rag/rag.py).
- Recupera fragmentos relevantes usando embeddings y búsqueda semántica.
- Enriquece el prompt del modelo generativo con contexto real y actualizado.

### Metaheurísticas

- Implementadas en [`agents/planner/metaheuristicas.py`](project/src/agents/planner/metaheuristicas.py).
- Incluye Algoritmo Genético (GA), Enjambre de Partículas (PSO) y Colonia de Hormigas (ACO) para optimizar itinerarios turísticos según preferencias y restricciones del usuario.

### Sistema de Crawlers

- Crawlers tradicionales y dinámicos en [`agents/Crawler/crawler2.py`](project/src/agents/Crawler/crawler2.py).
- Scrapper especializado para cubatravel.cu en [`agents/Crawler/Scrapper.py`](project/src/agents/Crawler/Scrapper.py).
- Permite obtener información actualizada de sitios turísticos, hoteles, actividades y más.

---

## Requisitos

### Software

- **Python**: >= 3.10 (recomendado 3.10 o superior)
- **pip**: >= 21.0

### Hardware

- 4 GB RAM mínimo (8 GB recomendado para crawling intensivo)
- Conexión a Internet para crawling y uso de APIs externas

### Configuraciones Previas

- **API Key de Google Gemini**: Necesaria para la generación de respuestas. Debes obtenerla en [Google AI Studio](https://aistudio.google.com/app/apikey) y colocarla en el archivo de configuración o como variable de entorno `GEMINI_API_KEY`.
- (Opcional) **API Key de Google Maps**: Para funcionalidades de geolocalización.
- (Opcional) **API Key de Weather.com**: Para pronósticos del tiempo.

---

## Instalación

1. Clona el repositorio:

    ```bash
    git clone https://github.com/DayanCabrera2003/TuristAI
    cd TuristAI
    ```

2. Instala las dependencias:

    ```bash
    pip install -r requirements.txt
    ```

3. Descarga los modelos de spaCy y nltk necesarios:

    ```bash
    python -m spacy download es_core_news_sm
    python -c "import nltk; nltk.download('omw-1.4'); nltk.download('wordnet')"
    ```

4. Configura tu API Key de Google Gemini:

    - Crea un archivo `.env` en la raíz del proyecto con el contenido:
      ```
      GEMINI_API_KEY=tu_api_key_aqui
      ```
    - O exporta la variable en tu terminal:
      ```bash
      export GEMINI_API_KEY=tu_api_key_aqui
      ```

---

## Ejecución

### Opción 1: Usando el script de inicio

Desde la raíz del proyecto, ejecuta:

```bash
source ~/envs/global_env/bin/activate  # (si usas entorno virtual)
./startup.sh
```

Esto lanzará la interfaz web de TuristIA en [http://localhost:8501](http://localhost:8501).

### Opción 2: Manualmente

Desde la raíz del proyecto:

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/project/src
streamlit run ./project/src/agents/chat_bot.py
```

---

## Ejemplo de Consulta

Puedes realizar consultas como:

```
¿Qué lugares turísticos puedo visitar en La Habana?
```

El sistema responderá con los mejores lugares turísticos en La Habana, basándose en información actualizada y relevante.

---

## Notas Adicionales

- **Dominio**: El sistema está orientado a la asistencia turística, cubriendo recomendaciones de lugares, actividades, rutas y consejos prácticos para viajeros en Cuba.
- **Extensibilidad**: Puedes adaptar el sistema para otros destinos turísticos agregando nuevas fuentes de datos y ajustando los crawlers.
- **Privacidad**: No almacena datos personales de los usuarios. Solo utiliza información pública y APIs externas.

---

## Contacto

Para dudas, sugerencias o reportes de errores, contacta a los integrantes del equipo o abre un issue en el repositorio.

---

¡Gracias por usar TuristIA!