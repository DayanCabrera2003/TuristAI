"""
Esta clase genera un itinerario personalizado según las preferencias del turista.
Utiliza un esquema JSON para solicitar información relevante a través del agente de búsqueda. 
Estos datos conforman el dominio del problema de satisfacción de restricciones (CSP). 
Primero, se busca una asignación factible de actividades. Luego, mediante una metaheurística, 
se optimiza el itinerario para minimizar el presupuesto o maximizar la cantidad de actividades, 
según los objetivos definidos por el usuario.

"""

schema = {
    "type": "object",
    "properties": {
        "actividades": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre de la actividad turística."},
                    "descripcion": {"type": "string", "description": "Descripción breve de la actividad."},
                    "costo": {"type": "number", "description": "Costo estimado de la actividad en moneda local."},
                    "ciudad": {
                        "type": "string",
                        "enum": [
                            "Isla de la Juventud", "Pinar del Rio", "Artemisa", "La Habana", "Mayabeque",
                            "Matanzas", "Cienfuegos", "Villa Clara", "Sancti Spiritus", "Ciego de Avila",
                            "Camaguey", "Las Tunas", "Granma", "Holguin", "Santiago de Cuba", "Guantanamo"
                        ],
                        "description": "Ciudad donde se realiza la actividad."
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
                    "lugares_a_visitar": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de lugares que se visitarán durante la actividad."
                    },
                    "tipo_actividad": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": [
                                "Museos", "Galerías de arte", "Monumentos históricos", "Obras de teatro", "Danza", "Centros históricos y patrimoniales",
                                

                            ]
                        },
                        "description": "Lista de tipos de actividad turística."
                    }
                },
                "required": [
                    "nombre", "descripcion", "costo", "ciudad", "horario", "lugares_a_visitar", "tipo_actividad"
                ]
            },
            "description": "Lista de actividades turísticas propuestas."
        }
    },
    "required": ["actividades"]
}















