import streamlit as st

st.set_page_config(page_title="Formulario Turístico", layout="centered")
seleccionAct = []
seleccionLug = []
diasVacaciones = 0
presupuestoDisponible = 0


opcionesLugares = [
    "Pinar del Río", "Artemisa", "La Habana", "Mayabeque", "Matanzas", "Villa Clara",
    "Sancti Spíritus", "Holguín", "Cienfuegos", "Granma", "Santiago de Cuba", "Marcar todas"
]

opciones = [
    "Culturales", "Gastronomía", "Playa", "Naturaleza", "Historia",
    "Relajación", "Musical", "Hoteles", "Religiosas", "Otros", "Marcar todas"
]

# Inicializa el estado de la página
if "pagina" not in st.session_state:
    st.session_state.pagina = "inicio"

if "actividades_seleccionadas" not in st.session_state:
    st.session_state.actividades_seleccionadas = []

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
    diasVacaciones = dias
    presupuesto_ilimitado = st.checkbox("Presupuesto ilimitado")
    if presupuesto_ilimitado:
        presupuesto = "Ilimitado"
        presupuestoDisponible = -float('inf')
    else:
        presupuesto = st.number_input(
            "¿Con cuánto presupuesto cuenta? (USD)",
            min_value=1,
            step=1,
            format="%d"
        )
        presupuestoDisponible = presupuesto

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
    if st.button("Siguiente"):
        if "Marcar todas" in seleccion:
            st.session_state.actividades_seleccionadas = opciones[:-1]  # Todas menos "Marcar todas"
        else:
            st.session_state.actividades_seleccionadas = seleccion
        st.session_state.pagina = "subformulario tipos de actividades"
        st.rerun()
    if st.button("Anterior"):
        st.session_state.pagina = "inicio"
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
        opcionesGastronomia = ["Gastronomía local", "Heladerías", "Dulcerías"]
        subopciones.extend(opcionesGastronomia)

    if "Playa" in st.session_state.actividades_seleccionadas:
        opcionesPlaya = ["Varadero", "Cayos", "Guardalavaca", "Playa Pesquero", "Playa Ancón"]
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
        subopciones.extend(["Marcar todas", "Otras"])

        for opcion in subopciones:
            checked = st.session_state.get(f"sub_chk_{opcion}", False)
            new_checked = st.checkbox(opcion, value=checked, key=f"sub_chk_{opcion}")
            if new_checked:
                seleccionAct.append(opcion)

        if st.button("Siguiente", key="sub_siguiente"):
            if "Marcar todas" in seleccionAct:
                seleccionAct = opciones[:-1]  # Todas menos "Marcar todas"
            st.session_state.pagina = "formulario lugares"
            st.rerun()
        if st.button("Anterior"):
            st.session_state.pagina = "tipo actividades"
            st.rerun()

if st.session_state.pagina == "formulario lugares":
    st.title("¿Qué lugares le gustaría visitar?")

    for opcion in opcionesLugares:
        checked = st.session_state.get(f"lug_chk_{opcion}", False)
        new_checked = st.checkbox(opcion, value=checked, key=f"lug_chk_{opcion}")
        if new_checked:
            seleccionLug.append(opcion)
    if st.button("Anterior"):
        st.session_state.pagina = "subformulario tipos de actividades"
        st.rerun()
    if st.button("Siguiente"):
        if "Marcar todas" in seleccionLug:
            seleccionLug = opcionesLugares[:-1]  # Todas menos "Marcar todas"
        st.success("¡Formulario completado!")
        


