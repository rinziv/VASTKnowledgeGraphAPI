"""
Test script to demonstrate how to use the NetworkX Graph API.

This script creates a sample NetworkX graph, saves it as JSON,
and then demonstrates how to interact with the API endpoints.
"""

import networkx as nx
import json
import requests

# Create a sample graph
def create_sample_graph():
    """Create a sample directed graph for testing."""
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
    """Save NetworkX graph as JSON file."""
    data = nx.node_link_data(graph)
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Graph saved to {filename}")
    return filename


def test_api_endpoints():
    """Test the API endpoints."""
    base_url = "http://localhost:8000"

    # Create and save sample graph
    graph = create_sample_graph()
    filename = save_graph_as_json(graph)

    print("\n" + "="*50)
    print("Testing API Endpoints")
    print("="*50)

    # Test 1: Health check
    print("\n1. Testing health check endpoint...")
    try:
        response = requests.get(f"{base_url}/health/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 2: Upload graph
    print("\n2. Testing graph upload endpoint...")
    try:
        with open(filename, 'rb') as f:
            files = {'file': (filename, f, 'application/json')}
            response = requests.post(f"{base_url}/upload/", files=files)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")

            if response.status_code == 201:
                graph_id = response.json()["graph_id"]
                print(f"   Graph ID: {graph_id}")

                # Test 3: Get graph summary
                print("\n3. Testing graph summary endpoint...")
                response = requests.get(f"{base_url}/summary/{graph_id}")
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    summary = response.json()
                    print(f"   Graph ID: {summary['graph_id']}")
                    print(f"   Nodes: {summary['basic_properties']['number_of_nodes']}")
                    print(f"   Edges: {summary['basic_properties']['number_of_edges']}")
                    print(f"   Directed: {summary['basic_properties']['is_directed']}")
                    print(f"   Average Degree: {summary['degree_properties']['average_degree']:.2f}")
                    print(f"   Top 3 nodes by degree: {summary['node_properties']['nodes_with_highest_degree'][:3]}")
    except Exception as e:
        print(f"   Error: {e}")


if __name__ == "__main__":
    test_api_endpoints()
