import numpy as np
import pickle
import os
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

local_model = SentenceTransformer('all-MiniLM-L6-v2')
class ChatUtils:
    def __init__(self,embeddings_path="./project/src/agents/data/embeddings.pkl"):
        # Inicializa el modelo de embeddings y el modelo de Gemini
        
        with open(embeddings_path, "rb") as f:
            self.store_vectors = pickle.load(f)
        
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    
        # self.knowledge_base = []
        # self.store_vectors=self.update_knowledge_base(self.knowledge_base, chunk_size=20, overlap_size=5)
    
    def get_embedding(self, text):
        """
        Computa un embedding para un texto dado utilizando el modelo sentence-transformers/all-MiniLM-L6-v2.

        Args:
            text (str): Texto para el cual se desea generar un embedding.

        Returns:
            list: Embedding del texto dado.
        """
        vector = local_model.encode(text)
        return vector.tolist()

    def split_text_into_chunks(self, text, window_size=20, overlap_size=5):
        """
        Divide el texto en chunks con ventanas deslizantes.

        Args:
            - text (str): El texto a dividir.
            - window_size (int): El tamaño de cada chunk.
            - overlap_size (int): El tamaño de la superposición entre chunks.

        Return: 
            list<str>: Lista de chunks asociada a los subtextos.
        """
        chunks = []
        if text is None or len(text) == 0:
            return chunks
        words = text.split()
        start = 0
        while start < len(words):
            end = start + window_size
            chunk = ' '.join(words[start:end])
            chunks.append(chunk)
            if end >= len(words):
                break
            start += window_size - overlap_size
        return chunks

    def compute_embeddings_for_text(self, text, chunk_size=20, overlap_size=5):
        """
        Computa los embeddings de un texto usando ventanas deslizantes.

        Args:
            text (str): El texto a procesar.
            chunk_size (int): El tamaño de cada chunk.
            overlap_size (int): El tamaño de la superposición entre chunks.

        Return: list<tuple>: Lista de tuplas (embedding, chunk) donde cada tupla contiene el embedding y el chunk asociado.
        """
        chunks = self.split_text_into_chunks(text, window_size=chunk_size, overlap_size=overlap_size)
        embeddings = []
        for chunk in chunks:
            vector = self.get_embedding(chunk)
            if vector is not None:
                embeddings.append((vector, chunk))
        return embeddings

    def update_knowledge_base(self, texts, chunk_size=50, overlap_size=10):
        """
        Actualiza la base de conocimiento con los embeddings de los textos dados.

        Args:
            texts (list): Lista de textos para procesar.

        Return: 
            list: Lista de embeddings generados.
        """
        store_vectors = []
        for text in texts:
            store_vectors.extend(self.compute_embeddings_for_text(text, chunk_size=chunk_size, overlap_size=overlap_size))
        return store_vectors

    def retrieve(self, query, store_vectors, top_k=3):
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
        query_vector = self.get_embedding(query)
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

    def prompt_gen(self, query, store_vectors, top_k=10):
        """
        Function that implements a Retrieval-Augmented Generation (RAG) system.

        Args:
            query (str): The query for which information should be retrieved.

        Returns:
            str: prompt that integrates the retrieved information and the query.
        """
        # 1. Recuperar los fragmentos más relevantes usando el recuperador
        retrieved_chunks = self.retrieve(query, store_vectors, top_k=top_k)

        # 2. Construir el prompt integrando los fragmentos recuperados y la consulta
        context = ".".join(retrieved_chunks)
        prompt = (
            "A continuación tienes información relevante que puede ayudarte a responder la pregunta del usuario."
            "Si la respuesta está en la información proporcionada, úsala. "
            "Si no encuentras la respuesta completa ahí, responde usando tu propio conocimiento general, "
            "pero intenta siempre ser útil y específico.\n\n"
            f"Información relevante:\n{context}\n\n"
            f"Pregunta del usuario: {query}\n"
            f"Respuesta:"
        )
        return prompt
    
    def ask(self, query, top_k=10):
        """
        Llama al modelo de lenguaje con la query y devuelve la respuesta.
        """
        prompt = self.prompt_gen(query,self.store_vectors, top_k=top_k)
        response = self.gemini_model.generate_content(prompt)
        return response.text
