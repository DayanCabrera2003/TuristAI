import random
from .mapaCuba import dist_recorrido
"""
En este módulo se implementan las metaheurísticas Algoritmo Genético (GA), Enjambre de Partículas (PSO) y
Colonia de Hormigas (ACO) para la optimización de itinerarios turísticos.
"""

class MetaheuristicasItinerario:
    def __init__(self, lugares_turisticos=None, preferencias_tipos_lugares=None, preferencias_lugares=None,
                 presupuesto_max=0, min_presupuesto=False, max_lugares=False, dias_vacaciones=7):
        
        self.lugares_turisticos = lugares_turisticos if lugares_turisticos is not None else []
        # self.variables = {}  # a cada variable se le asigna una actividad de la lista actividades
        self.preferencias_actividades = preferencias_tipos_lugares if preferencias_tipos_lugares is not None else []
        self.preferencias_lugares = preferencias_lugares if preferencias_lugares is not None else []
        self.presupuesto_max = presupuesto_max
        self.min_presupuesto = min_presupuesto
        self.max_lugares = max_lugares
        self.dias_vacaciones = dias_vacaciones  # Nuevo parámetro

    def evaluar_itinerario(self, actividades):
        evaluacion = 0.0

        actividades_cubiertas = [False] * len(self.preferencias_actividades)
        lugares_cubiertos = [False] * len(self.preferencias_lugares)
        total_costo = 0.0
        total_lugares = 0

        # Pesos ajustables para cada criterio
        peso_lugares = 10
        peso_tipo_pref = 30
        peso_lugar_pref = 30
        peso_distancia = 10
        peso_presupuesto = 1

        for actividad in actividades:
            lugares_visitar = actividad.get("lugares_a_visitar", [])
            total_lugares += len(lugares_visitar)
            total_costo += actividad.get("costo", 0)

            # Preferencias de tipo de actividad
            tipos_actividad = actividad.get("tipo_actividad", [])
            for i, tipo in enumerate(self.preferencias_actividades):
                if tipo in tipos_actividad and not actividades_cubiertas[i]:
                    evaluacion += peso_tipo_pref
                    actividades_cubiertas[i] = True

            # Preferencias de lugares
            for lugar in lugares_visitar:
                for i, lugar_preferido in enumerate(self.preferencias_lugares):
                    if lugar == lugar_preferido and not lugares_cubiertos[i]:
                        evaluacion += peso_lugar_pref
                        lugares_cubiertos[i] = True

        # Maximizar lugares visitados (solo si se desea)
        if self.max_lugares:
            evaluacion += peso_lugares * total_lugares

        # Penalización por no cubrir preferencias
        penalizacion = actividades_cubiertas.count(False) * peso_tipo_pref + lugares_cubiertos.count(False) * peso_lugar_pref
        evaluacion -= penalizacion

        # Penaliza la distancia total recorrida (más distancia, menor evaluación)
        lugares_totales = [lugar for actividad in actividades for lugar in actividad.get("lugares_a_visitar", [])]
        if lugares_totales:
            evaluacion -= peso_distancia * (dist_recorrido(lugares_totales) / 1000)

        # Penalización si se excede el presupuesto
        if self.min_presupuesto and self.presupuesto_max > 0 and total_costo > self.presupuesto_max:
            evaluacion -= peso_presupuesto * (total_costo - self.presupuesto_max)

        # Bonificación si se ajusta bien al presupuesto
        if self.min_presupuesto and self.presupuesto_max > 0 and total_costo <= self.presupuesto_max:
            evaluacion += peso_presupuesto * (self.presupuesto_max - total_costo) / self.presupuesto_max

        return evaluacion/100 + 15

    # Metaheurística: Algoritmo Genético
    def cruzar(self, padre1, padre2):
        """Cruza dos itinerarios (listas de actividades) usando un punto de corte."""
        if not padre1 or not padre2 or min(len(padre1), len(padre2)) < 2:
            return padre1[:], padre2[:]
        punto = random.randint(1, min(len(padre1), len(padre2)) - 1)
        hijo1 = padre1[:punto] + padre2[punto:]
        hijo2 = padre2[:punto] + padre1[punto:]
        return hijo1, hijo2

    def mutar(self, itinerario, actividades_disponibles, prob_mutacion=0.1):
        """Mutación: reemplaza aleatoriamente una actividad por otra (puede haber repetidas)."""
        nuevo = itinerario[:]
        for i in range(len(nuevo)):
            if random.random() < prob_mutacion:
                nuevo[i] = random.choice(actividades_disponibles)
        return nuevo

    def seleccionar(self, poblacion, fitnesses, num_seleccionados):
        """Selecciona los mejores individuos según su fitness."""
        seleccionados = sorted(zip(poblacion, fitnesses), key=lambda x: x[1], reverse=True)
        return [ind for ind, fit in seleccionados[:num_seleccionados]]

    def algoritmo_genetico_itinerario(self, tam_poblacion=30, generaciones=50):
        """
        Optimiza el itinerario usando un algoritmo genético.
        Retorna el mejor itinerario encontrado.
        """
        if not self.lugares_turisticos:
            print("No hay lugares turísticos disponibles para generar el itinerario.")
            return []

        # Inicialización aleatoria de la población
        poblacion = []
        for _ in range(tam_poblacion):
            # El itinerario tiene tamaño igual a dias_vacaciones, permitiendo repetidos
            individuo = [random.choice(self.lugares_turisticos) for _ in range(self.dias_vacaciones)]
            poblacion.append(individuo)

        for _ in range(generaciones):
            # Evaluar fitness
            fitnesses = [self.evaluar_itinerario(ind) for ind in poblacion]
            # Selección
            seleccionados = self.seleccionar(poblacion, fitnesses, tam_poblacion // 2)
            # Cruzamiento y mutación para crear nueva población
            nueva_poblacion = seleccionados[:]
            while len(nueva_poblacion) < tam_poblacion:
                padres = random.sample(seleccionados, 2)
                hijo1, hijo2 = self.cruzar(padres[0], padres[1])
                hijo1 = self.mutar(hijo1, self.lugares_turisticos)
                hijo2 = self.mutar(hijo2, self.lugares_turisticos)
                nueva_poblacion.extend([hijo1, hijo2])
            poblacion = nueva_poblacion[:tam_poblacion]

        # Seleccionar el mejor individuo final
        fitnesses = [self.evaluar_itinerario(ind) for ind in poblacion]
        mejor_indice = fitnesses.index(max(fitnesses))
        return poblacion[mejor_indice], fitnesses[mejor_indice]

    # Metaheurística: Enjambre de Partículas (PSO)
    def pso_itinerario(self, num_particulas=30, iteraciones=50, w=0.5, c1=1.5, c2=1.5):
        """
        Optimiza el itinerario usando Enjambre de Partículas (PSO).
        Cada partícula es un itinerario (lista de actividades).
        """
        # Inicialización de partículas
        particulas = []
        velocidades = []
        mejor_personal = []
        mejor_personal_fitness = []

        for _ in range(num_particulas):
            individuo = [random.choice(self.lugares_turisticos) for _ in range(self.dias_vacaciones)]
            particulas.append(individuo)
            velocidades.append([])  # Velocidad como lista de swaps (índices a intercambiar)
            mejor_personal.append(individuo[:])
            mejor_personal_fitness.append(self.evaluar_itinerario(individuo))

        # Mejor global
        mejor_global = mejor_personal[mejor_personal_fitness.index(max(mejor_personal_fitness))]
        mejor_global_fitness = max(mejor_personal_fitness)

        for _ in range(iteraciones):
            for i, particula in enumerate(particulas):
                # Actualizar velocidad (como swaps aleatorios)
                nueva_velocidad = []
                if random.random() < w:
                    # Inercia: mantener swaps anteriores
                    nueva_velocidad.extend(velocidades[i])
                if random.random() < c1:
                    # Cognitivo: intentar acercarse al mejor personal
                    if particula != mejor_personal[i]:
                        swap_idx = random.randint(0, len(particula)-1)
                        nueva_velocidad.append(swap_idx)
                if random.random() < c2:
                    # Social: intentar acercarse al mejor global
                    if particula != mejor_global:
                        swap_idx = random.randint(0, len(particula)-1)
                        nueva_velocidad.append(swap_idx)
                velocidades[i] = nueva_velocidad

                # Aplicar velocidad (swaps)
                nueva_particula = particula[:]
                for idx in velocidades[i]:
                    nueva_particula[idx % len(nueva_particula)] = random.choice(self.lugares_turisticos)
                particulas[i] = nueva_particula

                # Evaluar fitness
                fit = self.evaluar_itinerario(nueva_particula)
                if fit > mejor_personal_fitness[i]:
                    mejor_personal[i] = nueva_particula[:]
                    mejor_personal_fitness[i] = fit
                    if fit > mejor_global_fitness:
                        mejor_global = nueva_particula[:]
                        mejor_global_fitness = fit

        return mejor_global, mejor_global_fitness
    
    # Metaheurística: Búsqueda Tabú (Tabu Search)
    def tabu_search_itinerario(self, max_iter=50, tabu_tam=10):
        """
        Optimiza el itinerario usando Búsqueda Tabú.
        Retorna el mejor itinerario encontrado y su evaluación.
        """
        if not self.lugares_turisticos:
            print("No hay lugares turísticos disponibles para generar el itinerario.")
            return [], 0.0

        # Solución inicial aleatoria
        tam_itinerario = self.dias_vacaciones
        mejor_solucion = [random.choice(self.lugares_turisticos) for _ in range(tam_itinerario)]
        mejor_fitness = self.evaluar_itinerario(mejor_solucion)
        actual_solucion = mejor_solucion[:]
        actual_fitness = mejor_fitness

        tabu_lista = []

        for _ in range(max_iter):
            vecinos = []
            # Generar vecinos por reemplazo de una actividad (permitiendo repetidos)
            for i in range(len(actual_solucion)):
                for lugar in self.lugares_turisticos:
                    if actual_solucion[i] != lugar:
                        vecino = actual_solucion[:]
                        vecino[i] = lugar
                        if vecino not in tabu_lista:
                            vecinos.append(vecino)
            if not vecinos:
                break

            # Evaluar vecinos
            vecinos_fitness = [self.evaluar_itinerario(v) for v in vecinos]
            mejor_vecino_idx = vecinos_fitness.index(max(vecinos_fitness))
            mejor_vecino = vecinos[mejor_vecino_idx]
            mejor_vecino_fitness = vecinos_fitness[mejor_vecino_idx]

            # Actualizar solución actual
            actual_solucion = mejor_vecino
            actual_fitness = mejor_vecino_fitness

            # Actualizar mejor solución global
            if actual_fitness > mejor_fitness:
                mejor_solucion = actual_solucion[:]
                mejor_fitness = actual_fitness

            # Actualizar lista tabú
            tabu_lista.append(actual_solucion)
            if len(tabu_lista) > tabu_tam:
                tabu_lista.pop(0)

        return mejor_solucion, mejor_fitness