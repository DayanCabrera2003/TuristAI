import numpy as np
from pathlib import Path
import json
import pickle
import os
import shutil
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import unicodedata
import re
import spacy
from nltk.corpus import wordnet as wn
from Crawler.crawler2 import run_crawler
# from project.agents.Crawler.crawler2 import run_crawler
local_model = SentenceTransformer('all-MiniLM-L6-v2')
nlp = spacy.load("es_core_news_sm")

EMBEDDINGS_DYNAMIC_FILE = "./project/src/agents/data_dynamic/embeddings.pkl"
EMBEDDINGS_FORMULARIO_FILE = "./project/src/agents/data_formulario/embeddings.pkl"
EMBEDDINGS_FILE = "./project/src/agents/data/embeddings.pkl"
DATA_DYNAMIC_DIR = "./project/src/agents/data_dynamic"
# GEMINI_API_KEY = "AIzaSyDSWR4UwuJmxjvHrmw8t-V9PzUB5aV3QTU" #"AIzaSyA4642FobnkJVq5GcMmYKZsT_t2v0a_FuY"
GEMINI_API_KEY = "AIzaSyDxAqj0-PrXvI4vs4cedxQh1Wqf14OL29A"
# "AIzaSyDxAqj0-PrXvI4vs4cedxQh1Wqf14OL29A"
class ChatUtils:
    def __init__(self):
        
        # Inicializa el modelo de embeddings y el modelo de Gemini
        with open(EMBEDDINGS_FILE, "rb") as f:
            self.store_vectors = pickle.load(f)
        
        with open(EMBEDDINGS_FORMULARIO_FILE, "rb") as f:
            self.store_vectors_formulario = pickle.load(f)
        
        genai.configure(api_key=GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
    

    
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
    
    
    @staticmethod
    def normalize_text(text):
        """
        Normaliza un texto convirtiéndolo a minúsculas, eliminando tildes, signos de puntuación y espacios extra.
        Esta función es útil para estandarizar tanto las queries del usuario como los textos de la base de conocimiento
        antes de calcular embeddings o realizar búsquedas.

        Args:
            text (str): Texto de entrada a normalizar.

        Returns:
            str: Texto normalizado.
        """
        # Convierte a minúsculas
        text = text.lower()
        # Elimina tildes y acentos
        text = unicodedata.normalize('NFD', text)
        text = ''.join([c for c in text if unicodedata.category(c) != 'Mn'])
        # Elimina signos de puntuación
        text = re.sub(r'[^\w\s]', '', text)
        # Elimina espacios extra
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    @staticmethod
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
    
    @staticmethod
    def extract_texts_from_json_formulario(json_path):
        """
        Extrae textos relevantes de un archivo JSON con formato de hoteles para usar en embeddings o RAG.

        Args:
            json_path (str): Ruta al archivo JSON.

        Returns:
            list: Lista de textos combinados de cada entrada del JSON.
        """
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        textos = []
        for item in data:
            # Combina los campos más relevantes en un solo string
            texto = (
                f"Provincia: {item.get('Provincia', '')}."
                f"Nombre: {item.get('nombre', '')}. "
                f"Descripción: {item.get('descripcion', '')}. "
                f"Dirección: {item.get('direccion', '')}. "
                f"Tarifa: {item.get('tarifa', '')}. "
                f"Precio: {item.get('precio', '')}. "
                f"Estrellas: {item.get('estrellas', '')}. "
            )
            textos.append(texto)
        result = " ".join(textos)
        return ChatUtils.normalize_text(result)
    
    @staticmethod
    def clear_data_directory(data_dir):
        """
        Limpia el directorio de datos eliminando todos los archivos y subdirectorios.

        Args:
            data_dir (str): Ruta al directorio de datos a limpiar.
        """
        carpeta_base = Path(data_dir)
        if carpeta_base.exists():
            shutil.rmtree(carpeta_base)
        carpeta_base.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def load_all_texts(data_dir):
        
        all_texts = []
        carpeta_base = Path(data_dir)
        
        if not carpeta_base.exists():
            raise FileNotFoundError(f"La carpeta {carpeta_base} no existe, no se pueden cargar los datos.")
        
        for archivo_json in carpeta_base.rglob('*.json'):
            try:
                text = ChatUtils.extract_texts_from_json(archivo_json)
                all_texts.append(text)
            except json.JSONDecodeError:
                print(f"❌ Error: Archivo no es JSON válido - {archivo_json}")
            except Exception as e:
                print(f"⚠️ Error inesperado en {archivo_json}: {str(e)}")
        
        return all_texts
    
    @staticmethod
    def extract_keywords(text):
            """
            Extrae las palabras clave (sustantivos, verbos y adjetivos) de un texto en español usando spaCy.

            Args:
                text (str): Texto de entrada.

            Returns:
                list: Lista de lemas de palabras clave extraídas del texto.
            """
            doc = nlp(text)
            keywords = [token.lemma_ for token in doc if token.pos_ in ("NOUN", "VERB", "ADJ")]
            return keywords
    
    @staticmethod
    def get_synonyms(word, lang='spa', max_synonyms=2):
        
        """
        Obtiene una lista de sinónimos para una palabra dada usando WordNet.

        Args:
            word (str): Palabra para la cual buscar sinónimos.
            lang (str, optional): Idioma de WordNet. Por defecto 'spa' (español).
            max_synonyms (int, optional): Máximo número de sinónimos a devolver. Por defecto 2.

        Returns:
            list: Lista de sinónimos encontrados (máximo max_synonyms).
        """
        synonyms = set()
        for syn in wn.synsets(word, lang=lang):
            for lemma in syn.lemma_names(lang):
                if lemma != word:
                    synonyms.add(lemma.replace('_', ' '))
                if len(synonyms) >= max_synonyms:
                    break
            if len(synonyms) >= max_synonyms:
                break
        return list(synonyms)

    @staticmethod
    def expand_query_with_synonyms(query, max_synonyms=2):
        """
        Expande una consulta agregando palabras clave y hasta un número máximo de sinónimos por palabra clave.

        Args:
            query (str): Consulta original del usuario.
            max_synonyms (int, optional): Máximo número de sinónimos por palabra clave. Por defecto 2.

        Returns:
            str: Consulta expandida con palabras clave y sinónimos.
        """
        keywords = ChatUtils.extract_keywords(query)
        expanded = set(keywords)
        for kw in keywords:
            expanded.update(ChatUtils.get_synonyms(kw, max_synonyms=max_synonyms))
        # Devuelve la query original más las palabras clave y sus sinónimos
        return query + " " + " ".join(expanded)
    
    def is_continuation_of_previous_query(self,query, patterns_query, threshold=0.35):
        """
        Comprueba si una consulta es una continuación de la anterior basándose en patrones y similitud.

        Args:
            query (str): Consulta actual del usuario.
            patterns_query (list): Lista de patrones de consultas anteriores.
            threshold (float): Umbral de similitud para considerar que es una continuación.

        Returns:
            bool: True si la consulta es una continuación, False en caso contrario.
        """
        
        if not patterns_query:
            return False
        
        store_vectors = self.update_knowledge_base(patterns_query, chunk_size=15, overlap_size=5)
        query_norm = ChatUtils.normalize_text(query)
        query_vector = self.get_embedding(query_norm)
        
        if query_vector is None:
            return False
        
        query_vector = np.array(query_vector)
        distances = []
        for emb, text in store_vectors:
            emb_np = np.array(emb)
            dist = np.linalg.norm(query_vector - emb_np)
            distances.append((dist,text))
        if any(dist < threshold for dist, _ in distances):
            return True
        return False


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
            distances.append((dist,text))

        # Obtener los índices de los top_k fragmentos más cercanos
        # indices = np.argsort(distances)[:top_k]
        distances.sort(key=lambda x: x[0])
        # Devolver los textos correspondientes
        # return [store_vectors[i][1] for i in indices]
        return distances[:top_k]

    def prompt_gen(self, query, store_vectors, top_k=10, distance_threshold=0.7):
        """
        Function that implements a Retrieval-Augmented Generation (RAG) system.

        Args:
            query (str): The query for which information should be retrieved.

        Returns:
            str: prompt that integrates the retrieved information and the query.
        """
        # 1. Recuperar los fragmentos más relevantes usando el recuperador
        query_norm = ChatUtils.normalize_text(query)
        # expanded_query = ChatUtils.expand_query_with_synonyms(query, max_synonyms=2)
        retrieved = self.retrieve(query_norm, store_vectors, top_k=top_k)
        
        if all(dist > distance_threshold for dist, _ in retrieved):
            # Ejecuta tu crawler dinámico aquí
            print("⚠️ Contexto insuficiente, ejecutando crawler dinámico...")
            run_crawler(query)
            texts = ChatUtils.load_all_texts(DATA_DYNAMIC_DIR)
            embeddings = self.update_knowledge_base(
                     texts, chunk_size=100, overlap_size=10)
            retrieved = self.retrieve(query_norm, embeddings, top_k=top_k)
            ChatUtils.clear_data_directory(DATA_DYNAMIC_DIR)  # Limpia el directorio dinámico después de usarlo
            
            
            
        # 2. Construir el prompt integrando los fragmentos recuperados y la consulta
        context = ".".join([text for _, text in retrieved])
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
    
    def ask(self, query,json_format, top_k=60):
        """
        Llama al modelo de lenguaje con la query y devuelve la respuesta.
        """
        # Cambiar la fuente de conocimiento por la que solo devuelva hoteles y lugares con precios
        prompt = self.prompt_gen(query,self.store_vectors_formulario, top_k=top_k,distance_threshold=1) # Cambia a self.store_vectors por self.store_vectors_formulario
        prompt += "\n\nPor favor, devuelve la respuesta unicamente en el siguiente formato JSON:\n" + json.dumps(json_format, ensure_ascii=False, indent=2)
        response = self.gemini_model.generate_content(prompt)
        return response.text


