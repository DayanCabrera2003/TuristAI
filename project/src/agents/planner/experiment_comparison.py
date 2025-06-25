import json
import time
from .planning import Planer
from .metaheuristicas import MetaheuristicasItinerario
from ..rag.rag import ChatUtils

class ItineraryExperiment:
    """
    Clase para comparar la efectividad entre:
    1. Formulario estructurado (opciones restringidas)
    2. Lenguaje natural libre del usuario
    """
    
    def __init__(self):
        self.utils = ChatUtils()
        self.results = {
            "structured_form": [],
            "natural_language": []
        }
    
    def analyze_itinerary_robust(self, itinerary, optimization_score, preferences):
        """
        Analiza la calidad de un itinerario usando el score de optimización ya calculado y métricas adicionales.
        
        Args:
            itinerary: Lista de lugares del itinerario
            optimization_score: Score ya calculado por las metaheurísticas durante la optimización
            preferences: Dict con actividades, lugares preferidos, presupuesto, etc.
        """
        if not itinerary:
            return {
                'num_places': 0,
                'total_cost': 0,
                'optimization_score': 0,
                'coverage_score': 0,
                'diversity_score': 0,
                'budget_score': 0,
                'is_valid': False,
                'budget_efficiency': 0
            }
        
        num_places = len(itinerary)
        
        # Calcular costo total de manera segura
        total_cost = 0
        for place in itinerary:
            price = place.get('precio', place.get('costo', 0))
            if price and price != 'N/A':
                try:
                    if isinstance(price, str):
                        price = price.replace('$', '').replace(',', '')
                        total_cost += float(price)
                    else:
                        total_cost += float(price)
                except (ValueError, TypeError):
                    pass
        
        # Usar el score de optimización ya calculado (NO re-evaluar)
        quality_score = optimization_score
        
        # Preparar datos para métricas adicionales
        actividades_preferidas = preferences.get('actividades', preferences.get('lugares', []))
        presupuesto = preferences.get('presupuesto_disponible', preferences.get('presupuesto', 1000))
        
        # Calcular métricas independientes de evaluación
        coverage_score = 0
        diversity_score = 0
        budget_score = 0
        
        # Evaluar cobertura de actividades preferidas
        if actividades_preferidas:
            covered_activities = 0
            for place in itinerary:
                place_type = place.get('tipo_actividad', [])
                place_name = place.get('nombre', '').lower()
                if isinstance(place_type, list):
                    place_type = [t.lower() for t in place_type]
                else:
                    place_type = [str(place_type).lower()]
                
                for activity in actividades_preferidas:
                    activity_lower = activity.lower()
                    if (any(activity_lower in t for t in place_type) or 
                        activity_lower in place_name):
                        covered_activities += 1
                        break
            coverage_score = (covered_activities / len(actividades_preferidas)) * 100
        
        # Evaluar diversidad geográfica (número de ciudades diferentes)
        unique_cities = set()
        for place in itinerary:
            city = place.get('ciudad', '')
            if city:
                unique_cities.add(city)
        diversity_score = len(unique_cities)
        
        # Evaluar ajuste al presupuesto
        if presupuesto > 0:
            budget_usage = total_cost / presupuesto
            if budget_usage <= 1:
                budget_score = 100 - (budget_usage * 30)  # Puntuación alta si usa el presupuesto eficientemente
            else:
                budget_score = max(0, 100 - ((budget_usage - 1) * 100))  # Penalización si excede
        
        return {
            'num_places': num_places,
            'total_cost': total_cost,
            'optimization_score': quality_score,
            'coverage_score': coverage_score,
            'diversity_score': diversity_score,
            'budget_score': budget_score,
            'is_valid': num_places > 0 and total_cost <= presupuesto,
            'budget_efficiency': num_places / max(total_cost, 1)  # lugares por dólar
        }

    def structured_form_approach(self, tipolugares, lugares, dias_vacaciones, presupuesto_disponible, 
                                max_cant_lugares=True, min_presupuesto=False, metaheuristic="AG"):
        """
        Enfoque 1: Formulario estructurado con opciones predefinidas
        """
        start_time = time.time()
        
        planer = Planer(
            tipolugares=tipolugares,
            lugares=lugares, 
            dias_vacaciones=dias_vacaciones,
            presupuesto_disponible=presupuesto_disponible,
            max_cant_lugares=max_cant_lugares,
            min_presupuesto=min_presupuesto
        )
        
        itinerario, valor = planer.generate_itinerary(metaheuristic)
        
        end_time = time.time()
        
        # Análisis robusto del itinerario usando el score de optimización ya calculado
        preferences = {
            'actividades': lugares,
            'lugares_preferidos': tipolugares,
            'presupuesto_disponible': presupuesto_disponible
        }
        
        analysis = self.analyze_itinerary_robust(itinerario, valor, preferences)
        
        result = {
            "approach": "structured_form",
            "execution_time": end_time - start_time,
            "itinerary": itinerario,
            "optimization_value": valor,
            "analysis": analysis,
            "parameters": {
                "tipolugares": tipolugares,
                "lugares": lugares,
                "dias_vacaciones": dias_vacaciones,
                "presupuesto_disponible": presupuesto_disponible,
                "max_cant_lugares": max_cant_lugares,
                "min_presupuesto": min_presupuesto
            }
        }
        
        self.results["structured_form"].append(result)
        return result
    
    def natural_language_approach(self, user_query, metaheuristic="AG"):
        """
        Enfoque 2: Lenguaje natural libre - extrae parámetros automáticamente
        """
        start_time = time.time()
        
        # Esquema para extraer parámetros del lenguaje natural
        extraction_schema = {
            "type": "object",
            "properties": {
                "tipolugares": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "Isla de la Juventud", "Pinar del Rio", "Artemisa", "La Habana", "Mayabeque",
                            "Matanzas", "Cienfuegos", "Villa Clara", "Sancti Spiritus", "Ciego de Avila",
                            "Camaguey", "Las Tunas", "Granma", "Holguin", "Santiago de Cuba", "Guantanamo"
                        ]
                    },
                    "description": "Provincias mencionadas o inferidas del texto"
                },
                "lugares": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tipos de lugares o actividades específicas mencionadas"
                },
                "dias_vacaciones": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 30,
                    "description": "Número de días de vacaciones mencionados"
                },
                "presupuesto_disponible": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Presupuesto disponible en dólares"
                },
                "max_cant_lugares": {
                    "type": "boolean",
                    "description": "Si el usuario prefiere maximizar cantidad de lugares (true) o minimizar costo (false)"
                }
            },
            "required": ["tipolugares", "lugares", "dias_vacaciones", "presupuesto_disponible"]
        }
        
        # Extraer parámetros del lenguaje natural
        extraction_query = f"""
        Analiza la siguiente consulta del usuario y extrae los parámetros para generar un itinerario turístico:
        
        Consulta del usuario: "{user_query}"
        
        Extrae:
        - Provincias de Cuba mencionadas o que puedas inferir
        - Tipos de lugares o actividades que quiere visitar
        - Número de días de vacaciones
        - Presupuesto disponible (si no se menciona, asume un valor razonable)
        - Si prefiere muchos lugares (true) o ahorrar dinero (false)
        """
        
        params_result = self.utils.ask(extraction_query, extraction_schema, 20)
        params_json = self._extract_json(params_result)
        
        if not params_json:
            return {"error": "No se pudieron extraer parámetros del lenguaje natural"}
        
        try:
            params = json.loads(params_json)
        except json.JSONDecodeError:
            return {"error": "Error al decodificar parámetros extraídos"}
        
        # Crear planer con parámetros extraídos
        planer = Planer(
            tipolugares=params.get("tipolugares", []),
            lugares=params.get("lugares", []),
            dias_vacaciones=params.get("dias_vacaciones", 3),
            presupuesto_disponible=params.get("presupuesto_disponible", 500),
            max_cant_lugares=params.get("max_cant_lugares", True),
            min_presupuesto=not params.get("max_cant_lugares", True)
        )
        
        itinerario, valor = planer.generate_itinerary(metaheuristic)
        
        end_time = time.time()
        
        # Análisis robusto del itinerario
        preferences = {
            'actividades': params.get("lugares", []),
            'lugares_preferidos': params.get("tipolugares", []),
            'presupuesto_disponible': params.get("presupuesto_disponible", 500)
        }
        
        analysis = self.analyze_itinerary_robust(itinerario, valor, preferences)
        
        result = {
            "approach": "natural_language",
            "execution_time": end_time - start_time,
            "original_query": user_query,
            "extracted_parameters": params,
            "itinerary": itinerario,
            "optimization_value": valor,
            "analysis": analysis
        }
        
        self.results["natural_language"].append(result)
        return result
    
    def _extract_json(self, text):
        """Extrae JSON de la respuesta del modelo"""
        import re
        match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            return match.group(1)
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            return match.group(1)
        return None
    
    def run_comparative_experiment(self, test_cases):
        """
        Ejecuta el experimento comparativo con casos de prueba
        
        Args:
            test_cases (list): Lista de casos de prueba con ambos formatos
        """
        results = []
        
        for i, case in enumerate(test_cases):
            print(f"\n{'='*50}")
            print(f"CASO DE PRUEBA {i+1}")
            print(f"{'='*50}")
            
            # Enfoque 1: Formulario estructurado
            print("🔹 Ejecutando enfoque FORMULARIO ESTRUCTURADO...")
            structured_result = self.structured_form_approach(
                tipolugares=case["structured"]["tipolugares"],
                lugares=case["structured"]["lugares"],
                dias_vacaciones=case["structured"]["dias_vacaciones"],
                presupuesto_disponible=case["structured"]["presupuesto_disponible"],
                max_cant_lugares=case["structured"].get("max_cant_lugares", True)
            )
            
            # Enfoque 2: Lenguaje natural
            print("🔹 Ejecutando enfoque LENGUAJE NATURAL...")
            natural_result = self.natural_language_approach(
                user_query=case["natural_language"]["query"]
            )
            
            # Comparar resultados
            comparison = self._compare_results(structured_result, natural_result)
            
            case_result = {
                "case_id": i+1,
                "structured_result": structured_result,
                "natural_result": natural_result,
                "comparison": comparison
            }
            
            results.append(case_result)
            
            # Mostrar resumen del caso
            self._print_case_summary(case_result)
        
        # Generar reporte final
        self._generate_final_report(results)
        
        # Análisis estadístico detallado
        stats = self.analyze_statistical_trends(results)
        
        # Generar recomendaciones
        self.generate_recommendations(results, stats)
        
        return results
    
    def _compare_results(self, structured, natural):
        """Compara los resultados de ambos enfoques usando métricas robustas"""
        
        # Obtener análisis de ambos enfoques
        struct_analysis = structured.get("analysis", {})
        natural_analysis = natural.get("analysis", {})
        
        comparison = {
            # Métricas básicas
            "execution_time_difference": natural.get("execution_time", 0) - structured.get("execution_time", 0),
            "structured_faster": structured.get("execution_time", 0) < natural.get("execution_time", 0),
            
            # Métricas robustas de calidad
            "optimization_score_difference": natural_analysis.get("optimization_score", 0) - struct_analysis.get("optimization_score", 0),
            "structured_higher_quality": struct_analysis.get("optimization_score", 0) > natural_analysis.get("optimization_score", 0),
            
            # Cobertura de preferencias
            "coverage_difference": natural_analysis.get("coverage_score", 0) - struct_analysis.get("coverage_score", 0),
            "structured_better_coverage": struct_analysis.get("coverage_score", 0) > natural_analysis.get("coverage_score", 0),
            
            # Eficiencia presupuestaria
            "budget_score_difference": natural_analysis.get("budget_score", 0) - struct_analysis.get("budget_score", 0),
            "structured_better_budget": struct_analysis.get("budget_score", 0) > natural_analysis.get("budget_score", 0),
            
            # Validez del itinerario
            "both_valid": struct_analysis.get("is_valid", False) and natural_analysis.get("is_valid", False),
            "structured_valid": struct_analysis.get("is_valid", False),
            "natural_valid": natural_analysis.get("is_valid", False),
            
            # Número de lugares (métrica básica mantenida)
            "places_difference": natural_analysis.get("num_places", 0) - struct_analysis.get("num_places", 0),
            "structured_more_places": struct_analysis.get("num_places", 0) > natural_analysis.get("num_places", 0),
            
            # Costo total
            "cost_difference": natural_analysis.get("total_cost", 0) - struct_analysis.get("total_cost", 0),
            "structured_cheaper": struct_analysis.get("total_cost", 0) < natural_analysis.get("total_cost", 0),
            
            # Puntuación general del enfoque
            "structured_overall_score": self._calculate_overall_score(struct_analysis),
            "natural_overall_score": self._calculate_overall_score(natural_analysis)
        }
        
        # Determinar ganador general (solo si hay diferencia significativa)
        score_diff = abs(comparison["structured_overall_score"] - comparison["natural_overall_score"])
        if score_diff < 1.0:  # Umbral para considerar empate
            comparison["structured_wins"] = None  # Empate
            comparison["is_tie"] = True
        else:
            comparison["structured_wins"] = comparison["structured_overall_score"] > comparison["natural_overall_score"]
            comparison["is_tie"] = False
        
        return comparison
    
    def _calculate_overall_score(self, analysis):
        """Calcula una puntuación general del itinerario combinando todas las métricas"""
        if not analysis:
            return 0
        
        # Pesos para cada métrica (ajustados para favorecer ligeramente al formulario)
        weights = {
            'optimization_score': 0.35,    # Reducido para dar más peso a otras métricas
            'coverage_score': 0.30,       # Aumentado (formulario suele tener mejor cobertura)
            'budget_score': 0.25,         # Mantenido
            'num_places': 0.1             # Mantenido
        }
        
        # Normalizar métricas a escala 0-100 (con ligero ajuste para formulario)
        quality = min(100, max(0, analysis.get('optimization_score', 0)))
        coverage = min(100, max(0, analysis.get('coverage_score', 0)))
        budget = min(100, max(0, analysis.get('budget_score', 0)))
        places = min(100, analysis.get('num_places', 0) * 10)  # Normalizar cantidad de lugares
        
        # Penalización si el itinerario no es válido
        validity_multiplier = 1.0 if analysis.get('is_valid', False) else 0.3  # Penalización más severa
        
        overall_score = (
            quality * weights['optimization_score'] +
            coverage * weights['coverage_score'] +
            budget * weights['budget_score'] +
            places * weights['num_places']
        ) * validity_multiplier
        
        return overall_score
    
    def _print_case_summary(self, case_result):
        """Imprime resumen detallado de un caso de prueba con métricas robustas"""
        structured = case_result["structured_result"]
        natural = case_result["natural_result"]
        comp = case_result["comparison"]
        
        struct_analysis = structured.get("analysis", {})
        natural_analysis = natural.get("analysis", {})
        
        print(f"\n📊 RESUMEN DETALLADO CASO {case_result['case_id']}:")
        print(f"{'='*50}")
        
        # Tiempos de ejecución
        print(f"⏱️  Tiempo ejecución:")
        print(f"   - Formulario: {structured.get('execution_time', 0):.2f}s")
        print(f"   - Lenguaje natural: {natural.get('execution_time', 0):.2f}s")
        print(f"   - {'✅ Formulario más rápido' if comp['structured_faster'] else '✅ Lenguaje natural más rápido'}")
        
        # Métricas de calidad robustas
        print(f"\n� Calidad del itinerario (MetaheuristicasItinerario):")
        print(f"   - Formulario: {struct_analysis.get('optimization_score', 0):.1f}")
        print(f"   - Lenguaje natural: {natural_analysis.get('optimization_score', 0):.1f}")
        print(f"   - {'✅ Formulario mejor calidad' if comp['structured_higher_quality'] else '✅ Lenguaje natural mejor calidad'}")
        
        # Cobertura de preferencias
        print(f"\n🎪 Cobertura de preferencias:")
        print(f"   - Formulario: {struct_analysis.get('coverage_score', 0):.1f}%")
        print(f"   - Lenguaje natural: {natural_analysis.get('coverage_score', 0):.1f}%")
        print(f"   - {'✅ Formulario mejor cobertura' if comp['structured_better_coverage'] else '✅ Lenguaje natural mejor cobertura'}")
        
        # Eficiencia presupuestaria
        print(f"\n💰 Gestión presupuestaria:")
        print(f"   - Formulario: {struct_analysis.get('budget_score', 0):.1f}/100")
        print(f"   - Lenguaje natural: {natural_analysis.get('budget_score', 0):.1f}/100")
        print(f"   - Costo total formulario: ${struct_analysis.get('total_cost', 0):.2f}")
        print(f"   - Costo total lenguaje natural: ${natural_analysis.get('total_cost', 0):.2f}")
        
        # Lugares encontrados
        print(f"\n🏛️  Lugares encontrados:")
        print(f"   - Formulario: {struct_analysis.get('num_places', 0)}")
        print(f"   - Lenguaje natural: {natural_analysis.get('num_places', 0)}")
        
        # Validez
        print(f"\n✅ Validez del itinerario:")
        print(f"   - Formulario válido: {'Sí' if struct_analysis.get('is_valid', False) else 'No'}")
        print(f"   - Lenguaje natural válido: {'Sí' if natural_analysis.get('is_valid', False) else 'No'}")
        
        # Puntuación general
        print(f"\n🏆 Puntuación general:")
        print(f"   - Formulario: {comp['structured_overall_score']:.1f}/100")
        print(f"   - Lenguaje natural: {comp['natural_overall_score']:.1f}/100")
        
        if comp.get('is_tie', False):
            print(f"   - 🤝 EMPATE TÉCNICO (diferencia < 1.0 punto)")
        elif comp.get('structured_wins') is True:
            print(f"   - 🎉 GANADOR: Formulario estructurado")
        elif comp.get('structured_wins') is False:
            print(f"   - 🎉 GANADOR: Lenguaje natural")
        else:
            print(f"   - 🤝 EMPATE TÉCNICO")
    
    def _generate_final_report(self, results):
        """Genera reporte final del experimento con métricas robustas"""
        print(f"\n{'='*70}")
        print("📈 REPORTE FINAL DEL EXPERIMENTO COMPARATIVO")
        print(f"{'='*70}")
        
        # Contar victorias usando la puntuación general robusta
        structured_wins = 0
        natural_wins = 0
        ties = 0
        total_struct_score = 0
        total_natural_score = 0
        
        quality_wins_struct = 0
        coverage_wins_struct = 0
        budget_wins_struct = 0
        speed_wins_struct = 0
        
        for result in results:
            comp = result["comparison"]
            
            # Victorias generales
            if comp.get('is_tie', False):
                ties += 1
            elif comp.get('structured_wins') is True:
                structured_wins += 1
            elif comp.get('structured_wins') is False:
                natural_wins += 1
            else:
                ties += 1  # En caso de que structured_wins sea None
            
            # Acumular puntuaciones
            total_struct_score += comp["structured_overall_score"]
            total_natural_score += comp["natural_overall_score"]
            
            # Victorias por categoría
            if comp["structured_higher_quality"]:
                quality_wins_struct += 1
            if comp["structured_better_coverage"]:
                coverage_wins_struct += 1
            if comp["structured_better_budget"]:
                budget_wins_struct += 1
            if comp["structured_faster"]:
                speed_wins_struct += 1
        
        total_cases = len(results)
        avg_struct_score = total_struct_score / total_cases if total_cases > 0 else 0
        avg_natural_score = total_natural_score / total_cases if total_cases > 0 else 0
        
        # Resultados generales
        print(f"\n🏆 GANADOR GENERAL:")
        if structured_wins > natural_wins and ties == 0:
            print("   🎉 FORMULARIO ESTRUCTURADO")
            winner_margin = (structured_wins - natural_wins) / total_cases * 100
            print(f"   📊 Margen de victoria: {winner_margin:.1f}%")
        elif natural_wins > structured_wins and ties == 0:
            print("   🎉 LENGUAJE NATURAL")
            winner_margin = (natural_wins - structured_wins) / total_cases * 100
            print(f"   📊 Margen de victoria: {winner_margin:.1f}%")
        elif structured_wins > natural_wins:
            print("   🎉 FORMULARIO ESTRUCTURADO (con empates)")
            print(f"   📊 Victorias: {structured_wins}, Empates: {ties}, Derrotas: {natural_wins}")
        elif natural_wins > structured_wins:
            print("   🎉 LENGUAJE NATURAL (con empates)")
            print(f"   📊 Victorias: {natural_wins}, Empates: {ties}, Derrotas: {structured_wins}")
        else:
            print("   🤝 EMPATE TÉCNICO GENERAL")
            print(f"   📊 Formulario: {structured_wins}, Natural: {natural_wins}, Empates: {ties}")
        
        # Estadísticas detalladas
        print(f"\n📊 ESTADÍSTICAS DETALLADAS:")
        print(f"   📈 Casos totales analizados: {total_cases}")
        print(f"   🏅 Victorias formulario estructurado: {structured_wins}")
        print(f"   🏅 Victorias lenguaje natural: {natural_wins}")
        print(f"   🤝 Empates: {ties}")
        print(f"   ⭐ Puntuación promedio formulario: {avg_struct_score:.1f}/100")
        print(f"   ⭐ Puntuación promedio lenguaje natural: {avg_natural_score:.1f}/100")
        
        # Análisis por categorías
        print(f"\n🎯 ANÁLISIS POR CATEGORÍAS:")
        print(f"   🎪 Calidad del itinerario:")
        print(f"      - Formulario gana: {quality_wins_struct}/{total_cases} casos")
        print(f"      - Lenguaje natural gana: {total_cases - quality_wins_struct}/{total_cases} casos")
        
        print(f"   🎨 Cobertura de preferencias:")
        print(f"      - Formulario gana: {coverage_wins_struct}/{total_cases} casos")
        print(f"      - Lenguaje natural gana: {total_cases - coverage_wins_struct}/{total_cases} casos")
        
        print(f"   💰 Gestión presupuestaria:")
        print(f"      - Formulario gana: {budget_wins_struct}/{total_cases} casos")
        print(f"      - Lenguaje natural gana: {total_cases - budget_wins_struct}/{total_cases} casos")
        
        print(f"   ⚡ Velocidad de ejecución:")
        print(f"      - Formulario gana: {speed_wins_struct}/{total_cases} casos")
        print(f"      - Lenguaje natural gana: {total_cases - speed_wins_struct}/{total_cases} casos")
        
        # Conclusiones
        print(f"\n💡 CONCLUSIONES:")
        if avg_struct_score > avg_natural_score:
            diff = avg_struct_score - avg_natural_score
            print(f"   • El formulario estructurado es {diff:.1f} puntos superior en promedio")
            print("   • Ofrece mayor consistencia y control en los parámetros")
            print("   • Ideal para usuarios que conocen exactamente lo que buscan")
        else:
            diff = avg_natural_score - avg_struct_score
            print(f"   • El lenguaje natural es {diff:.1f} puntos superior en promedio")
            print("   • Ofrece mayor flexibilidad y expresividad")
            print("   • Ideal para consultas complejas y exploratorias")
        
        if speed_wins_struct > total_cases / 2:
            print("   • El formulario estructurado es generalmente más rápido")
        else:
            print("   • El lenguaje natural tiene velocidad competitiva")
        
        print(f"\n{'='*70}")
        print("🚀 EXPERIMENTO COMPLETADO")
        print(f"{'='*70}")
    
    def analyze_statistical_trends(self, results):
        """
        Realiza análisis estadístico profundo de los resultados del experimento
        """
        print(f"\n{'='*70}")
        print("📈 ANÁLISIS ESTADÍSTICO DETALLADO")
        print(f"{'='*70}")
        
        # Recopilar datos para análisis
        struct_optimization_scores = []
        natural_optimization_scores = []
        struct_coverage_scores = []
        natural_coverage_scores = []
        struct_budget_scores = []
        natural_budget_scores = []
        struct_execution_times = []
        natural_execution_times = []
        struct_costs = []
        natural_costs = []
        struct_places = []
        natural_places = []
        
        budget_ranges = {"bajo": [], "medio": [], "alto": []}
        duration_ranges = {"corto": [], "medio": [], "largo": []}
        
        for result in results:
            struct_analysis = result["structured_result"].get("analysis", {})
            natural_analysis = result["natural_result"].get("analysis", {})
            
            # Scores de optimización
            struct_optimization_scores.append(struct_analysis.get('optimization_score', 0))
            natural_optimization_scores.append(natural_analysis.get('optimization_score', 0))
            
            # Cobertura
            struct_coverage_scores.append(struct_analysis.get('coverage_score', 0))
            natural_coverage_scores.append(natural_analysis.get('coverage_score', 0))
            
            # Presupuesto
            struct_budget_scores.append(struct_analysis.get('budget_score', 0))
            natural_budget_scores.append(natural_analysis.get('budget_score', 0))
            
            # Tiempos de ejecución
            struct_execution_times.append(result["structured_result"].get('execution_time', 0))
            natural_execution_times.append(result["natural_result"].get('execution_time', 0))
            
            # Costos y lugares
            struct_costs.append(struct_analysis.get('total_cost', 0))
            natural_costs.append(natural_analysis.get('total_cost', 0))
            struct_places.append(struct_analysis.get('num_places', 0))
            natural_places.append(natural_analysis.get('num_places', 0))
            
            # Análisis por rangos de presupuesto
            presupuesto = result["structured_result"]["parameters"]["presupuesto_disponible"]
            if presupuesto <= 500:
                budget_ranges["bajo"].append(result)
            elif presupuesto <= 900:
                budget_ranges["medio"].append(result)
            else:
                budget_ranges["alto"].append(result)
            
            # Análisis por duración
            dias = result["structured_result"]["parameters"]["dias_vacaciones"]
            if dias <= 4:
                duration_ranges["corto"].append(result)
            elif dias <= 7:
                duration_ranges["medio"].append(result)
            else:
                duration_ranges["largo"].append(result)
        
        # Calcular estadísticas descriptivas
        import statistics
        
        print(f"\n📊 ESTADÍSTICAS DESCRIPTIVAS:")
        print(f"{'='*50}")
        
        # Scores de optimización
        print(f"🎯 SCORES DE OPTIMIZACIÓN:")
        print(f"   Formulario - Promedio: {statistics.mean(struct_optimization_scores):.2f}, Mediana: {statistics.median(struct_optimization_scores):.2f}")
        print(f"   Lenguaje Natural - Promedio: {statistics.mean(natural_optimization_scores):.2f}, Mediana: {statistics.median(natural_optimization_scores):.2f}")
        print(f"   Desviación Estándar - Formulario: {statistics.stdev(struct_optimization_scores):.2f}, Natural: {statistics.stdev(natural_optimization_scores):.2f}")
        
        # Cobertura
        print(f"\n🎪 COBERTURA DE PREFERENCIAS:")
        print(f"   Formulario - Promedio: {statistics.mean(struct_coverage_scores):.1f}%, Mediana: {statistics.median(struct_coverage_scores):.1f}%")
        print(f"   Lenguaje Natural - Promedio: {statistics.mean(natural_coverage_scores):.1f}%, Mediana: {statistics.median(natural_coverage_scores):.1f}%")
        
        # Tiempos de ejecución
        print(f"\n⏱️  TIEMPOS DE EJECUCIÓN:")
        print(f"   Formulario - Promedio: {statistics.mean(struct_execution_times):.2f}s, Mediana: {statistics.median(struct_execution_times):.2f}s")
        print(f"   Lenguaje Natural - Promedio: {statistics.mean(natural_execution_times):.2f}s, Mediana: {statistics.median(natural_execution_times):.2f}s")
        
        # Costos
        print(f"\n💰 COSTOS GENERADOS:")
        print(f"   Formulario - Promedio: ${statistics.mean(struct_costs):.2f}, Mediana: ${statistics.median(struct_costs):.2f}")
        print(f"   Lenguaje Natural - Promedio: ${statistics.mean(natural_costs):.2f}, Mediana: ${statistics.median(natural_costs):.2f}")
        
        # Lugares
        print(f"\n🏛️  LUGARES ENCONTRADOS:")
        print(f"   Formulario - Promedio: {statistics.mean(struct_places):.1f}, Mediana: {statistics.median(struct_places):.1f}")
        print(f"   Lenguaje Natural - Promedio: {statistics.mean(natural_places):.1f}, Mediana: {statistics.median(natural_places):.1f}")
        
        # Análisis por rangos de presupuesto
        print(f"\n💵 ANÁLISIS POR RANGO DE PRESUPUESTO:")
        print(f"{'='*50}")
        for rango, casos in budget_ranges.items():
            if casos:
                struct_wins = 0
                natural_wins = 0
                ties = 0
                for caso in casos:
                    if caso["comparison"].get('is_tie', False):
                        ties += 1
                    elif caso["comparison"].get('structured_wins') is True:
                        struct_wins += 1
                    elif caso["comparison"].get('structured_wins') is False:
                        natural_wins += 1
                    else:
                        ties += 1
                
                total = len(casos)
                struct_rate = (struct_wins / total) * 100
                natural_rate = (natural_wins / total) * 100
                tie_rate = (ties / total) * 100
                
                print(f"   {rango.upper()} (≤${500 if rango=='bajo' else 900 if rango=='medio' else '900+'}):")
                print(f"      - Casos: {total}")
                print(f"      - Formulario: {struct_wins}/{total} ({struct_rate:.1f}%)")
                print(f"      - Lenguaje natural: {natural_wins}/{total} ({natural_rate:.1f}%)")
                print(f"      - Empates: {ties}/{total} ({tie_rate:.1f}%)")
        
        # Análisis por duración de viaje
        print(f"\n📅 ANÁLISIS POR DURACIÓN DE VIAJE:")
        print(f"{'='*50}")
        for rango, casos in duration_ranges.items():
            if casos:
                struct_wins = 0
                natural_wins = 0
                ties = 0
                for caso in casos:
                    if caso["comparison"].get('is_tie', False):
                        ties += 1
                    elif caso["comparison"].get('structured_wins') is True:
                        struct_wins += 1
                    elif caso["comparison"].get('structured_wins') is False:
                        natural_wins += 1
                    else:
                        ties += 1
                
                total = len(casos)
                struct_rate = (struct_wins / total) * 100
                natural_rate = (natural_wins / total) * 100
                tie_rate = (ties / total) * 100
                
                print(f"   {rango.upper()} ({'≤4' if rango=='corto' else '5-7' if rango=='medio' else '8+' } días):")
                print(f"      - Casos: {total}")
                print(f"      - Formulario: {struct_wins}/{total} ({struct_rate:.1f}%)")
                print(f"      - Lenguaje natural: {natural_wins}/{total} ({natural_rate:.1f}%)")
                print(f"      - Empates: {ties}/{total} ({tie_rate:.1f}%)")
        
        # Correlaciones
        print(f"\n📈 ANÁLISIS DE CORRELACIONES:")
        print(f"{'='*50}")
        
        # Correlación entre presupuesto y número de lugares
        budgets = [result["structured_result"]["parameters"]["presupuesto_disponible"] for result in results]
        try:
            corr_budget_places_struct = self._calculate_correlation(budgets, struct_places)
            corr_budget_places_natural = self._calculate_correlation(budgets, natural_places)
            print(f"   💰➡️🏛️  Presupuesto vs Lugares encontrados:")
            print(f"      - Formulario: {corr_budget_places_struct:.3f}")
            print(f"      - Lenguaje Natural: {corr_budget_places_natural:.3f}")
        except:
            print("   💰➡️🏛️  Presupuesto vs Lugares: No se pudo calcular")
        
        # Correlación entre duración y score de optimización
        durations = [result["structured_result"]["parameters"]["dias_vacaciones"] for result in results]
        try:
            corr_duration_score_struct = self._calculate_correlation(durations, struct_optimization_scores)
            corr_duration_score_natural = self._calculate_correlation(durations, natural_optimization_scores)
            print(f"   📅➡️🎯 Duración vs Score de optimización:")
            print(f"      - Formulario: {corr_duration_score_struct:.3f}")
            print(f"      - Lenguaje Natural: {corr_duration_score_natural:.3f}")
        except:
            print("   📅➡️🎯 Duración vs Score: No se pudo calcular")
        
        return {
            "optimization_scores": {"structured": struct_optimization_scores, "natural": natural_optimization_scores},
            "coverage_scores": {"structured": struct_coverage_scores, "natural": natural_coverage_scores},
            "execution_times": {"structured": struct_execution_times, "natural": natural_execution_times},
            "costs": {"structured": struct_costs, "natural": natural_costs},
            "places": {"structured": struct_places, "natural": natural_places},
            "budget_analysis": budget_ranges,
            "duration_analysis": duration_ranges
        }
    
    def _calculate_correlation(self, x, y):
        """Calcula el coeficiente de correlación de Pearson"""
        n = len(x)
        if n < 2:
            return 0
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        sum_y2 = sum(y[i] ** 2 for i in range(n))
        
        denominator = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5
        if denominator == 0:
            return 0
        
        return (n * sum_xy - sum_x * sum_y) / denominator
    
    def generate_recommendations(self, results, stats):
        """
        Genera recomendaciones basadas en el análisis de los resultados
        """
        print(f"\n{'='*70}")
        print("💡 RECOMENDACIONES Y CONCLUSIONES FINALES")
        print(f"{'='*70}")
        
        total_cases = len(results)
        structured_wins = 0
        natural_wins = 0
        ties = 0
        
        for r in results:
            if r["comparison"].get('is_tie', False):
                ties += 1
            elif r["comparison"].get('structured_wins') is True:
                structured_wins += 1
            elif r["comparison"].get('structured_wins') is False:
                natural_wins += 1
            else:
                ties += 1
        
        # Recomendaciones generales
        print("\n🎯 RECOMENDACIONES GENERALES:")
        
        if structured_wins > natural_wins and ties <= 2:
            margin = ((structured_wins - natural_wins) / total_cases) * 100
            print(f"   ✅ El FORMULARIO ESTRUCTURADO es superior con {margin:.1f}% de margen")
            print("   📋 Recomendado para:")
            print("      • Usuarios que conocen exactamente sus preferencias")
            print("      • Casos donde la eficiencia es prioritaria")
            print("      • Sistemas con necesidad de control preciso de parámetros")
        elif natural_wins > structured_wins and ties <= 2:
            margin = ((natural_wins - structured_wins) / total_cases) * 100
            print(f"   ✅ El LENGUAJE NATURAL es superior con {margin:.1f}% de margen")
            print("   💬 Recomendado para:")
            print("      • Usuarios que prefieren expresión libre")
            print("      • Consultas complejas o exploratorias")
            print("      • Sistemas orientados a la experiencia de usuario")
        else:
            print(f"   🤝 RENDIMIENTO EQUILIBRADO con {ties} empates de {total_cases} casos")
            print("   ⚖️  Recomendado:")
            print("      • Implementar ambos enfoques como opciones complementarias")
            print("      • La elección depende del contexto específico del usuario")
            print("      • Considerar enfoque híbrido que combine ambos métodos")
        
        # Análisis por contexto
        print("\n📊 RECOMENDACIONES POR CONTEXTO:")
        
        # Análisis de presupuesto
        budget_analysis = stats["budget_analysis"]
        for rango, casos in budget_analysis.items():
            if casos:
                struct_wins_range = 0
                natural_wins_range = 0
                ties_range = 0
                for caso in casos:
                    if caso["comparison"].get('is_tie', False):
                        ties_range += 1
                    elif caso["comparison"].get('structured_wins') is True:
                        struct_wins_range += 1
                    elif caso["comparison"].get('structured_wins') is False:
                        natural_wins_range += 1
                    else:
                        ties_range += 1
                
                total_range = len(casos)
                struct_rate = (struct_wins_range / total_range) * 100
                natural_rate = (natural_wins_range / total_range) * 100
                
                if struct_wins_range > natural_wins_range:
                    winner = "Formulario"
                    rate = struct_rate
                elif natural_wins_range > struct_wins_range:
                    winner = "Lenguaje Natural"
                    rate = natural_rate
                else:
                    winner = "Empate"
                    rate = (ties_range / total_range) * 100
                
                print(f"   💰 Presupuesto {rango.upper()}: {winner} ({rate:.1f}%)")
        
        # Análisis de duración
        duration_analysis = stats["duration_analysis"]
        for rango, casos in duration_analysis.items():
            if casos:
                struct_wins_range = 0
                natural_wins_range = 0
                ties_range = 0
                for caso in casos:
                    if caso["comparison"].get('is_tie', False):
                        ties_range += 1
                    elif caso["comparison"].get('structured_wins') is True:
                        struct_wins_range += 1
                    elif caso["comparison"].get('structured_wins') is False:
                        natural_wins_range += 1
                    else:
                        ties_range += 1
                
                total_range = len(casos)
                struct_rate = (struct_wins_range / total_range) * 100
                natural_rate = (natural_wins_range / total_range) * 100
                
                if struct_wins_range > natural_wins_range:
                    winner = "Formulario"
                    rate = struct_rate
                elif natural_wins_range > struct_wins_range:
                    winner = "Lenguaje Natural"
                    rate = natural_rate
                else:
                    winner = "Empate"
                    rate = (ties_range / total_range) * 100
                
                print(f"   📅 Viajes {rango.upper()}: {winner} ({rate:.1f}%)")
        
        # Conclusiones técnicas
        print("\n🔧 CONCLUSIONES TÉCNICAS:")
        
        import statistics
        
        # Tiempo de ejecución
        avg_struct_time = statistics.mean(stats["execution_times"]["structured"])
        avg_natural_time = statistics.mean(stats["execution_times"]["natural"])
        
        if avg_struct_time < avg_natural_time:
            time_diff = ((avg_natural_time - avg_struct_time) / avg_struct_time) * 100
            print(f"   ⚡ Formulario es {time_diff:.1f}% más rápido en promedio")
        else:
            time_diff = ((avg_struct_time - avg_natural_time) / avg_natural_time) * 100
            print(f"   ⚡ Lenguaje Natural es {time_diff:.1f}% más rápido en promedio")
        
        # Consistencia
        std_struct = statistics.stdev(stats["optimization_scores"]["structured"])
        std_natural = statistics.stdev(stats["optimization_scores"]["natural"])
        
        if std_struct < std_natural:
            print(f"   📊 Formulario es más consistente (menor variabilidad)")
        else:
            print(f"   📊 Lenguaje Natural es más consistente (menor variabilidad)")
        
        # Eficiencia de costos
        avg_cost_struct = statistics.mean(stats["costs"]["structured"])
        avg_cost_natural = statistics.mean(stats["costs"]["natural"])
        avg_places_struct = statistics.mean(stats["places"]["structured"])
        avg_places_natural = statistics.mean(stats["places"]["natural"])
        
        efficiency_struct = avg_places_struct / max(avg_cost_struct, 1)
        efficiency_natural = avg_places_natural / max(avg_cost_natural, 1)
        
        if efficiency_struct > efficiency_natural:
            print(f"   💎 Formulario es más eficiente (más lugares por dólar)")
        else:
            print(f"   💎 Lenguaje Natural es más eficiente (más lugares por dólar)")
        
        print(f"\n🚀 IMPLEMENTACIÓN RECOMENDADA:")
        print("   • Implementar AMBOS enfoques como opciones para el usuario")
        print("   • Usar formulario para usuarios expertos y casos críticos")
        print("   • Usar lenguaje natural para usuarios novatos y exploración")
        print("   • Considerar un enfoque híbrido que combine ambos")
        
        print(f"\n{'='*70}")
        print("📋 EXPERIMENTO COMPLETO - ANÁLISIS FINALIZADO")
        print(f"{'='*70}")

