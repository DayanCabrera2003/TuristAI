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
        if "actividades" in query.lower():
            return f"""
            PREFIX ex: <http://turistai.org/turismo#>
            SELECT DISTINCT ?actividad WHERE {{
                ?lugar a ex:LugarTuristico ;
                    ex:ofreceActividad ?actividad ;
                    ex:estaEnProvincia ?provincia .
                ?provincia a ex:Provincia ;
                        ex:tieneNombre "{entity}" .
            }}
            """
        elif "lugares" in query.lower():
            return f"""
            PREFIX ex: <http://turistai.org/turismo#>
            SELECT DISTINCT ?nombre_lugar WHERE {{
                ?lugar a ex:LugarTuristico ;
                    ex:tieneNombre ?nombre_lugar ;
                    ex:estaEnProvincia ?provincia .
                ?provincia a ex:Provincia ;
                        ex:tieneNombre "{entity}" .
            }}
            """
        return None

    def query_ontology(self, sparql_query):
        return self.graph.query(sparql_query)
    
    @staticmethod
    def extract_entity(query):
        # Busca provincia o municipio en la pregunta
        match = re.search(r"(en|de)\s+([A-Za-zÁÉÍÓÚÑáéíóúñ ]+)", query, re.IGNORECASE)
        if match:
            return match.group(2).strip()
        return None
    
    @staticmethod
    def is_structured_query(query):
        patrones = [
            r"(actividades|lugares|hoteles|restaurantes).*(en|de)\s+([A-Za-zÁÉÍÓÚÑáéíóúñ ]+)",
            r"(municipio|provincia)\s+([A-Za-zÁÉÍÓÚÑáéíóúñ ]+)"
        ]
        for pat in patrones:
            if re.search(pat, query.lower()):
                return True
        return False
    
    def get_structured_answer(self, query):
        if OntologyManager.is_structured_query(query):
            entity = OntologyManager.extract_entity(query)
            sparql = OntologyManager.build_sparql_query(query, entity)
            if sparql:
                results = self.query_ontology(sparql)
                # Procesa los resultados y genera una respuesta legible
                return [str(row[0]) for row in results]
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


# Example usage:
if __name__ == "__main__":
    manager = OntologyManager()
    # manager.build_from_json_root("project/src/agents/data_formulario")
    # manager.save_ontology()
    # manager.print_summary()

    # # Load and query the ontology
    manager.load_ontology()
    query = """

    PREFIX ex: <http://turistai.org/turismo#>
    SELECT DISTINCT ?nombre_lugar WHERE {
        ?lugar a ex:LugarTuristico ;
            ex:tieneNombre ?nombre_lugar ;
            ex:estaEnProvincia ?provincia .
        ?provincia a ex:Provincia ;
                ex:tieneNombre "Matanzas" .
    }
    """
    results = manager.query_ontology(query)
    for row in results:
        print(row.nombre_lugar)