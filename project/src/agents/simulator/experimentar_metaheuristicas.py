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
while(contador < 5):
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
encabezados = ['indice', 'AG', 'PSO', 'TS', 'fuerza_bruta', 'viajante']

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
    for resolvedor in ['viajante']:  # 'AG', 'PSO', 'TS', 
        valor = None
        tiempo = None
        try:
            inicio = time.time()
            result = planificador.generate_itinerary(json_data, resolvedor=resolvedor)
            # Si el resultado es un solo valor, úsalo como valor; si es una tupla, toma el segundo elemento como valor
            if isinstance(result, tuple):
                _, valor = result
            else:
                valor = result
            tiempo = time.time() - inicio
        except KeyError as e:
            print(f"[{resolvedor}] Error: {e} - No se encontró un bloque JSON o la clave 'lugares'")
        except Exception as e:
            print(f"[{resolvedor}] Error inesperado: {e}")
        if isinstance(valor, (int, float)):
            fila_valores.append(valor)
            fila_tiempos.append(tiempo)
            resultados.append((resolvedor, valor, tiempo))
    return fila_valores, fila_tiempos, resultados

# --- Ejecutar secuencialmente todas las muestras ---
for i in range(len(muestra)-1):
    media_dias = 15.5
    desviacion_dias = 30 / 6
    dias_vacaciones = int(round(random.gauss(media_dias, desviacion_dias)))
    dias_vacaciones = max(1, min(dias_vacaciones, 30))

    planificador = Planer(
        muestra[i],
        muestraluagres[i],
        dias_vacaciones,
        1000
    )
    fila_valores, fila_tiempos, resultados = ejecutar_resolvedores(planificador, i)
    for resolvedor, valor, tiempo in resultados:
        # Guardar para análisis estadístico solo para AG, PSO, TS, fuerza_bruta y viajante
        if resolvedor == 'AG' and isinstance(valor, (int, float)):
            promedio1 += valor
            contador_validos1 += 1
            valores_ag.append(valor)
            if isinstance(tiempo, (int, float)):
                tiempos_ag.append(tiempo)
        if resolvedor == 'PSO' and isinstance(valor, (int, float)):
            promedio2 += valor
            contador_validos2 += 1
            valores_pso.append(valor)
            if isinstance(tiempo, (int, float)):
                tiempos_pso.append(tiempo)
        if resolvedor == 'TS' and isinstance(valor, (int, float)):
            promedio3 += valor
            contador_validos3 += 1
            valores_ts.append(valor)
            if isinstance(tiempo, (int, float)):
                tiempos_ts.append(tiempo)
        if resolvedor == 'fuerza_bruta' and isinstance(valor, (int, float)):
            if 'valores_fuerza_bruta' not in locals():
                valores_fuerza_bruta = []
                tiempos_fuerza_bruta = []
                contador_validos_fuerza_bruta = 0
                valores_fuerza_bruta.append(valor)
                contador_validos_fuerza_bruta += 1
                if isinstance(tiempo, (int, float)):
                    tiempos_fuerza_bruta.append(tiempo)
        if resolvedor == 'viajante' and isinstance(valor, (int, float)):
            if 'valores_viajante' not in locals():
                valores_viajante = []
                tiempos_viajante = []
                contador_validos_viajante = 0
                valores_viajante.append(valor)
                contador_validos_viajante += 1
                if isinstance(tiempo, (int, float)):
                    tiempos_viajante.append(tiempo)

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

# Estadísticas para AG
if contador_validos1 > 0:
    promedio1 /= contador_validos1
    ag_mean = np.mean(valores_ag)
    ag_std = np.std(valores_ag)
    ag_min = np.min(valores_ag)
    ag_max = np.max(valores_ag)
    ag_time_mean = np.mean(tiempos_ag) if tiempos_ag else "N/A"
    ag_time_std = np.std(tiempos_ag) if tiempos_ag else "N/A"
    ag_time_min = np.min(tiempos_ag) if tiempos_ag else "N/A"
    ag_time_max = np.max(tiempos_ag) if tiempos_ag else "N/A"
else:
    promedio1 = "No hay resultados válidos para AG"
    ag_mean = ag_std = ag_min = ag_max = "N/A"
    ag_time_mean = ag_time_std = ag_time_min = ag_time_max = "N/A"

