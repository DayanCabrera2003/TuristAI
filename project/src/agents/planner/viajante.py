import itertools
from .mapaCuba import obtener_coordenadas, distancia_haversine
from .metaheuristicas import MetaheuristicasItinerario

"""
Dada una lista de lugares, quiero que los ordene en el recorrido más óptimo posible, de modo que se visiten todos.
"""

def recorrido_optimo(lugares):
    """
    Dada una lista de lugares, retorna el recorrido más corto posible para visitarlos todos.
    """
    ubicaciones = [obtener_coordenadas(lugar) for lugar in lugares]
    min_distancia = float('inf')
    mejor_ruta = []

    for perm in itertools.permutations(range(len(lugares))):
        distancia = 0
        for i in range(len(perm) - 1):
            distancia += distancia_haversine(ubicaciones[perm[i]], ubicaciones[perm[i+1]])
        if distancia < min_distancia:
            min_distancia = distancia
            mejor_ruta = [lugares[i] for i in perm]

    return mejor_ruta



def mejor_itinerario(lugares, dias):
    """
    Ordena los lugares agrupándolos según el recorrido óptimo de provincias.
    """
    # 1. Obtener provincias únicas
    provincias = list({lugar.get('ciudad', " ") for lugar in lugares})

    # 2. Ordenar provincias óptimamente
    provincias_ordenadas = recorrido_optimo(provincias)

    # 3. Agrupar lugares por provincia según el orden óptimo
    lugares_ordenados = []
    for provincia in provincias_ordenadas:
        lugares_en_provincia = [lugar for lugar in lugares if lugar.get('ciudad', " ") == provincia]
        lugares_ordenados.extend(lugares_en_provincia)

    # Generar combinaciones con repetición de 'lugares_ordenados', de longitud 'dias', manteniendo el orden
    mejor_itinerario = None
    mejor_valor = 0
    n = len(lugares_ordenados)
    if n > 0 and dias > 0:
        # Genera todas las combinaciones con repetición y orden no decreciente de índices
        for indices in itertools.combinations_with_replacement(range(n), dias):
            combinacion = [lugares_ordenados[i] for i in indices]
            _, valor = MetaheuristicasItinerario.evaluar_itinerario(combinacion)
            if valor > mejor_valor: 
                mejor_valor = valor
                mejor_itinerario = combinacion
    return mejor_itinerario, mejor_valor