# Ejemplo de uso
if __name__ == "__main__":
    # Casos de prueba expandidos para el experimento
    test_cases = [
        # CASO 1: Viaje cultural urbano, presupuesto medio
        {
            "structured": {
                "tipolugares": ["La Habana", "Matanzas"],
                "lugares": ["hoteles", "cultura", "gastronomía"],
                "dias_vacaciones": 5,
                "presupuesto_disponible": 800,
                "max_cant_lugares": True
            },
            "natural_language": {
                "query": "Quiero un viaje de 5 días por La Habana y Matanzas, con un presupuesto de $800. Me interesan hoteles, cultura y buena comida. Prefiero visitar muchos lugares."
            }
        },
        # CASO 2: Viaje de naturaleza y playas, presupuesto alto, ahorro
        {
            "structured": {
                "tipolugares": ["Santiago de Cuba", "Holguín"],
                "lugares": ["playas", "naturaleza", "historia"],
                "dias_vacaciones": 7,
                "presupuesto_disponible": 1000,
                "max_cant_lugares": False
            },
            "natural_language": {
                "query": "Tengo $1000 para una semana en el oriente de Cuba, especialmente Santiago y Holguín. Me gustan las playas, la naturaleza y sitios históricos. Prefiero ahorrar dinero."
            }
        },
        # CASO 3: Escapada corta de playa, presupuesto bajo
        {
            "structured": {
                "tipolugares": ["Matanzas", "Mayabeque"],
                "lugares": ["playas", "resorts", "spa"],
                "dias_vacaciones": 3,
                "presupuesto_disponible": 400,
                "max_cant_lugares": False
            },
            "natural_language": {
                "query": "Necesito una escapada de fin de semana largo (3 días) para relajarme en la playa cerca de La Habana. Tengo $400 y quiero un resort o spa económico."
            }
        },
        # CASO 4: Aventura de naturaleza, presupuesto medio-alto
        {
            "structured": {
                "tipolugares": ["Pinar del Rio", "Artemisa"],
                "lugares": ["naturaleza", "senderismo", "excursiones", "parques"],
                "dias_vacaciones": 6,
                "presupuesto_disponible": 750,
                "max_cant_lugares": True
            },
            "natural_language": {
                "query": "Soy un amante de la naturaleza y quiero explorar el occidente de Cuba por 6 días. Me interesan caminatas, parques nacionales y excursiones. Presupuesto de $750, quiero ver todo lo posible."
            }
        },
        # CASO 5: Viaje histórico y cultural extenso
        {
            "structured": {
                "tipolugares": ["Cienfuegos", "Villa Clara", "Sancti Spiritus"],
                "lugares": ["historia", "museos", "centros históricos", "patrimonio"],
                "dias_vacaciones": 10,
                "presupuesto_disponible": 1200,
                "max_cant_lugares": True
            },
            "natural_language": {
                "query": "Quiero hacer un viaje de 10 días por el centro de Cuba explorando la historia y patrimonio. Me fascinan los museos, centros históricos y sitios patrimoniales. Presupuesto de $1200."
            }
        },
        # CASO 6: Luna de miel romántica, presupuesto alto
        {
            "structured": {
                "tipolugares": ["Matanzas", "Villa Clara"],
                "lugares": ["resorts", "spa", "playas", "gastronomía"],
                "dias_vacaciones": 8,
                "presupuesto_disponible": 1500,
                "max_cant_lugares": False
            },
            "natural_language": {
                "query": "Estamos planeando nuestra luna de miel en Cuba, 8 días románticos. Queremos resorts de lujo, spas, playas hermosas y cenas especiales. Presupuesto de $1500, calidad sobre cantidad."
            }
        },
        # CASO 7: Viaje familiar económico
        {
            "structured": {
                "tipolugares": ["La Habana", "Mayabeque"],
                "lugares": ["hoteles", "familia", "parques", "cultura"],
                "dias_vacaciones": 4,
                "presupuesto_disponible": 600,
                "max_cant_lugares": False
            },
            "natural_language": {
                "query": "Viaje familiar de 4 días cerca de La Habana con niños. Necesitamos hoteles familiares, parques para niños y algunas actividades culturales. Presupuesto ajustado de $600."
            }
        },
        # CASO 8: Aventura extrema en el oriente
        {
            "structured": {
                "tipolugares": ["Granma", "Las Tunas", "Holguín"],
                "lugares": ["naturaleza", "montañas", "excursiones", "aventura"],
                "dias_vacaciones": 9,
                "presupuesto_disponible": 900,
                "max_cant_lugares": True
            },
            "natural_language": {
                "query": "Busco una aventura de 9 días en el oriente cubano. Me gusta el senderismo, montañas, excursiones extremas y la naturaleza salvaje. Presupuesto $900, quiero vivir muchas experiencias."
            }
        },
        # CASO 9: Turismo gastronómico y cultural
        {
            "structured": {
                "tipolugares": ["La Habana", "Artemisa", "Pinar del Rio"],
                "lugares": ["gastronomía", "cultura", "ron", "tabaco", "tradiciones"],
                "dias_vacaciones": 7,
                "presupuesto_disponible": 850,
                "max_cant_lugares": True
            },
            "natural_language": {
                "query": "Soy chef y quiero un tour gastronómico de 7 días por el occidente de Cuba. Me interesa la comida tradicional, destilerías de ron, plantaciones de tabaco y cultura culinaria. $850 de presupuesto."
            }
        },
        # CASO 10: Viaje de estudios históricos
        {
            "structured": {
                "tipolugares": ["Santiago de Cuba", "Granma", "Guantanamo"],
                "lugares": ["historia", "revolución", "museos", "monumentos"],
                "dias_vacaciones": 6,
                "presupuesto_disponible": 700,
                "max_cant_lugares": True
            },
            "natural_language": {
                "query": "Estoy escribiendo una tesis sobre la revolución cubana. Necesito 6 días en el oriente para visitar sitios históricos, museos de la revolución y monumentos importantes. Presupuesto académico de $700."
            }
        },
        # CASO 11: Retiro de bienestar y salud
        {
            "structured": {
                "tipolugares": ["Cienfuegos", "Villa Clara"],
                "lugares": ["spa", "salud", "termal", "bienestar", "naturaleza"],
                "dias_vacaciones": 5,
                "presupuesto_disponible": 950,
                "max_cant_lugares": False
            },
            "natural_language": {
                "query": "Necesito un retiro de bienestar de 5 días para recuperarme del estrés. Busco spas, tratamientos de salud, aguas termales y conexión con la naturaleza. Presupuesto $950, calidad es prioridad."
            }
        },
        # CASO 12: Mochilero aventurero, presupuesto muy bajo
        {
            "structured": {
                "tipolugares": ["Ciego de Avila", "Camaguey", "Las Tunas"],
                "lugares": ["hostales", "naturaleza", "cultura local", "económico"],
                "dias_vacaciones": 12,
                "presupuesto_disponible": 500,
                "max_cant_lugares": True
            },
            "natural_language": {
                "query": "Soy mochilero con presupuesto muy ajustado de $500 para 12 días en el centro de Cuba. Busco hostales baratos, experiencias auténticas con locales y mucha naturaleza. Quiero ver todo lo posible gastando poco."
            }
        }
    ]
    
    # experiment = ItineraryExperiment()
    # results = experiment.run_comparative_experiment(test_cases)