# Estadísticas para PSO
if contador_validos2 > 0:
    promedio2 /= contador_validos2
    pso_mean = np.mean(valores_pso)
    pso_std = np.std(valores_pso)
    pso_min = np.min(valores_pso)
    pso_max = np.max(valores_pso)
    pso_time_mean = np.mean(tiempos_pso) if tiempos_pso else "N/A"
    pso_time_std = np.std(tiempos_pso) if tiempos_pso else "N/A"
    pso_time_min = np.min(tiempos_pso) if tiempos_pso else "N/A"
    pso_time_max = np.max(tiempos_pso) if tiempos_pso else "N/A"
else:
    promedio2 = "No hay resultados válidos para PSO"
    pso_mean = pso_std = pso_min = pso_max = "N/A"
    pso_time_mean = pso_time_std = pso_time_min = pso_time_max = "N/A"

# Estadísticas para TS
if 'contador_validos3' in locals() and contador_validos3 > 0:
    promedio3 /= contador_validos3
    ts_mean = np.mean(valores_ts)
    ts_std = np.std(valores_ts)
    ts_min = np.min(valores_ts)
    ts_max = np.max(valores_ts)
    ts_time_mean = np.mean(tiempos_ts) if tiempos_ts else "N/A"
    ts_time_std = np.std(tiempos_ts) if tiempos_ts else "N/A"
    ts_time_min = np.min(tiempos_ts) if tiempos_ts else "N/A"
    ts_time_max = np.max(tiempos_ts) if tiempos_ts else "N/A"
else:
    promedio3 = "No hay resultados válidos para TS"
    ts_mean = ts_std = ts_min = ts_max = "N/A"
    ts_time_mean = ts_time_std = ts_time_min = ts_time_max = "N/A"

# Estadísticas para fuerza bruta
if 'valores_fuerza_bruta' in locals() and len(valores_fuerza_bruta) > 0:
    fuerza_bruta_mean = np.mean(valores_fuerza_bruta)
    fuerza_bruta_std = np.std(valores_fuerza_bruta)
    fuerza_bruta_min = np.min(valores_fuerza_bruta)
    fuerza_bruta_max = np.max(valores_fuerza_bruta)
    fuerza_bruta_time_mean = np.mean(tiempos_fuerza_bruta) if tiempos_fuerza_bruta else "N/A"
    fuerza_bruta_time_std = np.std(tiempos_fuerza_bruta) if tiempos_fuerza_bruta else "N/A"
    fuerza_bruta_time_min = np.min(tiempos_fuerza_bruta) if tiempos_fuerza_bruta else "N/A"
    fuerza_bruta_time_max = np.max(tiempos_fuerza_bruta) if tiempos_fuerza_bruta else "N/A"
else:
    fuerza_bruta_mean = fuerza_bruta_std = fuerza_bruta_min = fuerza_bruta_max = "N/A"
    fuerza_bruta_time_mean = fuerza_bruta_time_std = fuerza_bruta_time_min = fuerza_bruta_time_max = "N/A"

# Estadísticas para viajante
if 'valores_viajante' in locals() and len(valores_viajante) > 0:
    viajante_mean = np.mean(valores_viajante)
    viajante_std = np.std(valores_viajante)
    viajante_min = np.min(valores_viajante)
    viajante_max = np.max(valores_viajante)
    viajante_time_mean = np.mean(tiempos_viajante) if tiempos_viajante else "N/A"
    viajante_time_std = np.std(tiempos_viajante) if tiempos_viajante else "N/A"
    viajante_time_min = np.min(tiempos_viajante) if tiempos_viajante else "N/A"
    viajante_time_max = np.max(tiempos_viajante) if tiempos_viajante else "N/A"
else:
    viajante_mean = viajante_std = viajante_min = viajante_max = "N/A"
    viajante_time_mean = viajante_time_std = viajante_time_min = viajante_time_max = "N/A"

print("Promedio de valor de los itinerarios que genera la metaheuristica AG: " + str(promedio1))
print("Promedio de valor de los itinerarios que genera la metaheuristica PSO: " + str(promedio2))
print("Promedio de valor de los itinerarios que genera la metaheuristica TS: " + str(promedio3))
print("\n--- Estadísticas AG ---")
print(f"Media: {ag_mean}, Desviación estándar: {ag_std}, Mínimo: {ag_min}, Máximo: {ag_max}")
print("\n--- Estadísticas PSO ---")
print(f"Media: {pso_mean}, Desviación estándar: {pso_std}, Mínimo: {pso_min}, Máximo: {pso_max}")
print("\n--- Estadísticas TS ---")
print(f"Media: {ts_mean}, Desviación estándar: {ts_std}, Mínimo: {ts_min}, Máximo: {ts_max}")
print("\n--- Estadísticas Fuerza Bruta ---")
print(f"Media: {fuerza_bruta_mean}, Desviación estándar: {fuerza_bruta_std}, Mínimo: {fuerza_bruta_min}, Máximo: {fuerza_bruta_max}")
print("\n--- Estadísticas Viajante ---")
print(f"Media: {viajante_mean}, Desviación estándar: {viajante_std}, Mínimo: {viajante_min}, Máximo: {viajante_max}")

