from flask import Flask, render_template, request, jsonify
import folium
import openrouteservice
import random
from geopy.distance import geodesic
import pandas as pd

app = Flask(__name__)

# Initialize OpenRouteService client
api_key = '5b3ce3597851110001cf62487dab724e881e4bfeab36d60cd37e61f6'
client = openrouteservice.Client(key=api_key)

# Sample dataset
file_path = "gurugram_data.csv"
data = pd.read_csv(file_path)

def is_near_route(point, route_coords, threshold=0.5):
    """Check if a point is within the threshold distance (in km) of the route."""
    point_lat, point_lon = point
    for route_lat, route_lon in route_coords:
        if geodesic((point_lat, point_lon), (route_lat, route_lon)).km <= threshold:
            return True
    return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/route', methods=['POST'])
def route():
    start_address = request.form['start']
    end_address = request.form['end']

    # Convert addresses to coordinates (For demonstration purposes, using dummy coordinates)
    start_coords = (28.4291, 77.0984433)
    end_coords = (28.4592, 77.049466)

    # Get the route
    route = client.directions(
        coordinates=[(start_coords[1], start_coords[0]), (end_coords[1], end_coords[0])],
        profile='driving-car',
        format='geojson'
    )

    # Extract route coordinates
    route_coords = [(coord[1], coord[0]) for coord in route['features'][0]['geometry']['coordinates']]

    # Filter path_points that are near the route
    threshold_distance = 0.5
    filtered_path_points = data[
        data.apply(lambda row: is_near_route((row['latitude'], row['longitude']), route_coords, threshold_distance), axis=1)
    ]

    # Generate map with route and points
    car_map = folium.Map(location=[start_coords[0], start_coords[1]], zoom_start=14)
    folium.GeoJson(route, name='route').add_to(car_map)

    # Add start and end markers
    folium.Marker(
        location=[start_coords[0], start_coords[1]],
        popup='Start',
        icon=folium.Icon(color='green')
    ).add_to(car_map)

    folium.Marker(
        location=[end_coords[0], end_coords[1]],
        popup='End',
        icon=folium.Icon(color='red')
    ).add_to(car_map)

    # Add filtered path points markers (with blue color)
    for idx, row in filtered_path_points.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f'Point {idx}',
            icon=folium.Icon(color='blue')
        ).add_to(car_map)

    # Add distance and duration info
    distance = route['features'][0]['properties']['segments'][0]['distance'] / 1000
    duration = route['features'][0]['properties']['segments'][0]['duration'] / 60

    folium.map.Marker(
        [start_coords[0], start_coords[1]],
        icon=folium.DivIcon(
            html=f'<div style="font-size: 16pt">Distance: {distance:.2f} km<br>Duration: {duration:.2f} min</div>'
        )
    ).add_to(car_map)

    # Generate random speed limits for each route segment
    speed_limits = [random.uniform(50, 80) for _ in route_coords]

    # Save the map to HTML string
    map_html = car_map._repr_html_()

    return jsonify({'map_html': map_html, 'route_coords': route_coords, 'speed_limits': speed_limits})

if __name__ == '__main__':
    app.run(debug=True)
