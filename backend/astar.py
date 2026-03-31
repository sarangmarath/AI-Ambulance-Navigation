import heapq
import math

def heuristic(G, node1, node2):
    # Straight line distance between two nodes (lat/lon)
    x1, y1 = G.nodes[node1]['x'], G.nodes[node1]['y']
    x2, y2 = G.nodes[node2]['x'], G.nodes[node2]['y']
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def astar(G, start, goal):
    # Priority queue: (f_score, node)
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

        # Reached the goal!
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path, g_score[goal]

        # Explore neighbors
        for neighbor in G.neighbors(current):
            if neighbor in visited:
                continue

            edge_data = G[current][neighbor][0]
            road_length = edge_data.get('length', 1)
            tentative_g = g_score[current] + road_length

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic(G, neighbor, goal)
                heapq.heappush(open_set, (f_score, neighbor))

    return None, float('inf')  # No path found
