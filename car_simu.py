import folium
import openrouteservice
import time
import random
import pandas as pd
import json
import os
import cv2
import numpy as np

# Your OpenRouteService API key
api_key = '5b3ce3597851110001cf6248ba7e3d9ac2dc4274b886a0edf9be574c'
client = openrouteservice.Client(key=api_key, timeout=60)

# Dataset for traffic light timings
data = {
    'District': ['Outer north', 'Outer north', 'Outer north', 'Outer north', 'Outer north'],
    'Junction': ['Between maharaja agarsen pub school', 'Ghogha chowk', 'Narela rd. station rd.', 'Raja harish chander hospital road', 'T point crpf camp'],
    'Signal_Blinker': ['Pelican', 'Blinker', 'Blinker', 'Signal With Pedestrian', 'Blinker'],
    'Latitude': [28.835195, 28.819777, 28.850621, 28.856737, 28.808122],
    'Longitude': [77.078542, 77.063503, 77.087627, 77.098443, 77.049466],
    'Cycle_time': [360, 180, 120, 240, 240],
    'Green_time': [180, 60, 60, 120, 120],
    'Yellow_time': [0, 60, 0, 0, 40],
    'Red_time': [180, 60, 60, 120, 60]
}

df = pd.DataFrame(data)

# Sample path points data
path_points = {
    'Longitude': [77.0984433, 77.088433, 77.078423, 77.068413, 77.049466],
    'Latitude': [28.8567367, 28.8467267, 28.8367167, 28.8267067, 28.808122]
}

# Convert path points to coordinates
coords_path = [(lat, lon) for lon, lat in zip(path_points['Longitude'], path_points['Latitude'])]

# Function to cache and load routes
def load_route_cache(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return {}

def save_route_cache(file_path, cache):
    with open(file_path, 'w') as file:
        json.dump(cache, file)

cache_file = 'route_cache.json'
route_cache = load_route_cache(cache_file)

# Generate route that follows the road with caching
def get_route(client, start, end):
    route_key = f'{start}-{end}'
    if route_key in route_cache:
        return route_cache[route_key]
    retry_counter = 0
    while retry_counter < 10:
        try:
            route = client.directions(coordinates=[(start[1], start[0]), (end[1], end[0])], profile='driving-car', format='geojson')
            coordinates = [(coord[1], coord[0]) for coord in route['features'][0]['geometry']['coordinates']]
            route_cache[route_key] = coordinates
            save_route_cache(cache_file, route_cache)
            return coordinates
        except openrouteservice.exceptions.ApiError as e:
            retry_counter += 1
            time.sleep(2 ** retry_counter)  # Exponential backoff
    raise Exception('Failed to get route after multiple retries')

# Combine all segments
full_route = []
for i in range(len(coords_path) - 1):
    segment = get_route(client, coords_path[i], coords_path[i+1])
    full_route.extend(segment if i == 0 else segment[1:])  # avoid duplicate points

# Create OpenCV video writer
fourcc = cv2.VideoWriter_fourcc(*'XVID')
video_writer = cv2.VideoWriter('car_movement_animation.avi', fourcc, 20.0, (800, 600))

# Helper function to add folium map to video frame
def add_map_to_frame(map_obj, frame_size=(800, 600)):
    map_img_data = map_obj._to_png(5)
    map_img = np.array(bytearray(map_img_data), dtype=np.uint8)
    map_img = cv2.imdecode(map_img, cv2.IMREAD_COLOR)
    map_img = cv2.resize(map_img, frame_size)
    return map_img

# Initial map setup
car_map = folium.Map(location=[coords_path[0][0], coords_path[0][1]], zoom_start=14)

# Add start and end markers
folium.Marker(
    location=[coords_path[0][0], coords_path[0][1]],
    popup='Start',
    icon=folium.Icon(color='green')
).add_to(car_map)

folium.Marker(
    location=[coords_path[-1][0], coords_path[-1][1]],
    popup='End',
    icon=folium.Icon(color='red')
).add_to(car_map)

# Add additional markers from points data
for index, row in df.iterrows():
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=(
            f'Junction: {row["Junction"]}<br>'
            f'Signal: {row["Signal_Blinker"]}<br>'
            f'District: {row["District"]}<br>'
            f'Green Time: {row["Green_time"]} s<br>'
            f'Yellow Time: {row["Yellow_time"]} s<br>'
            f'Red Time: {row["Red_time"]} s<br>'
            f'Cycle Time: {row["Cycle_time"]} s'
        ),
        icon=folium.Icon(color='green')
    ).add_to(car_map)

