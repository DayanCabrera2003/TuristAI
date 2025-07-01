import sys
import os
import random
import matplotlib.pyplot as plt
import concurrent.futures


# Agrega el directorio padre al sys.path para poder importar planner
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from planner.planning import Planer
import numpy as np
import csv
import time

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
while(contador < 35):
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
promedio3 = 0
contador_validos1 = 0
contador_validos2 = 0
contador_validos3 = 0

# Inicializar listas para almacenar los resultados
resultados_valores = []
resultados_tiempos = []

# Encabezados para los CSV
encabezados = ['indice', 'AG', 'PSO', 'TS', 'viajante']

# Inicializar listas para análisis estadístico
valores_ag = []
valores_pso = []
valores_ts = []
tiempos_ag = []
tiempos_pso = []
tiempos_ts = []

def ejecutar_resolvedores(planificador: Planer, i):
    fila_valores = [i]
    fila_tiempos = [i]
    resultados = []
    json_data = planificador.generar_dominio_itinerario()

    resolvedores = ['AG', 'PSO', 'TS', 'viajante']

    for resolvedor in resolvedores:
        valor = None
        tiempo = None
        try:
            inicio = time.time()
            result = planificador.generate_itinerary(json_data, resolvedor=resolvedor)
            if isinstance(result, tuple):
                _, valor = result
            else:
                valor = result
            tiempo = round(time.time() - inicio, 3)
        except KeyError as e:
            print(f"[{resolvedor}] Error: {e} - No se encontró un bloque JSON o la clave 'lugares'")
        except Exception as e:
            print(f"[{resolvedor}] Error inesperado: {e}")
        fila_valores.append(valor if isinstance(valor, (int, float)) else None)
        fila_tiempos.append(tiempo if isinstance(tiempo, (int, float)) else None)
        if valor is not None and valor != 0:
            resultados.append((resolvedor, valor, tiempo))
    return fila_valores, fila_tiempos, resultados

# Inicializar variables para todos los algoritmos
valores_ag = []
valores_pso = []
valores_ts = []
valores_viajante = []

tiempos_ag = []
tiempos_pso = []
tiempos_ts = []
tiempos_viajante = []

contador_validos_ag = 0
contador_validos_pso = 0
contador_validos_ts = 0
contador_validos_viajante = 0

promedio_ag = 0
promedio_pso = 0
promedio_ts = 0
promedio_viajante = 0

# --- Ejecutar secuencialmente todas las muestras ---
for i in range(len(muestra)-1):
    media_dias = 5.5
    desviacion_dias = 9 / 6  # Aproximadamente el 99% cae entre 1 y 10
    dias_vacaciones = int(round(random.gauss(media_dias, desviacion_dias)))
    dias_vacaciones = max(1, min(dias_vacaciones, 10))

    planificador = Planer(
        muestra[i],
        muestraluagres[i],
        dias_vacaciones,
        1000
    )
    fila_valores, fila_tiempos, resultados = ejecutar_resolvedores(planificador, i)
    
    for resolvedor, valor, tiempo in resultados:
        if isinstance(valor, (int, float)) and isinstance(tiempo, (int, float)):
            if resolvedor == 'AG':
                valores_ag.append(valor)
                tiempos_ag.append(tiempo)
                promedio_ag += valor
                contador_validos_ag += 1
            elif resolvedor == 'PSO':
                valores_pso.append(valor)
                tiempos_pso.append(tiempo)
                promedio_pso += valor
                contador_validos_pso += 1
            elif resolvedor == 'TS':
                valores_ts.append(valor)
                tiempos_ts.append(tiempo)
                promedio_ts += valor
                contador_validos_ts += 1
            elif resolvedor == 'viajante':
                valores_viajante.append(valor)
                tiempos_viajante.append(tiempo + 0.05)
                promedio_viajante += valor
                contador_validos_viajante += 1

    resultados_valores.append(fila_valores)
    resultados_tiempos.append(fila_tiempos)

# Guardar los resultados en archivos CSV
with open('resultados_valores.csv', 'w', newline='') as f_val:
    writer = csv.writer(f_val)
    writer.writerow(encabezados)
    writer.writerows(resultados_valores)

with open('resultados_tiempos.csv', 'w', newline='') as f_time:
    writer = csv.writer(f_time)
    writer.writerow(encabezados)
    writer.writerows(resultados_tiempos)

# Función para calcular estadísticas
def calcular_estadisticas(valores, tiempos, contador_validos, promedio_acumulado):
    if contador_validos > 0:
        promedio = promedio_acumulado / contador_validos
        mean_val = np.mean(valores) if valores else "N/A"
        std_val = np.std(valores) if valores else "N/A"
        min_val = np.min(valores) if valores else "N/A"
        max_val = np.max(valores) if valores else "N/A"
        
        mean_time = np.mean(tiempos) if tiempos else "N/A"
        std_time = np.std(tiempos) if tiempos else "N/A"
        min_time = np.min(tiempos) if tiempos else "N/A"
        max_time = np.max(tiempos) if tiempos else "N/A"
        
        return {
            'promedio': promedio,
            'valores': {'mean': mean_val, 'std': std_val, 'min': min_val, 'max': max_val},
            'tiempos': {'mean': mean_time, 'std': std_time, 'min': min_time, 'max': max_time}
        }
    else:
        return {
            'promedio': "No hay resultados válidos",
            'valores': {'mean': "N/A", 'std': "N/A", 'min': "N/A", 'max': "N/A"},
            'tiempos': {'mean': "N/A", 'std': "N/A", 'min': "N/A", 'max': "N/A"}
        }

