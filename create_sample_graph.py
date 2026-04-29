"""
Example script showing how to create a NetworkX graph and save it as JSON
for use with the API.
"""

import networkx as nx
import json

# Create a sample directed graph
def create_sample_graph():
    """Create a sample directed graph."""
    G = nx.DiGraph()

    # Add nodes
    G.add_nodes_from([1, 2, 3, 4, 5])

    # Add edges with weights
    G.add_edges_from([(1, 2, {'weight': 2.5}),
                      (1, 3, {'weight': 1.0}),
                      (2, 3, {'weight': 0.5}),
                      (2, 4, {'weight': 1.5}),
                      (3, 4, {'weight': 3.0}),
                      (4, 5, {'weight': 2.0}),
                      (5, 1, {'weight': 1.0})])

    return G


def save_graph_as_json(graph, filename="sample_graph.json"):
    """Save NetworkX graph as JSON file in node-link format."""
    data = nx.node_link_data(graph)
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Graph saved to {filename}")
    return filename


if __name__ == "__main__":
    # Create and save a sample graph
    graph = create_sample_graph()
    filename = save_graph_as_json(graph)

    # Print some info about the graph
    print(f"Graph created with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")
    print(f"Graph is directed: {nx.is_directed(graph)}")
    print(f"Graph is strongly connected: {nx.is_strongly_connected(graph)}")
