import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from project.src.agents.rag import rag
import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import numpy as np
import matplotlib.pyplot as plt

# Instancia de ChatUtils
chat_utils = rag.ChatUtils()

# 30 preguntas y respuestas sobre turismo en Cuba
preguntas_respuestas = [
    {
        "pregunta": "¿Cuáles son los principales destinos turísticos en Cuba?",
        "respuesta": "La Habana, Varadero, Trinidad, Cayo Coco y Santiago de Cuba son algunos de los principales destinos turísticos en Cuba."
    },
    {
        "pregunta": "¿Qué actividades se pueden hacer en Varadero?",
        "respuesta": "En Varadero se pueden disfrutar de playas, deportes acuáticos, excursiones en catamarán y visitas a cuevas."
    },
    {
        "pregunta": "¿Cuál es la mejor época para visitar Cuba?",
        "respuesta": "La mejor época para visitar Cuba es de noviembre a abril, durante la temporada seca."
    },
    {
        "pregunta": "¿Qué moneda se utiliza en Cuba para turistas?",
        "respuesta": "La moneda principal para turistas es el Peso Cubano (CUP), aunque algunos lugares aceptan dólares estadounidenses y euros."
    },
    {
        "pregunta": "¿Es seguro viajar a Cuba como turista?",
        "respuesta": "Cuba es generalmente un país seguro para turistas, aunque se recomienda tomar precauciones normales."
    },
    {
        "pregunta": "¿Qué platos típicos se pueden probar en Cuba?",
        "respuesta": "Algunos platos típicos son ropa vieja, congrí, yuca con mojo, lechón asado y tostones."
    },
    {
        "pregunta": "¿Qué documentos necesito para viajar a Cuba?",
        "respuesta": "Se necesita pasaporte vigente, visa turística (tarjeta de turista) y seguro médico."
    },
    {
        "pregunta": "¿Cuáles son las mejores playas de Cuba?",
        "respuesta": "Varadero, Cayo Coco, Cayo Santa María, Playa Ancón y Guardalavaca son algunas de las mejores playas."
    },
    {
        "pregunta": "¿Qué lugares históricos puedo visitar en La Habana?",
        "respuesta": "El Malecón, el Capitolio, la Habana Vieja, la Plaza de la Revolución y el Castillo del Morro."
    },
    {
        "pregunta": "¿Cómo es el clima en Cuba?",
        "respuesta": "Cuba tiene clima tropical, con temperaturas cálidas todo el año y una temporada de lluvias de mayo a octubre."
    },
    {
        "pregunta": "¿Qué souvenirs típicos se pueden comprar en Cuba?",
        "respuesta": "Tabacos, ron, artesanías, camisetas y obras de arte local."
    },
    {
        "pregunta": "¿Dónde se puede practicar buceo en Cuba?",
        "respuesta": "En lugares como Jardines de la Reina, Cayo Largo, Varadero y Playa Girón."
    },
    {
        "pregunta": "¿Qué transporte público hay en Cuba para turistas?",
        "respuesta": "Existen taxis, autobuses turísticos y coches de alquiler."
    },
    {
        "pregunta": "¿Cuáles son los principales festivales culturales en Cuba?",
        "respuesta": "El Carnaval de Santiago, el Festival del Habano y el Festival Internacional de Jazz de La Habana."
    },
    {
        "pregunta": "¿Dónde puedo alojarme en Cuba?",
        "respuesta": "Hoteles, casas particulares y resorts todo incluido."
    },
    {
        "pregunta": "¿Se puede usar internet en Cuba?",
        "respuesta": "Sí, pero el acceso es limitado y suele ser de pago en zonas Wi-Fi y hoteles."
    },
    {
        "pregunta": "¿Qué parques naturales se pueden visitar en Cuba?",
        "respuesta": "El Parque Nacional Viñales, Ciénaga de Zapata y Topes de Collantes."
    },
    {
        "pregunta": "¿Qué bebidas típicas hay en Cuba?",
        "respuesta": "El mojito, daiquirí, cuba libre y ron cubano."
    },
    {
        "pregunta": "¿Cuáles son los principales aeropuertos internacionales de Cuba?",
        "respuesta": "Aeropuerto Internacional José Martí (La Habana), Juan Gualberto Gómez (Varadero) y Frank País (Holguín)."
    },
    {
        "pregunta": "¿Qué excursiones se pueden hacer desde La Habana?",
        "respuesta": "Excursiones a Viñales, Playas del Este, Varadero y Cienfuegos."
    },
    {
        "pregunta": "¿Qué museos importantes hay en Cuba?",
        "respuesta": "Museo de la Revolución, Museo Nacional de Bellas Artes y Museo del Ron."
    },
    {
        "pregunta": "¿Cómo es la vida nocturna en Cuba?",
        "respuesta": "La vida nocturna es animada, con bares, discotecas y espectáculos de música en vivo."
    },
    {
        "pregunta": "¿Qué ciudades coloniales se pueden visitar en Cuba?",
        "respuesta": "Trinidad, Camagüey, Cienfuegos y Santiago de Cuba."
    },
    {
        "pregunta": "¿Qué opciones de turismo ecológico hay en Cuba?",
        "respuesta": "Senderismo, observación de aves y visitas a parques naturales."
    },
    {
        "pregunta": "¿Qué idioma se habla en Cuba?",
        "respuesta": "El idioma oficial es el español."
    }
]


