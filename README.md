# RapidRoute — AI Ambulance Navigation

An AI-powered emergency ambulance dispatch system that uses the A* Search Algorithm on real road networks to find the optimal route from an ambulance to a patient in the shortest possible time.

---

## Overview

Emergency response time is critical in saving lives. RapidRoute is a hospital-side web application that receives emergency alerts, identifies the nearest available ambulance within a 10km radius, and computes the fastest road route using a custom implementation of the A* pathfinding algorithm on real Chennai road data.

---

## Features

- Real-time emergency alert system using WebSockets
- Nearest ambulance detection within a 10km radius using the Haversine formula
- Custom A* algorithm implementation on real OpenStreetMap road network
- Live route visualization on an interactive map
- Hospital dispatch dashboard with ambulance fleet status

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask, Flask-SocketIO |
| Algorithm | A* Search (custom implementation) |
| Map Data | OpenStreetMap via OSMnx |
| Frontend | HTML, CSS, JavaScript |
| Real-time | WebSockets |
| Map Rendering | Folium |

---

## How It Works

1. The hospital receives an emergency alert with the patient's location
2. The system uses the Haversine formula to find the nearest available ambulance within 10km
3. The A* algorithm runs on Chennai's real road network to compute the optimal path
4. The route is displayed on a live map showing the ambulance location, patient location, and the exact road path

---

## Algorithm

The A* algorithm is implemented from scratch in `astar.py`. It uses:

- `g(n)` — actual road distance travelled from the start node
- `h(n)` — straight-line heuristic distance from the current node to the goal
- `f(n) = g(n) + h(n)` — total estimated cost used to prioritize exploration

This makes A* significantly faster than Dijkstra or BFS on large road networks by always exploring the most promising path first.

---

## Project Structure

```
ambulance-app/
│
├── backend/
│   ├── app.py           # Flask server and API routes
│   ├── astar.py         # A* algorithm implementation
│   └── map_loader.py    # OSMnx Chennai road network loader
│
├── frontend/
│   ├── index.html       # Hospital dashboard UI
│   ├── style.css        # Styling
│   └── script.js        # Real-time alert handling and map display
│
└── maps/
    └── chennai.graphml  # Saved Chennai road network (auto-generated)
```

---

## Setup and Installation

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the server

```bash
cd backend
python app.py
```

### 3. Open the dashboard

```
http://127.0.0.1:5000
```

### 4. Simulate an emergency alert

```
http://127.0.0.1:5000/simulate
```

---

## Team

| Name | Register Number |
|---|---|
| Suraj | RA2411033010150 |
| Sarang Marath Sabu | RA2411033010156 |
| Manu Prasath | RA2411033010162 |

---

## Institution

SRM Institute of Science and Technology  
Department of CINTEL — Computer Science with Software Engineering  
Semester 4 — Artificial Intelligence Project
