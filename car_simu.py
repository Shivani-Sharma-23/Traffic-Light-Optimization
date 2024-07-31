import folium
import openrouteservice
import cv2
import numpy as np
import random
import time
from IPython.display import display, clear_output

# Initialize OpenRouteService client
api_key = '5b3ce3597851110001cf62487dab724e881e4bfeab36d60cd37e61f6'
client = openrouteservice.Client(key=api_key)

# Define start and end coordinates
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

# Initialize folium map
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

# Add distance and duration info
distance = route['features'][0]['properties']['segments'][0]['distance'] / 1000
duration = route['features'][0]['properties']['segments'][0]['duration'] / 60

folium.map.Marker(
    [start_coords[0], start_coords[1]],
    icon=folium.DivIcon(
        html=f'<div style="font-size: 16pt">Distance: {distance:.2f} km<br>Duration: {duration:.2f} min</div>'
    )
).add_to(car_map)

# Save the initial map as an HTML file
car_map.save('car_movement_directions_map.html')

# Create a video writer
video_name = 'route_animation.avi'
frame_rate = 10  # frames per second
frame_size = (800, 600)

# Initialize video writer
fourcc = cv2.VideoWriter_fourcc(*'XVID')
video_writer = cv2.VideoWriter(video_name, fourcc, frame_rate, frame_size)

# Function to render map to image
def map_to_image(fmap, frame_size):
    fmap.save('temp_map.html')
    # Use selenium or an equivalent to capture map screenshot
    img = np.array(folium.Map()._to_png(5))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return cv2.resize(img, frame_size)

# Animate the route
for i, current_coords in enumerate(route_coords):
    clear_output(wait=True)
    car_map = folium.Map(location=current_coords, zoom_start=14)
    folium.GeoJson(route, name='route').add_to(car_map)
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

    folium.PolyLine(locations=route_coords[:i + 1], color='blue').add_to(car_map)

    # Add speed limit (randomly generated for demonstration)
    speed_limit = random.uniform(35, 37)
    folium.Marker(
        location=current_coords,
        popup=f'Speed Limit: {speed_limit:.2f} km/h',
        icon=folium.Icon(color='red')
    ).add_to(car_map)

    # Convert map to image and write to video
    img = map_to_image(car_map, frame_size)
    video_writer.write(img)

    # Display the current frame (optional)
    display(car_map)
    time.sleep(0.1)

# Release the video writer
video_writer.release()

# Display completion message
print("Route animation has been saved to", video_name)