def experimentar_rag():
    print("Iniciando experimentación RAG con 30 preguntas sobre turismo en Cuba...\n")
    resultados = []
    for idx, item in enumerate(preguntas_respuestas, 1):
        pregunta = item["pregunta"]
        respuesta_esperada = item["respuesta"]
        # Consulta al modelo RAG
        promp = chat_utils.prompt_gen(pregunta, chat_utils.store_vectors, top_k=30)
        respuesta_modelo=chat_utils.gemini_model.generate_content(promp).text.strip()
        resultados.append({
            "pregunta": pregunta,
            "respuesta_esperada": respuesta_esperada,
            "respuesta_modelo": respuesta_modelo
        })
        print(f"{idx}. Pregunta: {pregunta}")
        print(f"   Esperada: {respuesta_esperada}")
        print(f"   Modelo: {respuesta_modelo[:200]}...\n")  # Muestra solo los primeros 200 caracteres
        time.sleep(60)

    # Guardar resultados en un archivo para análisis posterior
    with open("project/src/agents/simulator/resultados_experimento_rag.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print("Resultados guardados en resultados_experimento_rag.json")

def calcular_similitud_respuestas(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        resultados = json.load(f)

    print("\nSimilitud coseno entre respuesta esperada y respuesta del modelo:\n")
    similitudes = {}
    for idx, item in enumerate(resultados, 1):
        pregunta = item["pregunta"]
        resp_esperada = item["respuesta_esperada"]
        resp_esperada2 = chat_utils.normalize_text(resp_esperada)
        resp_modelo = item["respuesta_modelo"]
        resp_modelo2 = chat_utils.normalize_text(resp_modelo)

        # Vectorización TF-IDF
        vectorizer = TfidfVectorizer().fit([resp_esperada2, resp_modelo2])
        vecs = vectorizer.transform([resp_esperada2, resp_modelo2])
        sim = cosine_similarity(vecs[0], vecs[1])[0][0]

        similitudes[str(idx)] = sim  # Guarda como string para compatibilidad JSON

        print(f"{idx}. Pregunta: {pregunta}")
        print(f"   Similitud coseno: {sim:.3f}")
        print(f"   Esperada: {resp_esperada}")
        print(f"   Modelo: {resp_modelo}\n")

    # Guardar similitudes en un JSON
    with open("project/src/agents/simulator/similitud_preguntas_rag.json", "w", encoding="utf-8") as f:
        json.dump(similitudes, f, ensure_ascii=False, indent=2)
    print("Similitudes guardadas en similitud_preguntas_rag.json")

if __name__ == "__main__":
    #experimentar_rag()
    # calcular_similitud_respuestas("project/src/agents/simulator/resultados_experimento_rag.json")

    def analisis_estadistico_similitud(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            similitudes = json.load(f)
        valores = [float(v) for v in similitudes.values()]
        media = np.mean(valores)
        mediana = np.median(valores)
        desviacion = np.std(valores)
        minimo = np.min(valores)
        maximo = np.max(valores)
        print("\nAnálisis estadístico de la similitud coseno:")
        print(f"  Media: {media:.3f}")
        print(f"  Mediana: {mediana:.3f}")
        print(f"  Desviación estándar: {desviacion:.3f}")
        print(f"  Mínimo: {minimo:.3f}")
        print(f"  Máximo: {maximo:.3f}")

        # Crear gráfico de barras
        plt.figure(figsize=(10, 5))
        plt.bar(range(1, len(valores) + 1), valores, color='skyblue')
        plt.axhline(media, color='red', linestyle='--', label=f"Media: {media:.2f}")
        plt.xlabel("Pregunta")
        plt.ylabel("Similitud coseno")
        plt.title("Similitud coseno por pregunta")
        plt.legend()
        plt.tight_layout()
        plt.savefig("project/src/agents/simulator/similitud_coseno_grafico.png")
        plt.show()

    # Llama a la función después de calcular las similitudes
    analisis_estadistico_similitud("project/src/agents/simulator/similitud_preguntas_rag.json")