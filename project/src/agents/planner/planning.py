from rag import rag
import json
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
    def __init__(self, tipolugares, lugares, dias_vacaciones, presupuesto_disponible):
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
                    "estrellas": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 5,
                        "description": "Puntuación del lugar en base a 5."
                    },
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
                    "tipo_lugar": {
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
                    "nombre", "descripcion", "ciudad", "tipo_lugar"
                ]
                },
                "description": "Lista lugares turísticos."
            }
            },
            "required": ["lugares"]
        }
    def generate_itinerary(self):
        
        utils = rag.ChatUtils()
        query = f"""
         {", ".join(self.tipolugares)} que estén en alguna de las siguientes provincias: {", ".join(self.lugares)} de Cuba.
        """
    
        result = utils.ask(query, self.schema)
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            print("Error al decodificar el resultado como JSON.")
            result = {}

        lugares_turisticos = []
        
        lugares = result.get("lugares", [])
        print(lugares)
        for lugar in lugares:
            nombre = lugar.get("nombre", "")
            descripcion = lugar.get("descripcion", "")
            estrellas = lugar.get("estrellas", 0)
            ciudad = lugar.get("ciudad", "")
            horario = lugar.get("horario", {})
            tipo_lugar = lugar.get("tipo_lugar", [])
            lugar_dict = {
                "nombre": nombre,
                "descripcion": descripcion,
                "estrellas": estrellas,
                "ciudad": ciudad,
                "horario": horario,
                "tipo_lugar": tipo_lugar
            }
            lugares_turisticos.append(lugar_dict)

        # metaheuristicas = MetaheuristicasItinerario(
        #     lugares_turisticos=lugares,
        #     preferencias_actividades=self.tipolugares,
        #     preferencias_lugares=self.lugares,
        #     presupuesto_max=self.presupuesto_disponible,
        #     min_presupuesto=True,  # Minimizar presupuesto
        #     max_lugares=False  # No maximizar lugares visitados
        # )



        return result
