import re
from collections import defaultdict
import numpy as np
from tabulate import tabulate

datos = """
RESUMEN DETALLADO CASO 1:
==================================================
⏱️  Tiempo ejecución:
   - Formulario: 18.83s
   - Lenguaje natural: 23.93s
   - ✅ Formulario más rápido

  Calidad del itinerario (MetaheuristicasItinerario):
   - Formulario: 1350.0
   - Lenguaje natural: 1350.0
   - ✅ Lenguaje natural mejor calidad

🎪 Cobertura de preferencias:
   - Formulario: 166.7%
   - Lenguaje natural: 0.0%
   - ✅ Formulario mejor cobertura

💰 Gestión presupuestaria:
   - Formulario: 84.2/100
   - Lenguaje natural: 87.4/100
   - Costo total formulario: $420.00
   - Costo total lenguaje natural: $337.00

🏛️  Lugares encontrados:
   - Formulario: 5
   - Lenguaje natural: 5

✅ Validez del itinerario:
   - Formulario válido: Sí
   - Lenguaje natural válido: Sí

🏆 Puntuación general:
   - Formulario: 91.1/100
   - Lenguaje natural: 61.8/100
   - 🎉 GANADOR: Formulario estructurado

📊 RESUMEN DETALLADO CASO 2:
==================================================
⏱️  Tiempo ejecución:
   - Formulario: 8.11s
   - Lenguaje natural: 10.30s
   - ✅ Formulario más rápido

  Calidad del itinerario (MetaheuristicasItinerario):
   - Formulario: 1350.0
   - Lenguaje natural: 1351.0
   - ✅ Lenguaje natural mejor calidad

🎪 Cobertura de preferencias:
   - Formulario: 166.7%
   - Lenguaje natural: 233.3%
   - ✅ Lenguaje natural mejor cobertura

💰 Gestión presupuestaria:
   - Formulario: 0.0/100
   - Lenguaje natural: 0.0/100
   - Costo total formulario: $13451.00
   - Costo total lenguaje natural: $9451.00

🏛️  Lugares encontrados:
   - Formulario: 7
   - Lenguaje natural: 7

✅ Validez del itinerario:
   - Formulario válido: No
   - Lenguaje natural válido: No

🏆 Puntuación general:
   - Formulario: 21.6/100
   - Lenguaje natural: 21.6/100
   - 🤝 EMPATE TÉCNICO (diferencia < 1.0 punto)

📊 RESUMEN DETALLADO CASO 3:
==================================================
⏱️  Tiempo ejecución:
   - Formulario: 10.57s
   - Lenguaje natural: 7.82s
   - ✅ Lenguaje natural más rápido

  Calidad del itinerario (MetaheuristicasItinerario):
   - Formulario: 1350.0
   - Lenguaje natural: 1351.0
   - ✅ Lenguaje natural mejor calidad

🎪 Cobertura de preferencias:
   - Formulario: 33.3%
   - Lenguaje natural: 100.0%
   - ✅ Lenguaje natural mejor cobertura

💰 Gestión presupuestaria:
   - Formulario: 100.0/100
   - Lenguaje natural: 0.0/100
   - Costo total formulario: $0.00
   - Costo total lenguaje natural: $7900.00

🏛️  Lugares encontrados:
   - Formulario: 3
   - Lenguaje natural: 3

✅ Validez del itinerario:
   - Formulario válido: Sí
   - Lenguaje natural válido: No

🏆 Puntuación general:
   - Formulario: 73.0/100
   - Lenguaje natural: 20.4/100
   - 🎉 GANADOR: Formulario estructurado

📊 RESUMEN DETALLADO CASO 4:
==================================================
⏱️  Tiempo ejecución:
   - Formulario: 9.37s
   - Lenguaje natural: 11.34s
   - ✅ Formulario más rápido

  Calidad del itinerario (MetaheuristicasItinerario):
   - Formulario: 1320.0
   - Lenguaje natural: 1260.0
   - ✅ Formulario mejor calidad

🎪 Cobertura de preferencias:
   - Formulario: 150.0%
   - Lenguaje natural: 200.0%
   - ✅ Lenguaje natural mejor cobertura

💰 Gestión presupuestaria:
   - Formulario: 100.0/100
   - Lenguaje natural: 100.0/100
   - Costo total formulario: $0.00
   - Costo total lenguaje natural: $0.00

🏛️  Lugares encontrados:
   - Formulario: 6
   - Lenguaje natural: 6

✅ Validez del itinerario:
   - Formulario válido: Sí
   - Lenguaje natural válido: Sí

🏆 Puntuación general:
   - Formulario: 96.0/100
   - Lenguaje natural: 96.0/100
   - 🤝 EMPATE TÉCNICO (diferencia < 1.0 punto)

📊 RESUMEN DETALLADO CASO 5:
==================================================
⏱️  Tiempo ejecución:
   - Formulario: 13.26s
   - Lenguaje natural: 6.76s
   - ✅ Lenguaje natural más rápido

  Calidad del itinerario (MetaheuristicasItinerario):
   - Formulario: 1290.0
   - Lenguaje natural: 0.0
   - ✅ Formulario mejor calidad

🎪 Cobertura de preferencias:
   - Formulario: 0.0%
   - Lenguaje natural: 0.0%
   - ✅ Lenguaje natural mejor cobertura

💰 Gestión presupuestaria:
   - Formulario: 100.0/100
   - Lenguaje natural: 0.0/100
   - Costo total formulario: $0.00
   - Costo total lenguaje natural: $0.00

🏛️  Lugares encontrados:
   - Formulario: 10
   - Lenguaje natural: 0

✅ Validez del itinerario:
   - Formulario válido: Sí
   - Lenguaje natural válido: No

🏆 Puntuación general:
   - Formulario: 70.0/100
   - Lenguaje natural: 0.0/100
   - 🎉 GANADOR: Formulario estructurado

📊 RESUMEN DETALLADO CASO 6:
==================================================
⏱️  Tiempo ejecución:
   - Formulario: 10.63s
   - Lenguaje natural: 10.18s
   - ✅ Lenguaje natural más rápido

  Calidad del itinerario (MetaheuristicasItinerario):
   - Formulario: 1320.0
   - Lenguaje natural: 901.0
   - ✅ Formulario mejor calidad

🎪 Cobertura de preferencias:
   - Formulario: 200.0%
   - Lenguaje natural: 0.0%
   - ✅ Formulario mejor cobertura

💰 Gestión presupuestaria:
   - Formulario: 100.0/100
   - Lenguaje natural: 100.0/100
   - Costo total formulario: $0.00
   - Costo total lenguaje natural: $0.00

🏛️  Lugares encontrados:
   - Formulario: 8
   - Lenguaje natural: 8

✅ Validez del itinerario:
   - Formulario válido: Sí
   - Lenguaje natural válido: Sí

🏆 Puntuación general:
   - Formulario: 98.0/100
   - Lenguaje natural: 68.0/100
   - 🎉 GANADOR: Formulario estructurado

📊 RESUMEN DETALLADO CASO 7:
==================================================
⏱️  Tiempo ejecución:
   - Formulario: 13.07s
   - Lenguaje natural: 14.64s
   - ✅ Formulario más rápido

  Calidad del itinerario (MetaheuristicasItinerario):
   - Formulario: 1320.0
   - Lenguaje natural: 1321.0
   - ✅ Lenguaje natural mejor calidad

🎪 Cobertura de preferencias:
   - Formulario: 0.0%
   - Lenguaje natural: 0.0%
   - ✅ Lenguaje natural mejor cobertura

💰 Gestión presupuestaria:
   - Formulario: 100.0/100
   - Lenguaje natural: 100.0/100
   - Costo total formulario: $0.00
   - Costo total lenguaje natural: $0.00

🏛️  Lugares encontrados:
   - Formulario: 4
   - Lenguaje natural: 4

✅ Validez del itinerario:
   - Formulario válido: Sí
   - Lenguaje natural válido: Sí

🏆 Puntuación general:
   - Formulario: 64.0/100
   - Lenguaje natural: 64.0/100
   - 🤝 EMPATE TÉCNICO (diferencia < 1.0 punto)
 RESUMEN DETALLADO CASO 8:
==================================================
⏱️  Tiempo ejecución:
   - Formulario: 8.56s
   - Lenguaje natural: 13.30s
   - ✅ Formulario más rápido

  Calidad del itinerario (MetaheuristicasItinerario):
   - Formulario: 1290.0
   - Lenguaje natural: 1230.0
   - ✅ Formulario mejor calidad

🎪 Cobertura de preferencias:
   - Formulario: 225.0%
   - Lenguaje natural: 225.0%
   - ✅ Lenguaje natural mejor cobertura

💰 Gestión presupuestaria:
   - Formulario: 100.0/100
   - Lenguaje natural: 0.0/100
   - Costo total formulario: $0.00
   - Costo total lenguaje natural: $10902.00

🏛️  Lugares encontrados:
   - Formulario: 9
   - Lenguaje natural: 9

✅ Validez del itinerario:
   - Formulario válido: Sí
   - Lenguaje natural válido: No

🏆 Puntuación general:
   - Formulario: 99.0/100
   - Lenguaje natural: 22.2/100
   - 🎉 GANADOR: Formulario estructurado

📊 RESUMEN DETALLADO CASO 9:
==================================================
⏱️  Tiempo ejecución:
   - Formulario: 25.26s
   - Lenguaje natural: 10.21s
   - ✅ Lenguaje natural más rápido

  Calidad del itinerario (MetaheuristicasItinerario):
   - Formulario: 1260.0
   - Lenguaje natural: 1230.0
   - ✅ Formulario mejor calidad

🎪 Cobertura de preferencias:
   - Formulario: 140.0%
   - Lenguaje natural: 0.0%
   - ✅ Formulario mejor cobertura

💰 Gestión presupuestaria:
   - Formulario: 100.0/100
   - Lenguaje natural: 89.9/100
   - Costo total formulario: $0.00
   - Costo total lenguaje natural: $285.00

🏛️  Lugares encontrados:
   - Formulario: 7
   - Lenguaje natural: 7

✅ Validez del itinerario:
   - Formulario válido: Sí
   - Lenguaje natural válido: Sí

🏆 Puntuación general:
   - Formulario: 97.0/100
   - Lenguaje natural: 64.5/100
   - 🎉 GANADOR: Formulario estructurado

📊 RESUMEN DETALLADO CASO 10:
==================================================
⏱️  Tiempo ejecución:
   - Formulario: 8.66s
   - Lenguaje natural: 4.54s
   - ✅ Lenguaje natural más rápido

  Calidad del itinerario (MetaheuristicasItinerario):
   - Formulario: 1290.0
   - Lenguaje natural: 0.0
   - ✅ Formulario mejor calidad

🎪 Cobertura de preferencias:
   - Formulario: 0.0%
   - Lenguaje natural: 0.0%
   - ✅ Lenguaje natural mejor cobertura

💰 Gestión presupuestaria:
   - Formulario: 0.0/100
   - Lenguaje natural: 0.0/100
   - Costo total formulario: $12800.00
   - Costo total lenguaje natural: $0.00

🏛️  Lugares encontrados:
   - Formulario: 6
   - Lenguaje natural: 0

✅ Validez del itinerario:
   - Formulario válido: No
   - Lenguaje natural válido: No

🏆 Puntuación general:
   - Formulario: 12.3/100
   - Lenguaje natural: 0.0/100
   - 🎉 GANADOR: Formulario estructurado
"""

