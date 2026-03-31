import osmnx as ox
import os

def load_chennai_map():
    map_path = os.path.join("..", "maps", "chennai.graphml")
    
    if os.path.exists(map_path):
        print(" Loading Chennai map from saved file...")
        G = ox.load_graphml(map_path)
    else:
        print(" Downloading Chennai road network... (first time only, takes ~1 min)")
        G = ox.graph_from_bbox(
    north=13.05,
    south=13.00,
    east=80.25,
    west=80.20,
    network_type="drive"
)
        ox.save_graphml(G, map_path)
        print(" Chennai map saved!")
    
    return G

def get_nearest_node(G, lat, lon):
    return ox.distance.nearest_nodes(G, lon, lat)

# ADD THIS AT THE BOTTOM 
if __name__ == "__main__":
    G = load_chennai_map()
    print(f" Map loaded! Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")