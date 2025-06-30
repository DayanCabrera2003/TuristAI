import itertools
import random
import math
from .mapaCuba import obtener_coordenadas, distancia_haversine
from .metaheuristicas import MetaheuristicasItinerario
from collections import deque

"""
Módulo optimizado para resolver el problema del viajante (TSP) aplicado a provincias cubanas.
Implementa múltiples algoritmos de optimización para encontrar el recorrido más eficiente.
"""

# Coordenadas aproximadas de las capitales provinciales de Cuba (lat, lon)
COORDENADAS_PROVINCIAS = {
    "Pinar del Rio": (22.4178, -83.6981),
    "Artemisa": (22.8135, -82.7597),
    "La Habana": (23.1136, -82.3666),
    "Mayabeque": (22.9275, -82.0592),
    "Matanzas": (23.0413, -81.5775),
    "Cienfuegos": (22.1465, -80.4363),
    "Villa Clara": (22.4067, -79.9645),
    "Sancti Spiritus": (21.9294, -79.4428),
    "Ciego de Avila": (21.8400, -78.7619),
    "Camaguey": (21.3806, -77.9169),
    "Las Tunas": (20.9619, -76.9511),
    "Granma": (20.3422, -76.6172),  # Bayamo
    "Holguin": (20.8875, -76.2631),
    "Santiago de Cuba": (20.0250, -75.8219),
    "Guantanamo": (20.1444, -75.2097),
    "Isla de la Juventud": (21.7587, -82.8597)
}

def distancia_haversine(coord1, coord2):
    """
    Calcula la distancia Haversine entre dos coordenadas (lat, lon).
    """
    R = 6371  # Radio de la Tierra en km
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calcular_distancia_total_ruta(provincias_lista):
    """
    Calcula la distancia total de una ruta entre provincias.
    
    Args:
        provincias_lista (list): Lista de nombres de provincias
        
    Returns:
        float: Distancia total en kilómetros
    """
    if len(provincias_lista) < 2:
        return 0
    
    distancia_total = 0
    for i in range(len(provincias_lista) - 1):
        prov1 = provincias_lista[i]
        prov2 = provincias_lista[i + 1]
        if prov1 in COORDENADAS_PROVINCIAS and prov2 in COORDENADAS_PROVINCIAS:
            distancia_total += distancia_haversine(
                COORDENADAS_PROVINCIAS[prov1], 
                COORDENADAS_PROVINCIAS[prov2]
            )
    
    return distancia_total


def recorrido_optimo(lugares):
    """
    Dada una lista de provincias, retorna el recorrido más corto posible para visitarlas todas,
    usando las coordenadas de COORDENADAS_PROVINCIAS. Devuelve los mismos elementos que hay en 'lugares' pero ordenados.
    Algoritmo: fuerza bruta si <=8 provincias, nearest neighbor si >8.
    """
    if not lugares:
        return []

    # Filtrar solo provincias válidas con coordenadas
    provincias = [prov for prov in lugares if prov in COORDENADAS_PROVINCIAS]
    if not provincias:
        return lugares

    n = len(provincias)
    # Fuerza bruta para pocos nodos
    if n <= 8:
        mejor_ruta = None
        mejor_dist = float('inf')
        for perm in itertools.permutations(provincias):
            dist = 0
            for i in range(n - 1):
                dist += distancia_haversine(COORDENADAS_PROVINCIAS[perm[i]], COORDENADAS_PROVINCIAS[perm[i+1]])
            if dist < mejor_dist:
                mejor_dist = dist
                mejor_ruta = perm
        return list(mejor_ruta)
    else:
        # Algoritmo nearest neighbor para más provincias
        mejor_ruta = []
        restantes = set(provincias)
        actual = provincias[0]
        mejor_ruta.append(actual)
        restantes.remove(actual)
        while restantes:
            siguiente = min(restantes, key=lambda prov: distancia_haversine(COORDENADAS_PROVINCIAS[actual], COORDENADAS_PROVINCIAS[prov]))
            mejor_ruta.append(siguiente)
            restantes.remove(siguiente)
            actual = siguiente
        return mejor_ruta



def mejor_itinerario(lugares, dias, evaluador: MetaheuristicasItinerario):
    """
    Ordena los lugares agrupándolos según el recorrido óptimo de provincias.
    
    Args:
        lugares (list): Lista de lugares con información de ciudad
        dias (int): Número de días/lugares a seleccionar
        algoritmo (str): Algoritmo de optimización a usar
        optimizar_por_distancia (bool): Si optimizar por distancia real o usar orden geográfico
    
    Returns:
        tuple: (lugares_seleccionados, cantidad_seleccionada)
    """
    if not lugares:
        return [], 0
    
    # 1. Obtener provincias únicas
    provincias_lugares = {}
    for lugar in lugares:
        ciudad = lugar.get('ciudad', '').strip()
        if ciudad:
            if ciudad not in provincias_lugares:
                provincias_lugares[ciudad] = []
            provincias_lugares[ciudad].append(lugar)
    
    provincias_unicas = list(provincias_lugares.keys())
    
    if not provincias_unicas:
        # Si no hay información de ciudad, devolver los primeros 'dias' lugares
        return lugares[:dias], min(len(lugares), dias)
    
    # 2. Ordenar provincias óptimamente

    provincias_ordenadas = recorrido_optimo(provincias_unicas)

    
    # 3. Seleccionar lugares siguiendo el orden óptimo de provincias
    lugares_seleccionados = []
    lugares_por_provincia = {provincia: provincias_lugares[provincia][:] for provincia in provincias_ordenadas}
    
    # Distribuir lugares de manera equilibrada entre provincias
    while len(lugares_seleccionados) < dias and any(lugares_por_provincia.values()):
        for provincia in provincias_ordenadas:
            if len(lugares_seleccionados) >= dias:
                break
            
            if lugares_por_provincia[provincia]:
                lugar = lugares_por_provincia[provincia].pop(0)
                if lugar not in lugares_seleccionados:
                    lugares_seleccionados.append(lugar)
    
    # Calcular el valor del itinerario usando una heurística simple
    # Como no tenemos acceso a la instancia de MetaheuristicasItinerario aquí,
    # calculamos un valor basado en la optimización de la ruta
    valor_itinerario = evaluador.evaluar_itinerario(lugares_seleccionados)
    
    return lugares_seleccionados, valor_itinerario