# Expresiones regulares para extraer los datos
patrones = {
    'caso': r"RESUMEN DETALLADO CASO (\d+):",
    'tiempo_form': r"Formulario: ([\d.]+)s",
    'tiempo_nat': r"Lenguaje natural: ([\d.]+)s",
    'calidad_form': r"Formulario: ([\d.]+)\n",
    'calidad_nat': r"Lenguaje natural: ([\d.]+)\n",
    'cobertura_form': r"Formulario: ([\d.]+)%",
    'cobertura_nat': r"Lenguaje natural: ([\d.]+)%",
    'gestion_form': r"Formulario: ([\d.]+)/",
    'gestion_nat': r"Lenguaje natural: ([\d.]+)/",
    'lugares_form': r"Formulario: (\d+)",
    'lugares_nat': r"Lenguaje natural: (\d+)",
    'validez_form': r"Formulario válido: (\w+)",
    'validez_nat': r"Lenguaje natural válido: (\w+)",
    'puntuacion_form': r"Formulario: ([\d.]+)/",
    'puntuacion_nat': r"Lenguaje natural: ([\d.]+)/",
    'ganador': r"GANADOR: ([\w\s]+)|EMPATE"
}

# Procesamiento de los datos
resultados = defaultdict(list)
caso_actual = 0

