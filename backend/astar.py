import heapq
import math
import pickle
import os
import warnings
import pandas as pd
from datetime import datetime

warnings.filterwarnings('ignore')

# ── Load ML model and encoder ──────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, 'traffic_model.pkl'), 'rb') as f:
    traffic_model = pickle.load(f)

with open(os.path.join(BASE_DIR, 'road_type_encoder.pkl'), 'rb') as f:
    road_type_encoder = pickle.load(f)

KNOWN_ROAD_TYPES = list(road_type_encoder.classes_)
print(" ML traffic model loaded!")

def precompute_traffic_weights(G):
    """Pre-compute ML congestion score for every edge ONCE at startup"""
    print(" Pre-computing traffic weights using ML model...")

    now = datetime.now()
    hour = now.hour
    day_of_week = now.weekday()
    is_weekend = 1 if day_of_week >= 5 else 0
    month = now.month
    is_monsoon = 1 if month in [6, 7, 8, 9, 10, 11] else 0

    edge_keys = []
    edge_features = []

    for u, v, data in G.edges(data=True):
        road_length = data.get('length', 100)
        road_type = data.get('highway', 'residential')
        if isinstance(road_type, list):
            road_type = road_type[0]
        if road_type not in KNOWN_ROAD_TYPES:
            road_type = 'residential'
        road_type_encoded = road_type_encoder.transform([road_type])[0]

        edge_keys.append((u, v))
        edge_features.append([
            hour, day_of_week, is_weekend, month,
            is_monsoon, road_type_encoded, road_length
        ])

    # Batch predict all edges at once
    features_df = pd.DataFrame(edge_features, columns=[
        'hour', 'day_of_week', 'is_weekend', 'month',
        'is_monsoon', 'road_type_encoded', 'road_length_m'
    ])
    scores = traffic_model.predict(features_df)

    # Build lookup dictionary
    weights = {}
    for (u, v), score, feat in zip(edge_keys, scores, edge_features):
        road_length = feat[6]
        congestion = round(max(0.1, min(1.0, score)), 3)
        weights[(u, v)] = road_length * (1 + congestion)

    print(f" Traffic weights computed for {len(weights)} road edges!")
    return weights

def heuristic(G, node1, node2):
    """Straight line GPS distance — h(n) in A*"""
    x1, y1 = G.nodes[node1]['x'], G.nodes[node1]['y']
    x2, y2 = G.nodes[node2]['x'], G.nodes[node2]['y']
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def astar(G, start, goal, traffic_weights):
    """
    A* Search Algorithm with ML traffic-aware edge weights
    g(n) = pre-computed traffic weight of road
    h(n) = straight line GPS distance to goal
    f(n) = g(n) + h(n)
    """
    open_set = []
    heapq.heappush(open_set, (0, start))

    came_from = {}
    g_score = {start: 0}
    visited = set()

    while open_set:
        _, current = heapq.heappop(open_set)

        if current in visited:
            continue
        visited.add(current)

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path, g_score[goal]

        for neighbor in G.neighbors(current):
            if neighbor in visited:
                continue

            weight = traffic_weights.get((current, neighbor), 100)
            tentative_g = g_score[current] + weight

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic(G, neighbor, goal)
                heapq.heappush(open_set, (f_score, neighbor))

    return None, float('inf')
