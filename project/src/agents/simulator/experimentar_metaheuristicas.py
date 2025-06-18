import sys
import os
import random

# Agrega el directorio padre al sys.path para poder importar planner
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from planner.planning import Planer

"""
n tamaño del subconjunto de preferencias de lugares turísticos
i clases de lugares turísticos de preferencias
m lugar de preferencia de esa clase
"""

gustos = {
    "Culturales": [
        "Museos", "Galerías de arte", "Obras de teatro", "Espectáculos", "Carnavales", "Centros históricos y patrimoniales"
    ],

    "Gastronomicas": ["Gastronomía local", "Heladerías", "Dulcerías"],

    "Playa": ["Varadero", "Cayos", "Guardalavaca", "Playa Pesquero", "Playa Ancón", "Hoteles"],

    "Naturaleza": [
        "Senderismo", "Excursiones", "Observación de flora", "Observación de fauna", "Parques Nacionales", "Reservas"
    ],

    "Historia": ["Fortalezas", "Castillos", "Casas-museo", "Museos de historia"],

    "Relajacion": ["Spa", "Hoteles", "Resorts"],

    "Musical": ["Conciertos", "Festivales de música", "Clubs nocturnos", "Bares"],

    "Religiosas": ["Iglesias", "Catedrales", "Festividades religiosas"],

}

opcionesLugares = [
    "Pinar del Río", "Artemisa", "La Habana", "Mayabeque", "Matanzas", "Cienfuegos",
    "Villa Clara", "Sancti Spíritus", "Ciego de Ávila", "Camagüey", "Las Tunas",
    "Holguín", "Granma", "Santiago de Cuba", "Guantánamo", "Isla de la Juventud", "Marcar todas"
]

total_preferencias = sum(len(v) for v in gustos.values())
k = len(gustos)

muestra = []
muestraluagres = []
contador = 0
while(contador < 100):
    contador += 1
    # Parámetros de la distribución normal
    media = (total_preferencias + 1) / 2
    desviacion = total_preferencias / 6  # Aproximadamente el 99% cae dentro del rango

    n = int(round(random.gauss(media, desviacion)))
    n = max(1, min(n, total_preferencias))

    # Generar i usando un modelo matemático de cadenas de Markov
    # Supongamos que hay k clases de lugares turísticos

    preferencias_usuarios = []
    preferencia_lugares = []
    for i in range(0, n-1):
        # Matriz de transición ajustada para tamaño k x k, con probabilidades uniformes excepto una ligera preferencia por permanecer en el mismo estado
        transicion = []
        for idx in range(k):
            fila = [0.1] * k
            fila[idx] = 0.6  # Preferencia por permanecer en el mismo estado
            suma = sum(fila)
            fila = [x / suma for x in fila]  # Normalizar para que sumen 1
            transicion.append(fila)

        # Estado inicial aleatorio
        estado_actual = random.randint(0, k - 1)

        # Número de pasos de la cadena de Markov
        pasos = 10
        for _ in range(pasos):
            estado_actual = random.choices(
                range(k), weights=transicion[estado_actual]
            )[0]

        i = estado_actual + 1  # Ajustar a 1-based index si es necesario

        clave = list(gustos.keys())[estado_actual]
        m = random.randint(0, len(gustos[clave]) - 1)
        preferencias_usuarios.append(gustos[clave][m])

    mediaL = (total_preferencias + 1) / 2
    desviacionL = len(opcionesLugares) / 6  # Aproximadamente el 99% cae dentro del rango

    nL = int(round(random.gauss(mediaL, desviacionL)))
    nL = max(1, min(n, len(opcionesLugares)))

    for i in range(0, nL):
        L = random.randint(0, len(opcionesLugares) - 1)
        preferencia_lugares.append(opcionesLugares[L])
    
    muestraluagres.append(preferencia_lugares)
    muestra.append(preferencias_usuarios)

promedio1 = 0
promedio2 = 0
for i in range(0, len(muestra)-1) :
    planificador = Planer(
        muestra[i],                # tipolugares (preferencias de actividades)
        muestraluagres[i],         # lugares (preferencias de lugares)
        7,                         # dias_vacaciones (puedes ajustar este valor)
        1000                       # presupuesto_disponible
    )

    _, valor1 = planificador.generate_itinerary(metaheuristic="AG")
    _, valor2 = planificador.generate_itinerary(metaheuristic="PSO")
    promedio1 += valor1
    promedio2 += valor2

promedio1 /= 100
promedio2 /= 100

print("Promedio de valor de los itinerarios que genera la metaheuristica AG: " + promedio1)
print("Promedio de valor de los itinerarios que genera la metaheuristica PGO: " + promedio2)