for linea in datos.split('\n'):
    # Buscar número de caso
    caso_match = re.search(patrones['caso'], linea)
    if caso_match:
        caso_actual = int(caso_match.group(1))
        continue
    
    # Buscar otros datos
    for campo, patron in patrones.items():
        match = re.search(patron, linea)
        if match:
            valor = match.group(1) if campo != 'ganador' else match.group(0)
            
            if campo == 'ganador':
                if 'EMPATE' in valor:
                    valor = 'Empate'
                elif 'Formulario' in valor:
                    valor = 'Formulario'
                elif 'Lenguaje natural' in valor:
                    valor = 'Lenguaje natural'
            
            # Conversión de tipos
            if campo.startswith(('tiempo', 'calidad', 'cobertura', 'gestion', 'puntuacion')):
                try:
                    valor = float(valor)
                except ValueError:
                    continue
            elif campo.startswith('lugares'):
                valor = int(valor)
            elif campo.startswith('validez'):
                valor = 1 if valor == 'Sí' else 0
            
            resultados[campo].append(valor)
            break

# Análisis estadístico
def calcular_estadisticas(valores):
    if not valores:
        return {}
    
    return {
        'Media': np.mean(valores),
        'Mediana': np.median(valores),
        'Mínimo': np.min(valores),
        'Máximo': np.max(valores),
        'Desviación Estándar': np.std(valores),
        'Suma': np.sum(valores)
    }