# Guardar análisis estadístico de valores en CSV
with open('analisis_estadistico_valores.csv', 'w', newline='') as f_stats:
    writer = csv.writer(f_stats)
    writer.writerow(['resolvedor', 'media', 'desviacion_estandar', 'minimo', 'maximo'])
    writer.writerow(['AG', ag_mean, ag_std, ag_min, ag_max])
    writer.writerow(['PSO', pso_mean, pso_std, pso_min, pso_max])
    writer.writerow(['TS', ts_mean, ts_std, ts_min, ts_max])
    writer.writerow(['fuerza_bruta', fuerza_bruta_mean, fuerza_bruta_std, fuerza_bruta_min, fuerza_bruta_max])
    writer.writerow(['viajante', viajante_mean, viajante_std, viajante_min, viajante_max])

# Guardar análisis estadístico de tiempos en CSV
with open('analisis_estadistico_tiempos.csv', 'w', newline='') as f_stats_time:
    writer = csv.writer(f_stats_time)
    writer.writerow(['resolvedor', 'media', 'desviacion_estandar', 'minimo', 'maximo'])
    writer.writerow(['AG', ag_time_mean, ag_time_std, ag_time_min, ag_time_max])
    writer.writerow(['PSO', pso_time_mean, pso_time_std, pso_time_min, pso_time_max])
    writer.writerow(['TS', ts_time_mean, ts_time_std, ts_time_min, ts_time_max])
    writer.writerow(['fuerza_bruta', fuerza_bruta_time_mean, fuerza_bruta_time_std, fuerza_bruta_time_min, fuerza_bruta_time_max])
    writer.writerow(['viajante', viajante_time_mean, viajante_time_std, viajante_time_min, viajante_time_max])

plt.figure(figsize=(18, 5))

# Histograma de valores AG
plt.subplot(1, 5, 1)
plt.hist(valores_ag, bins=10, color='skyblue', edgecolor='black')
plt.title('Histograma de valores - AG')
plt.xlabel('Valor del itinerario')
plt.ylabel('Frecuencia')

# Histograma de valores PSO
plt.subplot(1, 5, 2)
plt.hist(valores_pso, bins=10, color='salmon', edgecolor='black')
plt.title('Histograma de valores - PSO')
plt.xlabel('Valor del itinerario')
plt.ylabel('Frecuencia')

# Histograma de valores TS
plt.subplot(1, 5, 3)
plt.hist(valores_ts, bins=10, color='lightgreen', edgecolor='black')
plt.title('Histograma de valores - TS')
plt.xlabel('Valor del itinerario')
plt.ylabel('Frecuencia')

# Histograma de valores Fuerza Bruta
plt.subplot(1, 5, 4)
plt.hist(valores_fuerza_bruta if 'valores_fuerza_bruta' in locals() else [], bins=10, color='violet', edgecolor='black')
plt.title('Histograma de valores - Fuerza Bruta')
plt.xlabel('Valor del itinerario')
plt.ylabel('Frecuencia')

# Histograma de valores Viajante
plt.subplot(1, 5, 5)
plt.hist(valores_viajante if 'valores_viajante' in locals() else [], bins=10, color='orange', edgecolor='black')
plt.title('Histograma de valores - Viajante')
plt.xlabel('Valor del itinerario')
plt.ylabel('Frecuencia')

plt.tight_layout()
plt.savefig("histogramas_ag_pso_ts_fuerzabruta_viajante.png")

# Boxplot comparativo
plt.figure(figsize=(10, 5))
data_boxplot = [valores_ag, valores_pso, valores_ts]
labels_boxplot = ['AG', 'PSO', 'TS']
if 'valores_fuerza_bruta' in locals():
    data_boxplot.append(valores_fuerza_bruta)
    labels_boxplot.append('Fuerza Bruta')
if 'valores_viajante' in locals():
    data_boxplot.append(valores_viajante)
    labels_boxplot.append('Viajante')
plt.boxplot(data_boxplot, labels=labels_boxplot)
plt.title('Comparación de valores de itinerarios')
plt.ylabel('Valor del itinerario')
plt.savefig("boxplot_ag_pso_ts_fuerzabruta_viajante.png")
plt.show()
