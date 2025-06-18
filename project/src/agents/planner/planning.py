from rag import rag
import json
import re
from .metaheuristicas import MetaheuristicasItinerario


"""
Esta clase genera un itinerario personalizado según las preferencias del turista.
Utiliza un esquema JSON para solicitar información relevante a través del agente de búsqueda. 
Estos datos conforman el dominio del problema de satisfacción de restricciones (CSP). 
Primero, se busca una asignación factible de actividades. Luego, mediante una metaheurística, 
se optimiza el itinerario para minimizar el presupuesto o maximizar la cantidad de actividades, 
según los objetivos definidos por el usuario.

"""
class Planer:
    def __init__(self, tipolugares, lugares, dias_vacaciones, presupuesto_disponible,
                 max_cant_lugares=True, min_presupuesto=False):
        self.max_cant_lugares = max_cant_lugares
        self.min_presupuesto = min_presupuesto
        self.lugares = lugares
        self.dias_vacaciones = dias_vacaciones
        self.presupuesto_disponible = presupuesto_disponible
        self.tipolugares = tipolugares
        self.schema = {
            "type": "object",
            "properties": {
                "lugares": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "nombre": {"type": "string", "description": "Nombre del lugar turístico."},
                            "descripcion": {"type": "string", "description": "Descripción breve del lugar."},
                            "precio": {"type": "number", "description": "Costo estimado del lugar en dólares."},
                            "ciudad": {
                                "type": "string",
                                "enum": [
                                    "Isla de la Juventud", "Pinar del Rio", "Artemisa", "La Habana", "Mayabeque",
                                    "Matanzas", "Cienfuegos", "Villa Clara", "Sancti Spiritus", "Ciego de Avila",
                                    "Camaguey", "Las Tunas", "Granma", "Holguin", "Santiago de Cuba", "Guantanamo"
                                ],
                                "description": "Ciudad de Cuba donde está el lugar."
                            },
                            "horario": {
                                "type": "object",
                                "properties": {
                                    "dia": {"type": "integer", "minimum": 1, "maximum": 31, "description": "Día del mes en que se realizará la actividad."},
                                    "mes": {"type": "integer", "minimum": 1, "maximum": 12, "description": "Mes del año en que se realizará la actividad."},
                                    "hora": {"type": "string", "pattern": "^([01]?[0-9]|2[0-3]):[0-5][0-9]$", "description": "Hora en formato HH:MM (24h) en que se realizará la actividad."}
                                },
                                "required": ["dia", "mes", "hora"]
                            },
                            "tipo_actividad": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": [
                                        "Museos", "Galerías de arte", "Obras de teatro", "Espectáculos", "Carnavales",
                                        "Centros históricos y patrimoniales", "Gastronomía local", "Heladerías", "Dulcerías",
                                        "Varadero", "Cayos", "Guardalavaca", "Playa Pesquero", "Playa Ancón",
                                        "Senderismo", "Excursiones", "Observación de flora", "Observación de fauna",
                                        "Parques Nacionales", "Reservas", "Fortalezas", "Castillos", "Casas-museo", "Museos de historia",
                                        "Spa", "Resorts", "Conciertos", "Festivales de música", "Clubs nocturnos", "Bares", 
                                        "Iglesias", "Catedrales", "Festividades religiosas", "Hotel", "Otras"
                                    ]
                                },
                                "description": "Lista lugares, de tipos de lugares y de actividades que se realizan en ese lugar turístico."
                            }
                        },
                        "required": [
                            "nombre", "descripcion", "costo", "ciudad", "horario", "ciudad", "tipo_lugares"
                        ]
                    },
                    "description": "Lista de actividades turísticas propuestas."
                }
            },
            "required": ["lugares"]
        }
    def generate_itinerary(self, metaheuristic = "AG"):
        
        utils = rag.ChatUtils()
        query = f"""
         {", ".join(self.tipolugares)} que estén en alguna de las siguientes provincias: {", ".join(self.lugares)} de Cuba.
        """
        
        result= utils.ask(query,self.schema, 20)
        raw_json = self.extract_json(result)
        if raw_json:
            try:
                result_json = json.loads(raw_json)
            except json.JSONDecodeError as e:
                print("Error al decodificar el JSON extraído:", e)
                result_json = {}
        else:
            print("No se encontró un bloque JSON en la respuesta.")
            result_json = {}
        
        lugares = result_json["lugares"]
        if not lugares:
            print("No se encontraron lugares turísticos en la respuesta. No se puede generar itinerario.")
            return []


        metaheuristica = MetaheuristicasItinerario(
            lugares_turisticos=lugares,
            preferencias_tipos_lugares=self.tipolugares,
            preferencias_lugares=self.lugares,
            presupuesto_max=self.presupuesto_disponible,
            min_presupuesto= self.min_presupuesto,
            max_lugares= self.max_cant_lugares
        )
        itinerario = None
        valor = 0
        if metaheuristic == "AG":
            itinerario, valor = metaheuristica.algoritmo_genetico_itinerario()
        elif metaheuristic == "PSO":
            itinerario, valor = metaheuristica.pso_itinerario()
        return itinerario, valor
    

    def extract_json(self,text):
        """
        Extrae el primer bloque JSON válido de un string, incluso si está dentro de un bloque Markdown.
        """
        # Busca bloque entre ```json ... ```
        match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            return match.group(1)
        # Si no hay bloque markdown, busca cualquier bloque {...}
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            return match.group(1)
        return None










