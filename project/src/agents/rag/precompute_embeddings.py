import os
import json
import pickle
from pathlib import Path
from sentence_transformers import SentenceTransformer
from rag import ChatUtils

DATA_DIR = "./project/src/agents/data"
EMBEDDINGS_FILE = "./project/src/agents/data/embeddings.pkl"
DATA_FORMULARIO = "./project/src/agents/data_formulario"
EMBEDDINGS_FORMULARIO = "./project/src/agents/data_formulario/embeddings.pkl"


def extract_texts_from_json(json_path):
    text=""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if "titulo" in data:
            text = data["titulo"]
           
        # fragmentos de cada sección
        if "secciones" in data:
            for seccion in data["secciones"]:
                if "fragmentos" in seccion:
                    lista_fragmentos = seccion["fragmentos"]
                    text += ".".join(lista_fragmentos)
        
    return ChatUtils.normalize_text(text)


def load_all_texts(data_dir):
    
    all_texts = []
    carpeta_base = Path(data_dir)
    
    if not carpeta_base.exists():
        raise FileNotFoundError(f"La carpeta {carpeta_base} no existe, no se pueden cargar los datos.")
    
    for archivo_json in carpeta_base.rglob('*.json'):
        try:
            text = extract_texts_from_json(archivo_json)
            all_texts.append(text)
        except json.JSONDecodeError:
            print(f"❌ Error: Archivo no es JSON válido - {archivo_json}")
        except Exception as e:
            print(f"⚠️ Error inesperado en {archivo_json}: {str(e)}")
    
    return all_texts


def main():
    print("Extrayendo textos de los JSON...")
    texts = load_all_texts(DATA_DIR) #Cambia a DATA_FORMULARIO para cargar los datos del formulario
    print(f"Total de fragmentos/textos: {len(texts)}")

    print("Inicializando ChatUtils...")
    chat_utils = ChatUtils()

    print("Calculando embeddings con chunking...")
    # Usa el método de tu clase para hacer chunking y embeddings
    embeddings = chat_utils.update_knowledge_base(
        texts, chunk_size=100, overlap_size=10)

    print(f"Guardando embeddings en {EMBEDDINGS_FILE} ...")

    with open(EMBEDDINGS_FILE, "wb") as f:  # Cambia a EMBEDDINGS_FORMULARIO para guardar datos del formulario
        pickle.dump(embeddings, f)

    print("¡Listo! Embeddings precalculados y guardados.")

if __name__ == "__main__":
    main()