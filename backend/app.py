from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from flask_socketio import SocketIO
from map_loader import load_chennai_map, get_nearest_node
from astar import astar
import folium
import os
import math

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

print(" Loading Chennai map...")
G = load_chennai_map()
print(" Server ready!")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, '..', 'frontend')

# Ambulances with real Chennai locations
ambulances = {
    "AMB-01": {"lat": 13.0827, "lon": 80.2707, "status": "available"},
    "AMB-02": {"lat": 13.0569, "lon": 80.2425, "status": "available"},
    "AMB-03": {"lat": 13.1067, "lon": 80.2206, "status": "available"},
}

def haversine(lat1, lon1, lat2, lon2):
    """Calculate real-world distance in km between two GPS points"""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def find_nearest_ambulance(patient_lat, patient_lon, radius_km=10):
    """Find nearest available ambulance within radius_km"""
    best_amb = None
    best_dist = float('inf')

    for amb_id, amb in ambulances.items():
        if amb['status'] != 'available':
            continue
        dist = haversine(patient_lat, patient_lon, amb['lat'], amb['lon'])
        print(f"  {amb_id} is {dist:.2f} km away")
        if dist <= radius_km and dist < best_dist:
            best_dist = dist
            best_amb = amb_id

    return best_amb, round(best_dist, 2)

@app.route('/')
def serve_frontend():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)

@app.route('/simulate')
def simulate():
    """Simulate an incoming emergency alert"""
    patient = {
        "name": "Critical Patient",
        "lat": 13.03,
        "lon": 80.22
    }
    socketio.emit('new_emergency', patient)
    return jsonify({"message": "Emergency alert sent!"})

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    patient_lat = data['lat']
    patient_lon = data['lon']
    patient_name = data.get('name', 'Unknown')
    driver_lat = data.get('driver_lat')
    driver_lon = data.get('driver_lon')

    print(f" Emergency: {patient_name} at {patient_lat}, {patient_lon}")

    # If driver location provided, use it directly
    # Otherwise find nearest ambulance within 10km

    # Always find nearest ambulance from fleet — ignore browser GPS
    amb_id, dist = find_nearest_ambulance(patient_lat, patient_lon, radius_km=10)
    if not amb_id:
        return jsonify({"error": "No ambulances available within 10km radius!"}), 400
    ambulances[amb_id]['status'] = 'busy'
    amb_lat = ambulances[amb_id]['lat']
    amb_lon = ambulances[amb_id]['lon']
    amb_label = f" {amb_id}"

    # Run A* on real road network
    start_node = get_nearest_node(G, amb_lat, amb_lon)
    goal_node = get_nearest_node(G, patient_lat, patient_lon)

    print(f" Running A* algorithm...")
    path, cost = astar(G, start_node, goal_node)

    if not path:
        return jsonify({"error": "No road path found!"}), 400

    path_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in path]

    # Build folium map centered between ambulance and patient
    center_lat = (amb_lat + patient_lat) / 2
    center_lon = (amb_lon + patient_lon) / 2

    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    # Ambulance marker
    folium.Marker(
        [amb_lat, amb_lon],
        popup=folium.Popup(amb_label, max_width=200),
        icon=folium.Icon(color='blue', icon='plus', prefix='fa')
    ).add_to(m)

    # Patient marker
    folium.Marker(
        [patient_lat, patient_lon],
        popup=folium.Popup(f" {patient_name}", max_width=200),
        icon=folium.Icon(color='red', icon='heart', prefix='fa')
    ).add_to(m)

    # Draw A* route
    folium.PolyLine(
        path_coords,
        color='red',
        weight=6,
        opacity=0.85,
        tooltip=f"A* Optimal Route — {round(cost/1000, 2)} km"
    ).add_to(m)

    # Fit map to show full route
    folium.FitBounds([
        [min(amb_lat, patient_lat), min(amb_lon, patient_lon)],
        [max(amb_lat, patient_lat), max(amb_lon, patient_lon)]
    ]).add_to(m)

    map_path = os.path.join(FRONTEND_DIR, 'route_map.html')
    m.save(map_path)

    socketio.emit('route_ready', {
        "patient": patient_name,
        "distance": round(cost),
        "distance_km": round(cost / 1000, 2),
        "nodes": len(path)
    })

    return jsonify({
        "success": True,
        "distance_km": round(cost / 1000, 2),
        "nodes": len(path)
    })

@app.route('/ambulances')
def get_ambulances():
    # Also return distance info
    return jsonify(ambulances)

@app.route('/reset', methods=['POST'])
def reset():
    for amb in ambulances:
        ambulances[amb]['status'] = 'available'
    return jsonify({"message": "All ambulances reset!"})

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)