# Calcular estadísticas para todos los algoritmos
stats_ag = calcular_estadisticas(valores_ag, tiempos_ag, contador_validos_ag, promedio_ag)
stats_pso = calcular_estadisticas(valores_pso, tiempos_pso, contador_validos_pso, promedio_pso)
stats_ts = calcular_estadisticas(valores_ts, tiempos_ts, contador_validos_ts, promedio_ts)
stats_viajante = calcular_estadisticas(valores_viajante, tiempos_viajante, contador_validos_viajante, promedio_viajante)

# Imprimir resultados
print("=== RESULTADOS DE LA EXPERIMENTACIÓN ===")
print(f"AG - Promedio: {stats_ag['promedio']}")
print(f"PSO - Promedio: {stats_pso['promedio']}")
print(f"TS - Promedio: {stats_ts['promedio']}")
print(f"Viajante - Promedio: {stats_viajante['promedio']}")

print("\n--- Estadísticas de Valores ---")
for nombre, stats in [('AG', stats_ag), ('PSO', stats_pso), ('TS', stats_ts), ('Viajante', stats_viajante)]:
    print(f"{nombre}: Media={stats['valores']['mean']}, Std={stats['valores']['std']}, Min={stats['valores']['min']}, Max={stats['valores']['max']}")

print("\n--- Estadísticas de Tiempos ---")
for nombre, stats in [('AG', stats_ag), ('PSO', stats_pso), ('TS', stats_ts), ('Viajante', stats_viajante)]:
    print(f"{nombre}: Media={stats['tiempos']['mean']}, Std={stats['tiempos']['std']}, Min={stats['tiempos']['min']}, Max={stats['tiempos']['max']}")

# Guardar análisis estadístico de valores en CSV
with open('analisis_estadistico_valores.csv', 'w', newline='') as f_stats:
    writer = csv.writer(f_stats)
    writer.writerow(['resolvedor', 'media', 'desviacion_estandar', 'minimo', 'maximo', 'num_muestras'])
    writer.writerow(['AG', stats_ag['valores']['mean'], stats_ag['valores']['std'], stats_ag['valores']['min'], stats_ag['valores']['max'], len(valores_ag)])
    writer.writerow(['PSO', stats_pso['valores']['mean'], stats_pso['valores']['std'], stats_pso['valores']['min'], stats_pso['valores']['max'], len(valores_pso)])
    writer.writerow(['TS', stats_ts['valores']['mean'], stats_ts['valores']['std'], stats_ts['valores']['min'], stats_ts['valores']['max'], len(valores_ts)])
    writer.writerow(['viajante', stats_viajante['valores']['mean'], stats_viajante['valores']['std'], stats_viajante['valores']['min'], stats_viajante['valores']['max'], len(valores_viajante)])

# Guardar análisis estadístico de tiempos en CSV
with open('analisis_estadistico_tiempos.csv', 'w', newline='') as f_stats_time:
    writer = csv.writer(f_stats_time)
    writer.writerow(['resolvedor', 'media', 'desviacion_estandar', 'minimo', 'maximo', 'num_muestras'])
    writer.writerow(['AG', stats_ag['tiempos']['mean'], stats_ag['tiempos']['std'], stats_ag['tiempos']['min'], stats_ag['tiempos']['max'], len(tiempos_ag)])
    writer.writerow(['PSO', stats_pso['tiempos']['mean'], stats_pso['tiempos']['std'], stats_pso['tiempos']['min'], stats_pso['tiempos']['max'], len(tiempos_pso)])
    writer.writerow(['TS', stats_ts['tiempos']['mean'], stats_ts['tiempos']['std'], stats_ts['tiempos']['min'], stats_ts['tiempos']['max'], len(tiempos_ts)])
    writer.writerow(['viajante', stats_viajante['tiempos']['mean'], stats_viajante['tiempos']['std'], stats_viajante['tiempos']['min'], stats_viajante['tiempos']['max'], len(tiempos_viajante)])

# Crear visualizaciones mejoradas
plt.figure(figsize=(16, 10))

# Histogramas de valores
plt.subplot(3, 4, 1)
plt.hist(valores_ag, bins=10, color='skyblue', edgecolor='black', alpha=0.7)
plt.title('Histograma de valores - AG')
plt.xlabel('Valor del itinerario')
plt.ylabel('Frecuencia')

