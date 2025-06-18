import streamlit as st
from planner.planning import Planer
import os
import planner.mapaCuba as mapaCuba


st.set_page_config(page_title="Formulario Turístico", layout="centered")


opcionesLugares = [
    "Pinar del Río", "Artemisa", "La Habana", "Mayabeque", "Matanzas", "Cienfuegos",
    "Villa Clara", "Sancti Spíritus", "Ciego de Ávila", "Camagüey", "Las Tunas",
    "Holguín", "Granma", "Santiago de Cuba", "Guantánamo", "Isla de la Juventud", "Marcar todas"
]

opciones = [
    "Culturales", "Gastronomía", "Playa", "Naturaleza", "Historia",
    "Relajación", "Musical", "Religiosas", "Otros", "Marcar todas"
]

# Inicializa el estado de la página
if "pagina" not in st.session_state:
    st.session_state.pagina = "inicio"

if "actividades_seleccionadas" not in st.session_state:
    st.session_state.actividades_seleccionadas = []
if "seleccionAct" not in st.session_state:
    st.session_state.seleccionAct = []
if "seleccionLug" not in st.session_state:
    st.session_state.seleccionLug = []
if "diasVacaciones" not in st.session_state:
    st.session_state.diasVacaciones = 0
if "presupuestoDisponible" not in st.session_state:
    st.session_state.presupuestoDisponible = 0
if "max_cant_lugares" not in st.session_state:
    st.session_state.max_cant_lugares = True
if "min_presupuesto" not in st.session_state:
    st.session_state.min_presupuesto = False


if st.session_state.pagina == "inicio":
    st.title("Formulario de Actividades Turísticas")
    st.write("Por favor, seleccione las actividades que le gustaría realizar durante su visita.")
    st.write("Puede seleccionar varias opciones y luego proceder al siguiente paso.")

    dias = st.number_input(
        "¿Cuántos días durarán sus vacaciones?",
        min_value=1,
        max_value=30,
        step=1,
        format="%d"
    )
    st.session_state.diasVacaciones = dias
    presupuesto_ilimitado = st.checkbox("Presupuesto ilimitado")
    if presupuesto_ilimitado:
        presupuesto = "Ilimitado"
        st.session_state.presupuestoDisponible = -float('inf')
    else:
        presupuesto = st.number_input(
            "¿Con cuánto presupuesto cuenta? (USD)",
            min_value=1,
            step=1,
            format="%d"
        )
        st.session_state.presupuestoDisponible = presupuesto

    cols = st.columns([1, 1])
    with cols[0]:
        pass  # No hay botón "Anterior" en la primera página
    with cols[1]:
        if st.button("Siguiente"):
            st.session_state.dias_vacaciones = dias
            st.session_state.presupuesto = presupuesto
            st.session_state.pagina = "tipo actividades"
            st.rerun()

if st.session_state.pagina == "tipo actividades":
    st.title("¿Qué tipo de lugares le gustaría visitar?")
    seleccion = []
    for opcion in opciones:
        checked = st.session_state.get(f"tipo_chk_{opcion}", False)
        new_checked = st.checkbox(opcion, value=checked, key=f"tipo_chk_{opcion}")
        if new_checked:
            seleccion.append(opcion)
    cols = st.columns([1, 1])
    with cols[0]:
        if st.button("Anterior"):
            st.session_state.pagina = "inicio"
            st.rerun()
    with cols[1]:
        if st.button("Siguiente"):
            if "Marcar todas" in seleccion:
                st.session_state.actividades_seleccionadas = opciones[:-1]  # Todas menos "Marcar todas"
            else:
                st.session_state.actividades_seleccionadas = seleccion
            st.session_state.pagina = "subformulario tipos de actividades"
            st.rerun()

if st.session_state.pagina == "subformulario tipos de actividades":
    st.title("¿Qué lugares le gustaría visitar?")
    subopciones = []

    if "Culturales" in st.session_state.actividades_seleccionadas:
        opcionesCulturales = [
            "Museos", "Galerías de arte", "Obras de teatro", "Espectáculos", "Carnavales",
            "Centros históricos y patrimoniales"
        ]
        subopciones.extend(opcionesCulturales)

    if "Gastronomía" in st.session_state.actividades_seleccionadas:
        opcionesGastronomicas = ["Gastronomía local", "Heladerías", "Dulcerías"]
        subopciones.extend(opcionesGastronomicas)

    if "Playa" in st.session_state.actividades_seleccionadas:
        opcionesPlaya = ["Varadero", "Cayos", "Guardalavaca", "Playa Pesquero", "Playa Ancón", "Hoteles"]
        subopciones.extend(opcionesPlaya)

    if "Naturaleza" in st.session_state.actividades_seleccionadas:
        opcionesNaturaleza = [
            "Senderismo", "Excursiones", "Observación de flora", "Observación de fauna",
            "Parques Nacionales", "Reservas" ]
        subopciones.extend(opcionesNaturaleza)

    if "Historia" in st.session_state.actividades_seleccionadas:
        opcionesHistoria = ["Fortalezas", "Castillos", "Casas-museo", "Museos de historia"]
        subopciones.extend(opcionesHistoria)

    if "Relajación" in st.session_state.actividades_seleccionadas:
        opcionesRelajacion = ["Spa", "Resorts"]
        subopciones.extend(opcionesRelajacion)

    if "Musical" in st.session_state.actividades_seleccionadas:
        opcionesMusical = ["Conciertos", "Festivales de música", "Clubs nocturnos", "Bares"]
        subopciones.extend(opcionesMusical)

    if "Religiosas" in st.session_state.actividades_seleccionadas:
        opcionesReligiosas = ["Iglesias", "Catedrales", "Festividades religiosas"]
        subopciones.extend(opcionesReligiosas)
    
    if len(subopciones) > 0:
        subopciones.extend(["Otras", "Marcar todas"])
        
        for opcion in subopciones:
            if opcion not in st.session_state.seleccionAct:
                checked = st.session_state.get(f"sub_chk_{opcion}", False)
            else:
                checked = True
            new_checked = st.checkbox(opcion, value=checked, key=f"sub_chk_{opcion}")
            if new_checked:
                st.session_state.seleccionAct.append(opcion)

        cols = st.columns([1, 1])
        with cols[0]:
            if st.button("Anterior"):
                st.session_state.pagina = "tipo actividades"
                st.rerun()
        with cols[1]:
            if st.button("Siguiente", key="sub_siguiente"):
                if "Marcar todas" in st.session_state.seleccionAct:
                    st.session_state.seleccionAct = subopciones[:-1]  # Todas menos "Marcar todas"

                st.session_state.pagina = "formulario lugares"
                st.rerun()

