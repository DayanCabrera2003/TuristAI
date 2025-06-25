from .metaheuristicas import MetaheuristicasItinerario
from itertools import product

""""
Prueba todas las combinaciones posibles y elige la mejor según la función de evaluación.
"""

def fuerza_bruta(lugares, dias, min_repeticiones=1, max_repeticiones=None):
    """
    Genera todas las combinaciones posibles de tamaño igual a 'dias'
    de los elementos del vector 'lugares', permitiendo repeticiones.
    Además, permite especificar el mínimo y máximo de repeticiones de cada elemento.
    """
    if max_repeticiones is None:
        max_repeticiones = dias

    todos_itinerarios = []
    for combinacion in product(lugares, repeat=dias):
        valido = True
        for lugar in lugares:
            rep = combinacion.count(lugar)
            if rep < min_repeticiones or rep > max_repeticiones:
                valido = False
                break
        if valido:
            todos_itinerarios.append(combinacion)
    
    mejor_itinerario = None
    mejor_valor = 0
    for itinerario in todos_itinerarios:
        _, valor = MetaheuristicasItinerario.evaluar_itinerario(itinerario)
        if valor > mejor_valor:
            mejor_valor = valor
            mejor_itinerario = itinerario

    return mejor_itinerario, mejor_valor