from rag import rag


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
                            "costo": {"type": "number", "description": "Costo estimado del lugar en dólares."},
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
                            "nombre", "descripcion", "costo", "ciudad", "horario", "ciudad", "tipo_lugares"
                        ]
                    },
                    "description": "Lista de actividades turísticas propuestas."
                }
            },
            "required": ["actividades"]
        }
    def generate_itinerary(self):
        
        utils = rag.ChatUtils()
        query = f"""
         {", ".join(self.tipolugares)} que estén en alguna de las siguientes provincias: {", ".join(self.lugares)} de Cuba.
        """
        print("#############Realizando búsqueda con el query:", query)
        result= utils.ask(query,self.schema, 20)
        print("Resultado de la búsqueda:", result)
        return result
