# Add green markers for all points in coords_path
for lat, lon in coords_path:
    folium.Marker(
        location=[lat, lon],
        icon=folium.Icon(color='green')
    ).add_to(car_map)

# Create frames for the animation
total_time_taken = 0
car_speed = 35  # km/h (constant speed for simplicity)
frame_interval = 0.1  # Time between frames in seconds

for i in range(len(full_route)):
    current_coords = full_route[i]
    car_map = folium.Map(location=current_coords, zoom_start=14)

    # Add start and end markers
    folium.Marker(
        location=[coords_path[0][0], coords_path[0][1]],
        popup='Start',
        icon=folium.Icon(color='green')
    ).add_to(car_map)

    folium.Marker(
        location=[coords_path[-1][0], coords_path[-1][1]],
        popup='End',
        icon=folium.Icon(color='red')
    ).add_to(car_map)

    # Draw the route path
    folium.PolyLine(locations=full_route[:i+1], color='blue').add_to(car_map)

    # Calculate the distance to the next point (in km)
    if i < len(full_route) - 1:
        next_coords = full_route[i + 1]
        distance_to_next = client.distance_matrix(
            locations=[(current_coords[1], current_coords[0]), (next_coords[1], next_coords[0])],
            profile='driving-car',
            metrics=['distance']
        )['distances'][0][1] / 1000  # convert meters to kilometers
    else:
        distance_to_next = 0

    # Calculate the time to the next point (in seconds)
    time_to_next = (distance_to_next / car_speed) * 3600  # convert hours to seconds
    total_time_taken += time_to_next

    # Check for traffic light at the current position
    for index, row in df.iterrows():
        if (abs(current_coords[0] - row['Latitude']) < 0.0001) and (abs(current_coords[1] - row['Longitude']) < 0.0001):
            cycle_time = row['Cycle_time']
            red_time = row['Red_time']

            # Calculate the wait time at the red light
            current_cycle_position = total_time_taken % cycle_time
            if current_cycle_position < red_time:
                wait_time = red_time - current_cycle_position
                total_time_taken += wait_time
                print(f"Waiting at red light for {wait_time:.2f} seconds at {row['Junction']}")

    # Simulate a random speed limit for the current position
    speed_limit = random.uniform(35, 37)
    print(f'Current speed limit: {speed_limit:.2f} km/h')

    # Add a marker for the current position with speed limit
    folium.Marker(
        location=current_coords,
        popup=f'Speed Limit: {speed_limit:.2f} km/h',
        icon=folium.Icon(color='red')
    ).add_to(car_map)

    # Add permanent green markers for all points in coords_path
    for lat, lon in coords_path:
        folium.Marker(
            location=[lat, lon],
            icon=folium.Icon(color='green')
        ).add_to(car_map)

    # Add markers from points data
    for index, row in df.iterrows():
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=(
                f'Junction: {row["Junction"]}<br>'
                f'Signal: {row["Signal_Blinker"]}<br>'
                f'District: {row["District"]}<br>'
                f'Green Time: {row["Green_time"]} s<br>'
                f'Yellow Time: {row["Yellow_time"]} s<br>'
                f'Red Time: {row["Red_time"]} s<br>'
                f'Cycle Time: {row["Cycle_time"]} s'
            ),
            icon=folium.Icon(color='green')
        ).add_to(car_map)

    # Create frame and write to video
    frame = add_map_to_frame(car_map)
    video_writer.write(frame)

# Release video writer
video_writer.release()
print("Video created successfully.")
