# MEDRoute — AI Ambulance Navigation / Simulated

An AI-powered emergency ambulance dispatch system that uses the A* Search Algorithm combined with a Random Forest ML model to find the optimal traffic-aware route from an ambulance to a patient in the shortest possible time.

---

## Overview

Emergency response time is critical in saving lives. RapidRoute is a hospital-side web application that receives emergency alerts, identifies the nearest available ambulance within a 10km radius, predicts road congestion using machine learning, and computes the fastest road route using a custom implementation of the A* pathfinding algorithm on real Chennai road data.

Once the route is calculated, the dashboard shows a live ambulance animation moving along the optimal path in real time.

---

## Features

- Real-time emergency alert system using WebSockets
- Nearest ambulance detection within a 10km radius using the Haversine formula
- Custom A* algorithm implementation on real OpenStreetMap road network
- Random Forest ML model predicting traffic congestion on 173,000+ road edges
- Traffic-aware routing — A* avoids congested roads automatically
- Live ambulance animation moving along the route on the map
- Hospital dispatch dashboard with ambulance fleet status

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask, Flask-SocketIO |
| Algorithm | A* Search (custom implementation) |
| Machine Learning | Random Forest Regressor (scikit-learn) |
| Map Data | OpenStreetMap via OSMnx |
| Frontend | HTML, CSS, JavaScript |
| Real-time | WebSockets |
| Map Rendering | Folium |

---

## How It Works

1. The hospital receives an emergency alert with the patient's location
2. The system uses the Haversine formula to find the nearest available ambulance within 10km
3. The Random Forest ML model predicts congestion scores for all road edges based on current time, day, road type and monsoon season
4. The A* algorithm runs on Chennai's real road network using traffic-aware edge weights
5. The optimal route is displayed on a live map with an ambulance marker animating along the path in real time

---

## Machine Learning Model

The Random Forest model is trained on 15,000 Chennai traffic records.

Features used for prediction:
- Hour of day
- Day of week
- Weekend or weekday
- Month
- Monsoon season (June to November)
- Road type (primary, secondary, tertiary, residential, trunk)
- Road length

Model performance:
- Accuracy: 97.46%
- Mean Absolute Error: 0.04

The predicted congestion score is multiplied with road length to create a traffic-aware edge weight. A* naturally avoids heavier edges — finding the fastest route rather than just the shortest.

---

## Algorithm

The A* algorithm is implemented from scratch in `astar.py`.

- `g(n)` — actual traffic-aware road cost from start node
- `h(n)` — straight-line heuristic distance to the goal using GPS coordinates
- `f(n) = g(n) + h(n)` — total estimated cost used to prioritize exploration

Traffic weights for all 173,000+ road edges are pre-computed once at server startup using batch ML prediction — making each route calculation fast.

---

## Project Structure

```
ambulance-app/
│
├── backend/
│   ├── app.py                  # Flask server and API routes
│   ├── astar.py                # A* algorithm with ML traffic weights
│   ├── map_loader.py           # OSMnx Chennai road network loader
│   ├── train_model.py          # Random Forest model training script
│   ├── traffic_model.pkl       # Trained ML model
│   └── road_type_encoder.pkl   # Road type label encoder
│
├── frontend/
│   ├── index.html              # Hospital dashboard UI
│   ├── style.css               # Styling
│   └── script.js               # Real-time alerts and ambulance animation
│
└── maps/
    └── chennai.graphml         # Saved Chennai road network (auto-generated)
```

---

## Setup and Installation

### 1. Install dependencies

```bash
pip install osmnx networkx flask flask-socketio flask-cors folium scikit-learn pandas numpy
```

### 2. Train the ML model (first time only)

```bash
cd backend
python train_model.py
```

### 3. Run the server

```bash
python app.py
```

### 4. Open the dashboard

```
http://127.0.0.1:5000
```

### 5. Simulate an emergency alert

```
http://127.0.0.1:5000/simulate
```

---

## Demo

1. Start the Flask server and wait for traffic weights to be computed
2. Open the dashboard at `http://127.0.0.1:5000`
3. Open `/simulate` in a new tab to fire an emergency alert
4. Switch back to the dashboard
5. Watch the emergency alert appear, route get calculated, and the ambulance animate along the optimal path in real time

---

Note: This is a simulated academic project. It is not intended for real-world deployment. Emergency locations and ambulance positions are simulated for demonstration purposes.