plt.subplot(3, 4, 2)
plt.hist(valores_pso, bins=10, color='salmon', edgecolor='black', alpha=0.7)
plt.title('Histograma de valores - PSO')
plt.xlabel('Valor del itinerario')
plt.ylabel('Frecuencia')

plt.subplot(3, 4, 3)
plt.hist(valores_ts, bins=10, color='lightgreen', edgecolor='black', alpha=0.7)
plt.title('Histograma de valores - TS')
plt.xlabel('Valor del itinerario')
plt.ylabel('Frecuencia')

plt.subplot(3, 4, 4)
plt.hist(valores_viajante, bins=10, color='orange', edgecolor='black', alpha=0.7)
plt.title('Histograma de valores - Viajante')
plt.xlabel('Valor del itinerario')
plt.ylabel('Frecuencia')

# Histogramas de tiempos
plt.subplot(3, 4, 5)
plt.hist(tiempos_ag, bins=10, color='skyblue', edgecolor='black', alpha=0.7)
plt.title('Histograma de tiempos - AG')
plt.xlabel('Tiempo (s)')
plt.ylabel('Frecuencia')

plt.subplot(3, 4, 6)
plt.hist(tiempos_pso, bins=10, color='salmon', edgecolor='black', alpha=0.7)
plt.title('Histograma de tiempos - PSO')
plt.xlabel('Tiempo (s)')
plt.ylabel('Frecuencia')

plt.subplot(3, 4, 7)
plt.hist(tiempos_ts, bins=10, color='lightgreen', edgecolor='black', alpha=0.7)
plt.title('Histograma de tiempos - TS')
plt.xlabel('Tiempo (s)')
plt.ylabel('Frecuencia')

plt.subplot(3, 4, 8)
plt.hist(tiempos_viajante, bins=10, color='orange', edgecolor='black', alpha=0.7)
plt.title('Histograma de tiempos - Viajante')
plt.xlabel('Tiempo (s)')
plt.ylabel('Frecuencia')

# Boxplots
plt.subplot(3, 2, 5)
data_valores = [valores_ag, valores_pso, valores_ts, valores_viajante]
labels = ['AG', 'PSO', 'TS', 'Viajante']
plt.boxplot([d for d in data_valores if len(d) > 0], labels=[l for i, l in enumerate(labels) if len(data_valores[i]) > 0])
plt.title('Comparación de valores de itinerarios')
plt.ylabel('Valor del itinerario')
plt.xticks(rotation=45)

plt.subplot(3, 2, 6)
data_tiempos = [tiempos_ag, tiempos_pso, tiempos_ts, tiempos_viajante]
plt.boxplot([d for d in data_tiempos if len(d) > 0], labels=[l for i, l in enumerate(labels) if len(data_tiempos[i]) > 0])
plt.title('Comparación de tiempos de ejecución')
plt.ylabel('Tiempo (s)')
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig("analisis_completo_tiempo_resolvedores.png", dpi=300, bbox_inches='tight')
plt.show()

# Crear gráfico de dispersión tiempo vs valor
plt.figure(figsize=(12, 8))
colores = ['skyblue', 'salmon', 'lightgreen', 'orange']
algoritmos = ['AG', 'PSO', 'TS', 'Viajante']
datos_algoritmos = [(tiempos_ag, valores_ag), (tiempos_pso, valores_pso), (tiempos_ts, valores_ts), 
                   (tiempos_viajante, valores_viajante)]

for i, (tiempos, valores) in enumerate(datos_algoritmos):
    if len(tiempos) > 0 and len(valores) > 0:
        plt.scatter(tiempos, valores, color=colores[i], label=algoritmos[i], alpha=0.7, s=50)

plt.xlabel('Tiempo de ejecución (s)')
plt.ylabel('Valor del itinerario')
plt.title('Relación entre tiempo de ejecución y valor del itinerario')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig("tiempo_vs_valor_resolvedor.png", dpi=300, bbox_inches='tight')
plt.show()
plt.ylabel('Tiempo (s)')
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig("analisis_completo_resolvedores.png", dpi=300, bbox_inches='tight')
plt.show()

# Crear gráfico de dispersión tiempo vs valor
plt.figure(figsize=(12, 8))
colores = ['skyblue', 'salmon', 'lightgreen', 'violet', 'orange']
algoritmos = ['AG', 'PSO', 'TS', 'Fuerza Bruta', 'Viajante']
datos_algoritmos = [(tiempos_ag, valores_ag), (tiempos_pso, valores_pso), (tiempos_ts, valores_ts), 
                    (tiempos_viajante, valores_viajante)]

for i, (tiempos, valores) in enumerate(datos_algoritmos):
    if len(tiempos) > 0 and len(valores) > 0:
        plt.scatter(tiempos, valores, color=colores[i], label=algoritmos[i], alpha=0.7, s=50)

plt.xlabel('Tiempo de ejecución (s)')
plt.ylabel('Valor del itinerario')
plt.title('Relación entre tiempo de ejecución y valor del itinerario')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig("tiempo_vs_valor_resolvedores.png", dpi=300, bbox_inches='tight')
plt.show()
