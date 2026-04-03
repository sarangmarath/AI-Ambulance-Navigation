from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from flask_socketio import SocketIO
from map_loader import load_chennai_map, get_nearest_node
from astar import astar, precompute_traffic_weights
import folium
import os
import math

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

print("Loading Chennai map...")
G = load_chennai_map()
traffic_weights = precompute_traffic_weights(G)
print("Server ready!")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, '..', 'frontend')

ambulances = {
    "AMB-01": {"lat": 13.0827, "lon": 80.2707, "status": "available"},
    "AMB-02": {"lat": 13.0569, "lon": 80.2425, "status": "available"},
    "AMB-03": {"lat": 13.1067, "lon": 80.2206, "status": "available"},
}

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def find_nearest_ambulance(patient_lat, patient_lon, radius_km=10):
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
    patient = {"name": "Critical Patient", "lat": 13.03, "lon": 80.22}
    socketio.emit('new_emergency', patient)
    return jsonify({"message": "Emergency alert sent!"})

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    patient_lat = data['lat']
    patient_lon = data['lon']
    patient_name = data.get('name', 'Unknown')

    print(f"Emergency: {patient_name} at {patient_lat}, {patient_lon}")

    amb_id, dist = find_nearest_ambulance(patient_lat, patient_lon, radius_km=10)
    if not amb_id:
        return jsonify({"error": "No ambulances available within 10km radius!"}), 400

    ambulances[amb_id]['status'] = 'busy'
    amb_lat = ambulances[amb_id]['lat']
    amb_lon = ambulances[amb_id]['lon']

    start_node = get_nearest_node(G, amb_lat, amb_lon)
    goal_node = get_nearest_node(G, patient_lat, patient_lon)

    print(f"Running A* with ML traffic weights...")
    path, cost = astar(G, start_node, goal_node, traffic_weights)

    if not path:
        return jsonify({"error": "No road path found!"}), 400

    path_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in path]

    center_lat = (amb_lat + patient_lat) / 2
    center_lon = (amb_lon + patient_lon) / 2

    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    folium.Marker(
        [amb_lat, amb_lon],
        popup=folium.Popup(f"Ambulance {amb_id}", max_width=200),
        icon=folium.Icon(color='blue', icon='plus', prefix='fa')
    ).add_to(m)

    folium.Marker(
        [patient_lat, patient_lon],
        popup=folium.Popup(f"Patient: {patient_name}", max_width=200),
        icon=folium.Icon(color='red', icon='heart', prefix='fa')
    ).add_to(m)

    folium.PolyLine(
        path_coords,
        color='red',
        weight=6,
        opacity=0.85,
        tooltip=f"A* Optimal Route — {round(cost/1000, 2)} km"
    ).add_to(m)

    folium.FitBounds([
        [min(amb_lat, patient_lat), min(amb_lon, patient_lon)],
        [max(amb_lat, patient_lat), max(amb_lon, patient_lon)]
    ]).add_to(m)

    map_path = os.path.join(FRONTEND_DIR, 'route_map.html')
    m.save(map_path)

    # Inject ambulance animation script into map
    animation_script = """
<script>
var ambulanceMarker = null;
var mapObj = null;

function getMap() {
    try {
        var keys = Object.keys(window);
        for (var i = 0; i < keys.length; i++) {
            var val = window[keys[i]];
            if (val && val._container && val.panTo && val.setView) {
                return val;
            }
        }
    } catch(e) {}
    return null;
}

window.addEventListener('message', function(e) {
    if (!e.data || e.data.type !== 'updateAmbulance') return;

    var lat = e.data.lat;
    var lon = e.data.lon;

    if (!mapObj) {
        mapObj = getMap();
    }
    if (!mapObj) return;

    if (ambulanceMarker) {
        ambulanceMarker.setLatLng([lat, lon]);
    } else {
        var ambulanceIcon = L.divIcon({
            html: '<div style="font-size:28px; filter: drop-shadow(2px 2px 2px rgba(0,0,0,0.5));">🚑</div>',
            iconSize: [35, 35],
            iconAnchor: [17, 17],
            className: ''
        });
        ambulanceMarker = L.marker([lat, lon], {icon: ambulanceIcon}).addTo(mapObj);
    }

    mapObj.panTo([lat, lon], {animate: true, duration: 0.5});
});
</script>
"""

    with open(map_path, 'r', encoding='utf-8') as f:
        map_html = f.read()

    map_html = map_html.replace('</body>', animation_script + '</body>')

    with open(map_path, 'w', encoding='utf-8') as f:
        f.write(map_html)

    socketio.emit('route_ready', {
        "patient": patient_name,
        "distance_km": round(cost / 1000, 2),
        "nodes": len(path),
        "path_coords": path_coords
    })

    return jsonify({
        "success": True,
        "distance_km": round(cost / 1000, 2),
        "nodes": len(path)
    })

@app.route('/ambulances')
def get_ambulances():
    return jsonify(ambulances)

@app.route('/reset', methods=['POST'])
def reset():
    for amb in ambulances:
        ambulances[amb]['status'] = 'available'
    return jsonify({"message": "All ambulances reset!"})

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)