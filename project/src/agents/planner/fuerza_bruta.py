from .metaheuristicas import MetaheuristicasItinerario
from itertools import product


""""
Prueba todas las combinaciones posibles y elige la mejor según la función de evaluación.
"""

def fuerza_bruta(lugares, dias, planificador: MetaheuristicasItinerario, min_repeticiones=1, max_repeticiones=None):
    """
    Genera todas las combinaciones posibles de tamaño igual a 'dias'
    de los elementos del vector 'lugares', permitiendo repeticiones.
    Además, permite especificar el mínimo y máximo de repeticiones de cada elemento.
    """
    if max_repeticiones is None:
        max_repeticiones = dias

    mejor_itinerario = None
    mejor_valor = 0.0
    contador = 0
    for combinacion in product(lugares, repeat=dias):
        if contador >= 3000: break
        contador += 1
        valor = planificador.evaluar_itinerario(actividades=combinacion)
        if valor > mejor_valor:
            mejor_valor = valor
            mejor_itinerario = combinacion

    return mejor_itinerario, mejor_valor