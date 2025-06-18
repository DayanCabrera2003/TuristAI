import random
from .mapaCuba import dist_recorrido

"""
En este módulo se implementan las metaheurísticas Algoritmo Genético (GA), Enjambre de Partículas (PSO) y
Colonia de Hormigas (ACO) para la optimización de itinerarios turísticos.
"""

class MetaheuristicasItinerario:
    def __init__(self, lugares_turisticos=None, preferencias_tipos_lugares=None, preferencias_lugares=None,
                 presupuesto_max=0, min_presupuesto=False, max_lugares=False):
        
        self.lugares_turisticos = lugares_turisticos if lugares_turisticos is not None else []
        self.variables = {}  # a cada variable se le asigna una actividad de la lista actividades
        self.preferencias_actividades = preferencias_tipos_lugares if preferencias_tipos_lugares is not None else []
        self.preferencias_lugares = preferencias_lugares if preferencias_lugares is not None else []
        self.presupuesto_max = presupuesto_max
        self.min_presupuesto = min_presupuesto
        self.max_lugares = max_lugares

    def evaluar_itinerario(self, actividades):
        evaluacion = 0

        actividades_cubiertas = [False] * len(self.preferencias_actividades)
        lugares_cubiertos = [False] * len(self.preferencias_lugares)
        total_costo = 0

        for actividad in actividades:
            # Maximizar lugares visitados
            if self.max_lugares:
                evaluacion += len(actividad.get("lugares_a_visitar", []))
            # Minimizar presupuesto
            if self.min_presupuesto:
                total_costo += actividad.get("costo", 0)
            # Preferencias de tipo de actividad
            for i, tipo in enumerate(self.preferencias_actividades):
                for tipo_actividad_propuesta in actividad.get("tipo_actividad"):
                    if tipo_actividad_propuesta == tipo:
                        evaluacion += 1 if  actividades_cubiertas[i] else 2 # Mayor peso por cubrir preferencia
                        actividades_cubiertas[i] = True 
            # Preferencias de lugares
            for lugar in actividad.get("lugares_a_visitar", []):
                for i, lugar_preferido in enumerate(self.preferencias_lugares):
                    if lugar == lugar_preferido:
                        evaluacion += 1 if lugares_cubiertos[i] else 2
                        lugares_cubiertos[i] = True

        # Penalización por no cubrir preferencias
        penalizacion = actividades_cubiertas.count(False) + lugares_cubiertos.count(False)
        evaluacion -= penalizacion

        # Penalización si se excede el presupuesto
        if self.min_presupuesto and total_costo > self.presupuesto_max > 0:
            evaluacion -= (total_costo - self.presupuesto_max) / 10  # Penaliza el exceso

        return evaluacion

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
        """Mutación: reemplaza aleatoriamente una actividad por otra."""
        nuevo = itinerario[:]
        for i in range(len(nuevo)):
            if random.random() < prob_mutacion:
                opciones = [a for a in actividades_disponibles if a not in nuevo]
                if opciones:
                    nuevo[i] = random.choice(opciones)
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
            tam_itinerario = random.randint(1, min(5, len(self.lugares_turisticos)))
            individuo = random.sample(self.lugares_turisticos, tam_itinerario)
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
            tam_itinerario = random.randint(1, min(5, len(self.lugares_turisticos)))
            individuo = random.sample(self.lugares_turisticos, tam_itinerario)
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
                    # Reemplazar actividad por una aleatoria no repetida
                    opciones = [a for a in self.lugares_turisticos if a not in nueva_particula]
                    if opciones:
                        nueva_particula[idx % len(nueva_particula)] = random.choice(opciones)
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
