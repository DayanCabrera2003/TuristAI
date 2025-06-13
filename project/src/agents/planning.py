import networkx as nx
import folium
import webbrowser
from geopy.geocoders import Nominatim
import random

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
                            "Isla_de_la_Juventud", "Pinar_del_Rio", "Artemisa", "La_Habana", "Mayabeque",
                            "Matanzas", "Cienfuegos", "Villa_Clara", "Sancti_Spiritus", "Ciego_de_Avila",
                            "Camaguey", "Las_Tunas", "Granma", "Holguin", "Santiago_de_Cuba", "Guantanamo"
                        ],
                        "description": "Ciudad donde se realiza la actividad."
                    },
                    "horario": {
                        "type": "object",
                        "properties": {
                            "dia": {"type": "integer", "minimum": 1, "maximum": 31, "description": "Día del mes."},
                            "mes": {"type": "integer", "minimum": 1, "maximum": 12, "description": "Mes del año."},
                            "hora": {"type": "string", "pattern": "^([01]?[0-9]|2[0-3]):[0-5][0-9]$", "description": "Hora en formato HH:MM (24h)."}
                        },
                        "required": ["dia", "mes", "hora"]
                    },
                    "lugares_a_visitar": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de lugares que se visitarán durante la actividad."
                    },
                    "tipo_actividad": {
                        "type": "string",
                        "enum": [
                            "Cultural", "Gastronomica", "Playa", "Aventura", "Naturaleza", "Histórica", "Deportiva", "Otro"
                        ],
                        "description": "Tipo de actividad turística."
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

actividades_turisticas = []
variables = {} #a cada variable se le asigna una actividad de la lista actividades
preferencias_actividades = []
preferencias_actividades_booleano = []
preferencias_lugares = []
preferencias_lugares_booleano = []
presupuesto_max = 0
min_presupuesto = False
max_lugares = False

def evaluar_itinerario(actividades):
    evaluacion = 0

    # Copias locales para no modificar las listas globales
    actividades_cubiertas = [False] * len(preferencias_actividades)
    lugares_cubiertos = [False] * len(preferencias_lugares)
    total_costo = 0

    for actividad in actividades:
        # Maximizar lugares visitados
        if max_lugares:
            evaluacion += len(actividad.get("lugares_a_visitar", []))
        # Minimizar presupuesto
        if min_presupuesto:
            total_costo += actividad.get("costo", 0)
        # Preferencias de tipo de actividad
        for i, tipo in enumerate(preferencias_actividades):
            if actividad.get("tipo_actividad") == tipo and not actividades_cubiertas[i]:
                evaluacion += 2  # Mayor peso por cubrir preferencia
                actividades_cubiertas[i] = True
        # Preferencias de lugares
        for lugar in actividad.get("lugares_a_visitar", []):
            for i, lugar_preferido in enumerate(preferencias_lugares):
                if lugar == lugar_preferido and not lugares_cubiertos[i]:
                    evaluacion += 2
                    lugares_cubiertos[i] = True

    # Penalización por no cubrir preferencias
    penalizacion = actividades_cubiertas.count(False) + lugares_cubiertos.count(False)
    evaluacion -= penalizacion

    # Penalización si se excede el presupuesto
    if min_presupuesto and total_costo > presupuesto_max > 0:
        evaluacion -= (total_costo - presupuesto_max) / 10  # Penaliza el exceso

    return evaluacion



def crear_mapa(lugares):
    # Coordenadas aproximadas del centro de Cuba
    cuba_center = [21.5218, -77.7812]

    # Crear el mapa centrado en Cuba con opción de zoom
    mapa = folium.Map(location=cuba_center, zoom_start=7, control_scale=True, max_zoom=30, min_zoom=7)
    geolocator = Nominatim(user_agent="turistia")
    
    for lugar in lugares:
        location = geolocator.geocode(f"{lugar}, Cuba")
        if location:
            folium.Marker([location.latitude, location.longitude], popup=lugar).add_to(mapa)
    
    # Guardar el mapa en un archivo HTML
    mapa.save("mapa_cuba.html")
    webbrowser.open("mapa_cuba.html")



#Metaheuristica algoritmos geneticos

def cruzar(padre1, padre2):
    """Cruza dos itinerarios (listas de actividades) usando un punto de corte."""
    if not padre1 or not padre2:
        return padre1[:], padre2[:]
    punto = random.randint(1, min(len(padre1), len(padre2)) - 1)
    hijo1 = padre1[:punto] + padre2[punto:]
    hijo2 = padre2[:punto] + padre1[punto:]
    return hijo1, hijo2

def mutar(itinerario, actividades_disponibles, prob_mutacion=0.1):
    """Mutación: reemplaza aleatoriamente una actividad por otra."""
    nuevo = itinerario[:]
    for i in range(len(nuevo)):
        if random.random() < prob_mutacion:
            opciones = [a for a in actividades_disponibles if a not in nuevo]
            if opciones:
                nuevo[i] = random.choice(opciones)
    return nuevo

def seleccionar(poblacion, fitnesses, num_seleccionados):
    """Selecciona los mejores individuos según su fitness."""
    seleccionados = sorted(zip(poblacion, fitnesses), key=lambda x: x[1], reverse=True)
    return [ind for ind, fit in seleccionados[:num_seleccionados]]

def algoritmo_genetico_itinerario(actividades_disponibles, tam_poblacion=30, generaciones=50):
    """
    Optimiza el itinerario usando un algoritmo genético.
    Retorna el mejor itinerario encontrado.
    """
    # Inicialización aleatoria de la población
    poblacion = []
    for _ in range(tam_poblacion):
        tam_itinerario = random.randint(1, min(5, len(actividades_disponibles)))
        individuo = random.sample(actividades_disponibles, tam_itinerario)
        poblacion.append(individuo)

    for _ in range(generaciones):
        # Evaluar fitness
        fitnesses = [evaluar_itinerario(ind) for ind in poblacion]
        # Selección
        seleccionados = seleccionar(poblacion, fitnesses, tam_poblacion // 2)
        # Cruzamiento y mutación para crear nueva población
        nueva_poblacion = seleccionados[:]
        while len(nueva_poblacion) < tam_poblacion:
            padres = random.sample(seleccionados, 2)
            hijo1, hijo2 = cruzar(padres[0], padres[1])
            hijo1 = mutar(hijo1, actividades_disponibles)
            hijo2 = mutar(hijo2, actividades_disponibles)
            nueva_poblacion.extend([hijo1, hijo2])
        poblacion = nueva_poblacion[:tam_poblacion]

    # Seleccionar el mejor individuo final
    fitnesses = [evaluar_itinerario(ind) for ind in poblacion]
    mejor_indice = fitnesses.index(max(fitnesses))
    return poblacion[mejor_indice]