if st.session_state.pagina == "formulario lugares":
    st.title("¿Qué lugares le gustaría visitar?")

    for opcion in opcionesLugares:
        checked = st.session_state.get(f"lug_chk_{opcion}", False)
        new_checked = st.checkbox(opcion, value=checked, key=f"lug_chk_{opcion}")
        if new_checked:
            st.session_state.seleccionLug.append(opcion)
    cols = st.columns([1, 1])
    with cols[0]:
        if st.button("Anterior"):
            st.session_state.pagina = "subformulario tipos de actividades"
            st.rerun()
    with cols[1]:
        if st.button("Siguiente"):
            if "Marcar todas" in st.session_state.seleccionLug:
                st.session_state.seleccionLug = opcionesLugares[:-1]  # Todas menos "Marcar todas"
            st.session_state.pagina = "Optimizacion"
            st.rerun()

if st.session_state.pagina == "Optimizacion":
    st.title("¿Qué le interesa?")
    opciones = [ "Visitar la mayor cantidad de lugares", "Reducir el presupuesto", "Ambas opciones" ]
    for opcion in opciones:
        checked = st.session_state.get(f"lug_chk_{opcion}", False)
        new_checked = st.checkbox(opcion, value=checked, key=f"lug_chk_{opcion}")
        if new_checked:
            st.session_state.max_cant_lugares = True if opcion == "Visitar la mayor cantidad de lugares" else False
            st.session_state.min_presupuesto = True if opcion == "Reducir el presupuesto" else False
    cols = st.columns([1, 1])
    with cols[0]:
        if st.button("Anterior"):
            st.session_state.pagina = "formulario lugares"
            st.rerun()
    with cols[1]:
        if st.button("Siguiente"):
            if "Marcar todas" in st.session_state.seleccionLug:
                st.session_state.max_cant_lugares = True 
                st.session_state.min_presupuesto = True
            st.success("¡Formulario completado!")
            st.session_state.pagina = "Itinerario"
            st.rerun()
    
if st.session_state.pagina == "Itinerario":
    st.title("Generando itinerario...")
    planer = Planer(
        st.session_state.seleccionLug,
        st.session_state.seleccionAct,
        st.session_state.diasVacaciones,
        st.session_state.presupuestoDisponible,
        st.session_state.max_cant_lugares,
        st.session_state.min_presupuesto
    )
    itinerario, _ = planer.generate_itinerary()
    st.title("Itinerario Propuesto")
    st.write("Aquí se mostraría el itinerario propuesto basado en sus selecciones.")
    # Imprime el itinerario de forma bonita
    # Asume que cada actividad es un dict con las claves: 'nombre', 'descripcion', 'ciudad', 'precio'
    
    lugares = []

    def mostrar_actividad(actividad):
        nombre = actividad.get('nombre', 'Sin nombre')
        descripcion = actividad.get('descripcion', 'Sin descripción')
        ciudad = actividad.get('ciudad', 'Sin ciudad')
        precio = actividad.get('precio', 'Sin precio')
        st.markdown(f"**Lugar:** {nombre}")
        st.markdown(f"**Descripción:** {descripcion}")
        st.markdown(f"**Ciudad:** {ciudad}")
        st.markdown(f"**Precio:** {precio} USD")
        st.markdown("---")
        str = nombre + ", " + ciudad
        lugares.append(str)

    
    if isinstance(itinerario, dict):
        for dia, actividades in itinerario.items():
            st.subheader(f"Día {dia}")
            if isinstance(actividades, list):
                for actividad in actividades:
                    if isinstance(actividad, dict):
                        mostrar_actividad(actividad)
            elif isinstance(actividades, dict):
                mostrar_actividad(actividades)
    elif isinstance(itinerario, list):
        for idx, actividades in enumerate(itinerario, 1):
            st.subheader(f"Día {idx}")
            if isinstance(actividades, list):
                for actividad in actividades:
                    if isinstance(actividad, dict):
                        mostrar_actividad(actividad)
            elif isinstance(actividades, dict):
                mostrar_actividad(actividades)
    elif isinstance(itinerario, dict):
        mostrar_actividad(itinerario)
    else:
        st.write("No hay actividades para mostrar.")
    
    
    try:
        mapaCuba.crear_mapa(lugares)
        with open("mapa_cuba.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        st.components.v1.html(html_content, height=600, scrolling=True)
    except Exception as e:
        st.warning(f"No se pudo generar el mapa: {e}")
    st.session_state.pagina = "Finalizado"


