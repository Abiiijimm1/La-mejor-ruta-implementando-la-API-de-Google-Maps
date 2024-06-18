from flask import Flask, request, render_template
import folium
from geopy.geocoders import Nominatim
import googlemaps

app = Flask(__name__)

consumo_combustible = 12  
costo_gasolina = 23.86  
costo_estimado_peaje = 50  


gmaps = googlemaps.Client(key='AIzaSyDCdlWcmsljkLcA2fcN3TkvFaUOL4d3tbM')

def geocode_place(place_name):
    geolocator = Nominatim(user_agent="route_finder")
    location = geolocator.geocode(place_name)
    return (location.latitude, location.longitude) if location else None

def get_toll_cost(route):
    total_toll_cost = 0
    if 'legs' in route and 'steps' in route['legs'][0]:
        steps = route['legs'][0]['steps']
        for step in steps:
            if 'html_instructions' in step and 'toll' in step['html_instructions'].lower():
                total_toll_cost += costo_estimado_peaje
    return total_toll_cost

@app.route('/')
def index():
    return render_template('index.html', results="", map_html="")

@app.route('/route', methods=['POST'])
def route():
    origin_name = request.form['origin']
    destination_name = request.form['destination']

    origin_coords = geocode_place(origin_name)
    destination_coords = geocode_place(destination_name)

    if not origin_coords or not destination_coords:
        return f"Error: no se pudo geocodificar {origin_name if not origin_coords else destination_name}"

    directions_result = gmaps.directions(
        origin=f"{origin_coords[0]},{origin_coords[1]}",
        destination=f"{destination_coords[0]},{destination_coords[1]}",
        mode="driving",
        alternatives=False,
        departure_time="now"  
    )

    if not directions_result:
        return "Error al obtener la ruta desde la API de Google Maps"

    route = directions_result[0]
    distance_meters = route['legs'][0]['distance']['value']
    distance_km = distance_meters / 1000
    duration_seconds = route['legs'][0]['duration']['value']
    duration_in_traffic_seconds = route['legs'][0].get('duration_in_traffic', {'value': duration_seconds})['value']
    hours = int(duration_seconds // 3600)
    minutes = int((duration_seconds % 3600) // 60)
    traffic_hours = int(duration_in_traffic_seconds // 3600)
    traffic_minutes = int((duration_in_traffic_seconds % 3600) // 60)
    traffic_status = "con tráfico" if duration_in_traffic_seconds > duration_seconds else "sin tráfico"
    steps = route['legs'][0]['steps']
    route_coords = [(step['start_location']['lat'], step['start_location']['lng']) for step in steps]
    route_coords.append((steps[-1]['end_location']['lat'], steps[-1]['end_location']['lng']))

    litros_necesarios = distance_km / consumo_combustible
    costo_gasolina_total = litros_necesarios * costo_gasolina
    costo_casetas = get_toll_cost(route)

    m = folium.Map(location=origin_coords, zoom_start=10)
    folium.Marker(location=origin_coords, popup='Origen', icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(location=destination_coords, popup='Destino', icon=folium.Icon(color='red')).add_to(m)
    folium.PolyLine(route_coords, color='blue', weight=2.5, opacity=1).add_to(m)

    map_html = m._repr_html_()

    results = f"""
    <h2>Ruta más corta de {origin_name} a {destination_name}:</h2>
    <p><img src="https://img.icons8.com/dusk/64/000000/road.png" alt="Distancia" style="vertical-align: middle;"> Distancia: {distance_km:.2f} km</p>
    <p><img src="https://img.icons8.com/color/48/000000/clock--v1.png" alt="Duración sin tráfico" style="vertical-align: middle;"> Duración sin tráfico: {hours} horas y {minutes} minutos</p>
    <p><img src="https://img.icons8.com/color/48/000000/clock--v1.png" alt="Duración con tráfico" style="vertical-align: middle;"> Duración con tráfico: {traffic_hours} horas y {traffic_minutes} minutos</p>
    <p><img src="https://img.icons8.com/color/48/000000/traffic-jam.png" alt="Estado del tráfico" style="vertical-align: middle;"> Estado del tráfico: {traffic_status}</p>
    <p><img src="https://img.icons8.com/color/48/000000/gas-station.png" alt="Costo de gasolina" style="vertical-align: middle;"> Costo de gasolina: ${costo_gasolina_total:.2f} MXN</p>
    <p><img src="https://img.icons8.com/color/48/000000/tollbooth.png" alt="Costo de casetas" style="vertical-align: middle;"> Costo de casetas: ${costo_casetas:.2f} MXN</p>
    <p><img src="https://img.icons8.com/color/48/000000/money.png" alt="Costo total estimado" style="vertical-align: middle;"> Costo total estimado: ${costo_gasolina_total + costo_casetas:.2f} MXN</p>
    """

    return render_template('index.html', results=results, map_html=map_html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