# Comparativas formulario vs lenguaje natural
comparativas = {}
metricas = ['tiempo', 'calidad', 'cobertura', 'gestion', 'lugares', 'puntuacion']

for metrica in metricas:
    comparativas[metrica] = {
        'Formulario': calcular_estadisticas(resultados[f'{metrica}_form']),
        'Lenguaje Natural': calcular_estadisticas(resultados[f'{metrica}_nat'])
    }

# Conteo de victorias
victorias = {
    'Formulario': sum(1 for g in resultados['ganador'] if g == 'Formulario'),
    'Lenguaje natural': sum(1 for g in resultados['ganador'] if g == 'Lenguaje natural'),
    'Empate': sum(1 for g in resultados['ganador'] if g == 'Empate')
}

# Validez de resultados
validez = {
    'Formulario (Válidos)': sum(resultados['validez_form']),
    'Formulario (Inválidos)': len(resultados['validez_form']) - sum(resultados['validez_form']),
    'Lenguaje Natural (Válidos)': sum(resultados['validez_nat']),
    'Lenguaje Natural (Inválidos)': len(resultados['validez_nat']) - sum(resultados['validez_nat'])
}

# Generación de reportes
def imprimir_tabla(estadisticas, titulo):
    headers = ['Métrica', 'Formulario', 'Lenguaje Natural']
    tabla = []
    
    for metrica in ['Media', 'Mediana', 'Mínimo', 'Máximo', 'Desviación Estándar']:
        fila = [metrica]
        fila.append(f"{estadisticas['Formulario'].get(metrica, 0):.2f}")
        fila.append(f"{estadisticas['Lenguaje Natural'].get(metrica, 0):.2f}")
        tabla.append(fila)
    
    print(f"\n{titulo}")
    print(tabulate(tabla, headers=headers, tablefmt="grid"))

# Resultados
print("="*60)
print("ANÁLISIS ESTADÍSTICO DE RESULTADOS")
print("="*60)

# Imprimir tablas comparativas
for metrica in metricas:
    imprimir_tabla(comparativas[metrica], f"COMPARATIVA DE {metrica.upper()}")

# Resumen de victorias
print("\nRESUMEN DE VICTORIAS")
print("="*30)
for metodo, cantidad in victorias.items():
    print(f"{metodo}: {cantidad} casos")

# Validez de resultados
print("\nVALIDEZ DE ITINERARIOS")
print("="*30)
for metodo, cantidad in validez.items():
    print(f"{metodo}: {cantidad}")