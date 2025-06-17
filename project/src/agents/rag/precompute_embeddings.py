import pickle
from rag import ChatUtils

DATA_DIR = "./project/src/agents/data"
EMBEDDINGS_FILE = "./project/src/agents/data/embeddings.pkl"
DATA_FORMULARIO = "./project/src/agents/data_formulario"
EMBEDDINGS_FORMULARIO = "./project/src/agents/data_formulario/embeddings.pkl"


def main():
    print("Extrayendo textos de los JSON...")
    texts = ChatUtils.load_all_texts(DATA_DIR) #Cambia a DATA_FORMULARIO para cargar los datos del formulario
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