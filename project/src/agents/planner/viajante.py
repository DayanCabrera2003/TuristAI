import itertools
from .mapaCuba import obtener_coordenadas, distancia_haversine
from .metaheuristicas import MetaheuristicasItinerario
from collections import deque

"""
Dada una lista de lugares, quiero que los ordene en el recorrido más óptimo posible, de modo que se visiten todos.
"""
provincias = {
    "Isla de la Juventud": ["Pinar del Rio", "Artemisa"],
    "Pinar del Rio": ["Artemisa", "Isla de la Juventud"],
    "Artemisa": ["Pinar del Rio", "La Habana", "Mayabeque", "Isla de la Juventud"],
    "La Habana": ["Artemisa", "Mayabeque"],
    "Mayabeque": ["Artemisa", "La Habana", "Matanzas"],
    "Matanzas": ["Mayabeque", "Cienfuegos", "Villa Clara"],
    "Cienfuegos": ["Matanzas", "Villa Clara", "Sancti Spiritus"],
    "Villa Clara": ["Cienfuegos", "Sancti Spiritus", "Matanzas"],
    "Sancti Spiritus": ["Villa Clara", "Ciego de Avila", "Cienfuegos"],
    "Ciego de Avila": ["Sancti Spiritus", "Camaguey"],
    "Camaguey": ["Ciego de Avila", "Las Tunas"],
    "Las Tunas": ["Camaguey", "Holguin", "Granma"],
    "Holguin": ["Las Tunas", "Bayamo", "Santiago de Cuba", "Guantanamo"],
    "Granma": ["Holguin", "Santiago de Cuba", "Las Tunas"],
    "Santiago de Cuba": ["Holguin", "Guantanamo", "Granma"],
    "Guantanamo": ["Santiago de Cuba", "Holguin"]
}

def recorrido_optimo(lugares):
    """
    Dada una lista de provincias, retorna el recorrido más corto posible para visitarlas todas,
    usando el grafo de adyacencias 'provincias'. Devuelve los mismos elementos que hay en 'lugares' pero ordenados.
    """

    if not lugares:
        return []

    # BFS para encontrar el camino más corto que pase por todos los nodos (TSP aproximado)
    mejor_ruta = []
    min_camino = None
    min_len = float('inf')

    # Probar cada provincia como punto de inicio
    for inicio in lugares:
        queue = deque()
        queue.append((inicio, [inicio], set([inicio])))
        while queue:
            actual, camino, visitados = queue.popleft()
            if len(visitados) == len(lugares):
                if len(camino) < min_len:
                    min_len = len(camino)
                    min_camino = camino
                continue
            for vecino in provincias.get(actual, []):
                if vecino in lugares and vecino not in visitados:
                    queue.append((vecino, camino + [vecino], visitados | {vecino}))
    # Si no se encuentra un camino válido, devolver la lista original
    return min_camino if min_camino else lugares



def mejor_itinerario(lugares, dias):
    """
    Ordena los lugares agrupándolos según el recorrido óptimo de provincias.
    """
    # 1. Obtener provincias únicas
    provincias = list({lugar.get('ciudad', " ") for lugar in lugares})

    # 2. Ordenar provincias óptimamente
    provincias_ordenadas = recorrido_optimo(provincias)

    # 3. Seleccionar una cantidad de lugares igual a 'dias', recorriendo provincias en orden óptimo
    lugares_seleccionados = []
    for provincia in provincias_ordenadas:
        for lugar in lugares:
            if lugar.get('ciudad', " ") == provincia and lugar not in lugares_seleccionados:
                lugares_seleccionados.append(lugar)
                if len(lugares_seleccionados) == dias:
                    break
        if len(lugares_seleccionados) == dias:
            break

    return lugares_seleccionados, len(lugares_seleccionados)
