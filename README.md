# TuristIA: Asistente Inteligente para Planificación de Viajes Turísticos

## Introducción

El proyecto consiste en diseñar e implementar un sistema funcional que integre conocimientos de Inteligencia Artificial, Simulación y Sistemas de Recuperación de Información. El objetivo es aplicar los fundamentos teóricos y prácticos estudiados durante el semestre, utilizando tecnologías avanzadas como una arquitectura multiagente y el modelo Retrieve-Augmented Generation (RAG).

## Integrantes

- Nombre: Dayan Cabrera Corvo, Grupo: 311 
- Nombre: Eveliz Espinaco Milian, Grupo: 311  
- Nombre: Michell Viu Ramirez, Grupo: 311  

## Descripción del Proyecto

TuristIA es una plataforma inteligente que asiste a los usuarios en la planificación de viajes turísticos, proporcionando recomendaciones personalizadas mediante el uso de agentes inteligentes y técnicas de recuperación de información aumentada. El sistema simula escenarios turísticos y responde a consultas utilizando información relevante y actualizada.

## Tecnologías Utilizadas

El sistema está implementado en Python y requiere los siguientes paquetes, especificados en el archivo [requirements.txt](./requirements.txt):

## Instalación

1. Clona el repositorio:

    ```bash
    git clone https://github.com/DayanCabrera2003/TuristAI
    cd TuristIA
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

## Estructura del Proyecto

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

## Ejemplo de Consulta

Puedes realizar consultas como:
`
¿Qué lugares turísticos puedo visitar en La Habana?
`
El sistema responderá con los mejores lugares turísticos en La Habana, basándose en información actualizada y relevante.
