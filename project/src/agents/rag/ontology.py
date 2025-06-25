from rdflib import Graph, Namespace, Literal, RDF, URIRef
import os
import json
import re

EX = Namespace("http://turistai.org/turismo#")

def clean_uri(text):
    # Elimina caracteres no válidos para URIs y reemplaza espacios por "_"
    return re.sub(r'[^a-zA-Z0-9_]', '_', text.replace(" ", "_"))

class OntologyManager:
    def __init__(self, store_file="project/src/agents/rag/ontology_data.ttl"):
        self.store_file = store_file
        self.graph = Graph()
        self.graph.bind("ex", EX)

    def build_from_json_root(self, root_folder):
        """
        Recorre todas las subcarpetas (actividades) y procesa los JSON de cada una.
        """
        for actividad in os.listdir(root_folder):
            actividad_path = os.path.join(root_folder, actividad)
            if os.path.isdir(actividad_path):
                self._process_activity_folder(actividad_path, actividad.lower())

    def _process_activity_folder(self, folder_path, actividad):
        for filename in os.listdir(folder_path):
            if filename.endswith(".json"):
                with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as f:
                    lugares = json.load(f)
                for lugar in lugares:
                    nombre = lugar.get("nombre", "LugarDesconocido")
                    provincia = lugar.get("Provincia", None)
                    lugar_uri = URIRef(EX[clean_uri(nombre)])
                    self.graph.add((lugar_uri, RDF.type, EX.LugarTuristico))
                    self.graph.add((lugar_uri, EX.tieneNombre, Literal(nombre)))
                    self.graph.add((lugar_uri, EX.ofreceActividad, Literal(actividad)))
                    if provincia:
                        provincia_uri = URIRef(EX[clean_uri(provincia)])
                        self.graph.add((provincia_uri, RDF.type, EX.Provincia))
                        self.graph.add((provincia_uri, EX.tieneNombre, Literal(provincia)))
                        self.graph.add((lugar_uri, EX.estaEnProvincia, provincia_uri))

    def save_ontology(self):
        self.graph.serialize(destination=self.store_file, format="ttl")

    def load_ontology(self):
        self.graph = Graph()
        self.graph.parse(self.store_file, format="ttl")
    
    def build_sparql_query(query, entity):
        print(f"[DEBUG] Construyendo SPARQL para query: '{query}' y entity: '{entity}'")
        if "actividades" in query.lower():
            sparql = f"""
            PREFIX ex: <http://turistai.org/turismo#>
            SELECT DISTINCT ?actividad WHERE {{
                ?lugar a ex:LugarTuristico ;
                    ex:ofreceActividad ?actividad ;
                    ex:estaEnProvincia ?provincia .
                ?provincia a ex:Provincia ;
                        ex:tieneNombre "{entity}" .
            }}
            """
            print("[DEBUG] Tipo de consulta: ACTIVIDADES")
            return sparql
        elif "lugares" in query.lower() or "visitar" in query.lower():
            sparql = f"""
            PREFIX ex: <http://turistai.org/turismo#>
            SELECT DISTINCT ?nombre_lugar WHERE {{
                ?lugar a ex:LugarTuristico ;
                    ex:tieneNombre ?nombre_lugar ;
                    ex:estaEnProvincia ?provincia .
                ?provincia a ex:Provincia ;
                        ex:tieneNombre "{entity}" .
            }}
            """
            print("[DEBUG] Tipo de consulta: LUGARES")
            return sparql
        
        print("[DEBUG] No se reconoció el tipo de consulta")
        return None

    def query_ontology(self, sparql_query):
        return self.graph.query(sparql_query)
    
    @staticmethod
    def extract_entity(query):
        # Busca provincia o municipio en la pregunta
        print(f"[DEBUG] Extrayendo entidad de: '{query}'")
        match = re.search(r"(en|de)\s+([A-Za-zÁÉÍÓÚÑáéíóúñ ]+)", query, re.IGNORECASE)
        if match:
            entity = match.group(2).strip()
            print(f"[DEBUG] Entidad encontrada: '{entity}'")
            return entity
        print("[DEBUG] No se encontró entidad")
        return None
    
    @staticmethod
    def is_structured_query(query):
        """Detecta si la consulta es estructurada para usar la ontología"""
        print(f"[DEBUG] Verificando patrones en: '{query}'")
        patrones = [
            r"(actividades|lugares|hoteles|restaurantes).*(en|de)\s+([A-Za-zÁÉÍÓÚÑáéíóúñ ]+)",
            r"(qué|que).*(actividades|lugares).*(en|de)\s+([A-Za-zÁÉÍÓÚÑáéíóúñ ]+)",
            r"(municipio|provincia)\s+([A-Za-zÁÉÍÓÚÑáéíóúñ ]+)"
        ]
        for i, pat in enumerate(patrones):
            match = re.search(pat, query.lower())
            if match:
                print(f"[DEBUG] Patrón {i+1} coincide: {pat}")
                print(f"[DEBUG] Match: {match.groups()}")
                return True
            else:
                print(f"[DEBUG] Patrón {i+1} no coincide: {pat}")
        return False
    
    def get_structured_answer(self, query):
        # Verificar si es consulta estructurada
        is_structured = OntologyManager.is_structured_query(query)
        
        if is_structured:
            # Extraer entidad
            entity = OntologyManager.extract_entity(query)
            
            # Normalizar nombre de provincia
            if entity:
                normalized_entity = self.normalize_province_name(entity)
            else:
                normalized_entity = entity
            
            # Construir consulta SPARQL
            sparql = OntologyManager.build_sparql_query(query, normalized_entity)
            
            if sparql:
                try:
                    results = self.query_ontology(sparql)
                    result_list = [str(row[0]) for row in results]
                    return result_list
                except Exception as e:
                    print(f"[ERROR] Error ejecutando consulta SPARQL: {e}")
                    return None
        
        return None

    def print_summary(self):
        print("Provincias encontradas:")
        for prov in self.graph.subjects(RDF.type, EX.Provincia):
            print("-", self.graph.value(prov, EX.tieneNombre))
        print("\nLugares turísticos y su actividad:")
        for lugar in self.graph.subjects(RDF.type, EX.LugarTuristico):
            nombre = self.graph.value(lugar, EX.tieneNombre)
            actividad = self.graph.value(lugar, EX.ofreceActividad)
            provincia = self.graph.value(lugar, EX.estaEnProvincia)
            provincia_nombre = self.graph.value(provincia, EX.tieneNombre) if provincia else None
            print(f"- {nombre} ({actividad}) en {provincia_nombre}")
    
    def get_all_provinces(self):
        """Obtiene todas las provincias en la ontología para debugging"""
        provinces = []
        for prov in self.graph.subjects(RDF.type, EX.Provincia):
            provinces.append(str(self.graph.value(prov, EX.tieneNombre)))
        return provinces
    
    def normalize_province_name(self, entity):
        """Normaliza el nombre de la provincia para mejor matching"""
        # Obtiene todas las provincias disponibles
        available_provinces = self.get_all_provinces()
        print(f"[DEBUG] Provincias disponibles: {available_provinces}")
        
        # Busca coincidencia exacta (case insensitive)
        for prov in available_provinces:
            if entity.lower() == prov.lower():
                print(f"[DEBUG] Coincidencia exacta encontrada: '{prov}'")
                return prov
        
        # Busca coincidencia parcial
        for prov in available_provinces:
            if entity.lower() in prov.lower() or prov.lower() in entity.lower():
                print(f"[DEBUG] Coincidencia parcial encontrada: '{prov}' para '{entity}'")
                return prov
        
        print(f"[DEBUG] No se encontró coincidencia para '{entity}'")
        return entity


