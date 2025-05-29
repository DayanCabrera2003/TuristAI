import numpy as np
from sentence_transformers import SentenceTransformer
# Importa el modelo preentrenado de Sentence Transformers
local_model = SentenceTransformer('all-MiniLM-L6-v2')


def get_embedding(text):
    """ Computa un embedding para un texto dado utilizando el modelo sentence-transformers/all-MiniLM-L6-v2.

    Args:
        text (str): Texto para el cual se desea generar un embedding.

    Returns:
        list: Embedding del texto dado.
    """
    
    vector = local_model.encode(text)
    return vector.tolist()



def split_text_into_chunks(text, window_size=20, overlap_size=5):
    """
    Divide el texto en chunks con ventanas deslizantes.
    
    Args:
        - text (str): El texto a dividir.
        - window_size (int): El tamaño de cada chunk.
        - overlap_size (int): El tamaño de la superposición entre chunks.
        
    Return: 
        list<str>: Lista de chunks asociada a los subtextos.
    """
    
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + window_size
        chunk = ' '.join(words[start:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        start += window_size - overlap_size
    return chunks



def compute_embeddings_for_text(text, chunk_size=20, overlap_size=5):
    """"
    Computa los embeddings de un texto usando ventanas deslizantes.
    
    Args:
        text (str): El texto a procesar.
        chunk_size (int): El tamaño de cada chunk.
        overlap_size (int): El tamaño de la superposición entre chunks.
        
    Return: list<tuple>: Lista de tuplas (embedding, chunk) donde cada tupla contiene el embedding y el chunk asociado.
    """
    
    chunks = split_text_into_chunks(text, window_size=chunk_size, overlap_size=overlap_size)
    embeddings = []
    for chunk in chunks:
        vector = get_embedding(chunk)
        if vector is not None:
            embeddings.append((vector, chunk))
    return embeddings



def update_knowledge_base(texts, chunk_size=20, overlap_size=5):
    """
    Actualiza la base de conocimiento con los embeddings de los textos dados.
    
    Args:
        texts (list): Lista de textos para procesar.
        
    Return: 
        list: Lista de embeddings generados.
    """
    store_vectors = []
    for text in texts:
        store_vectors.extend(compute_embeddings_for_text(text, chunk_size=chunk_size, overlap_size=overlap_size))
        
    return store_vectors



def retrieve(query,store_vectors, top_k=3):
    """
    Retrieve the top_k texts closest to the query based on Euclidean distance.

    Parameters:
        query (str): User's query.
        store_vectors (list of tuples (embedding, text)): Where each embedding is a vector and text is the original text.
        top_k (int): Amount of texts to retrieve.

    Returns:
        List of str: Texts closest to the query.
    """

 # Obtener el embedding de la consulta
    query_vector = get_embedding(query)
    if query_vector is None:
        return []
    query_vector = np.array(query_vector)

    # Calcular la distancia euclideana entre el embedding de la consulta y cada embedding almacenado
    distances = []
    for emb, text in store_vectors:
        emb_np = np.array(emb)
        dist = np.linalg.norm(query_vector - emb_np)
        distances.append(dist)

    # Obtener los índices de los top_k fragmentos más cercanos
    indices = np.argsort(distances)[:top_k]
    # Devolver los textos correspondientes
    return [store_vectors[i][1] for i in indices]
