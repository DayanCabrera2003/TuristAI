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