# Example usage:
if __name__ == "__main__":
    manager = OntologyManager()
    # manager.build_from_json_root("project/src/agents/data_formulario")
    # manager.save_ontology()
    # manager.print_summary()

    #    # Load and query the ontology
    manager.load_ontology()
    print("[DEBUG] Ontología cargada")
    
    # Mostrar las provincias disponibles primero
    print("\n" + "="*50)
    print("PROVINCIAS DISPONIBLES EN LA ONTOLOGÍA:")
    print("="*50)
    available_provinces = manager.get_all_provinces()
    for i, prov in enumerate(available_provinces, 1):
        print(f"{i}. '{prov}'")
    print("="*50)
    
    # Testear diferentes tipos de consultas
    test_queries = [
        "Que lugares puedo visitar en la habana",
        "¿Qué actividades puedo hacer en Matanzas?",
        "lugares turísticos en Santiago de Cuba",
        "actividades en Pinar del Río"
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"PROBANDO CONSULTA: {query}")
        print(f"{'='*50}")
        result = manager.get_structured_answer(query)
        if result:
            print("✓ Resultados estructurados encontrados:", result)
        else:
            print("✗ No se encontraron resultados estructurados para la consulta.")
        print(f"{'='*50}")
    
    # query="Que lugares puedo visitar en la habana"
    # result = manager.get_structured_answer(query)
    # if result:
    #     print("Resultados estructurados:", result)
    # else:
    #     print("No se encontraron resultados estructurados para la consulta.")