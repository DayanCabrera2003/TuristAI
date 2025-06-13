import folium
import webbrowser
from geopy.geocoders import Nominatim
import math


"""
En este fichero se crea un mapa con la ubicación de los lugares incluidos en el itinerario.
También determina la posición de cada lugar en el mapa, lo que permite calcular la distancia entre ellos.
Esta información se utiliza como parámetro en la función de evaluación del itinerario empleada por las metaheurísticas.
"""


def crear_mapa(lugares):
    # Coordenadas aproximadas del centro de Cuba
    cuba_center = [21.5218, -77.7812]

    # Crear el mapa centrado en Cuba con opción de zoom
    mapa = folium.Map(location=cuba_center, zoom_start=7, control_scale=True, max_zoom=30, min_zoom=7)
    geolocator = Nominatim(user_agent="turistia")
    
    for lugar in lugares:
        location = geolocator.geocode(f"{lugar}, Cuba")
        if location:
            folium.Marker([location.latitude, location.longitude], popup=lugar).add_to(mapa)
    
    # Guardar el mapa en un archivo HTML
    mapa.save("mapa_cuba.html")
    webbrowser.open("mapa_cuba.html")


def obtener_coordenadas(lugares):
    geolocator = Nominatim(user_agent="turistia")
    coordenadas = []
    
    for lugar in lugares:
        location = geolocator.geocode(f"{lugar}, Cuba")
        if location:
            coordenadas.append((location.latitude, location.longitude))
    
    return coordenadas

def distancia_haversine(coord1, coord2):
    """
    Calcula la distancia en kilómetros entre dos puntos dados por (lat, lon).
    """
    R = 6371  # Radio de la Tierra en km
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def dist_recorrido(lugares):
    """
    Calcula la distancia total del recorrido entre los lugares turísticos.
    """
    total_distancia = 0
    coordenadas = obtener_coordenadas(lugares)
    
    for i in range(len(coordenadas) - 2):
        total_distancia += distancia_haversine(coordenadas[i], coordenadas[i + 1])
    
    return total_distancia


