"""
Test script to verify the edge type counting endpoint.
"""

import requests
import json

def test_edge_type_endpoint():
    """Test the edge type counting endpoint."""
    base_url = "http://localhost:8000"

    print("Testing Edge Type Counting Endpoint")
    print("=" * 50)

    # Test 1: Get edge types for default graph
    print("\n1. Testing edge type counts for default graph...")
    try:
        response = requests.get(f"{base_url}/edge-types/default")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Graph ID: {result['graph_id']}")
            print(f"   Total Edges: {result['total_edges']}")
            print(f"   Edge Type Counts:")
            for edge_type, count in sorted(result['edge_type_counts'].items(), key=lambda x: x[1], reverse=True):
                print(f"      {edge_type}: {count}")

    except Exception as e:
        print(f"   Error: {e}")

    # Test 2: Get edge types for a specific graph ID
    print("\n2. Testing edge type counts for a specific graph ID...")
    try:
        # First, upload a simple graph
        sample_graph = {
            "directed": True,
            "multigraph": False,
            "graph": {},
            "nodes": [
                {"id": 1},
                {"id": 2},
                {"id": 3},
                {"id": 4},
                {"id": 5}
            ],
            "links": [
                {"source": 1, "target": 2, "Edge Type": "Friendship", "weight": 1.0},
                {"source": 2, "target": 3, "Edge Type": "Friendship", "weight": 2.0},
                {"source": 3, "target": 4, "Edge Type": "Follows", "weight": 1.5},
                {"source": 4, "target": 5, "Edge Type": "Follows", "weight": 2.5},
                {"source": 5, "target": 1, "Edge Type": "Follows", "weight": 1.0},
                {"source": 1, "target": 3, "Edge Type": "Family", "weight": 3.0}
            ]
        }

        # Save to temp file and upload
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_graph, f)
            temp_file = f.name

        try:
            with open(temp_file, 'rb') as f:
                files = {'file': (temp_file, f, 'application/json')}
                upload_response = requests.post(f"{base_url}/upload/", files=files)

            if upload_response.status_code == 201:
                graph_id = upload_response.json()["graph_id"]
                print(f"   Uploaded graph with ID: {graph_id}")

                # Now test the edge type endpoint with this graph
                response = requests.get(f"{base_url}/edge-types/{graph_id}")
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"   Graph ID: {result['graph_id']}")
                    print(f"   Total Edges: {result['total_edges']}")
                    print(f"   Edge Type Counts:")
                    for edge_type, count in sorted(result['edge_type_counts'].items()):
                        print(f"      {edge_type}: {count}")
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    except Exception as e:
        print(f"   Error: {e}")

    # Test 3: Also check that edge types are included in summary
    print("\n3. Testing that edge types are included in summary endpoint...")
    try:
        response = requests.get(f"{base_url}/summary/default")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            summary = response.json()
            if 'edge_type_properties' in summary:
                print(f"   Edge type properties found in summary!")
                print(f"   Edge Type Counts:")
                for edge_type, count in sorted(summary['edge_type_properties']['edge_type_counts'].items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"      {edge_type}: {count}")
                print(f"      ... and {len(summary['edge_type_properties']['edge_type_counts'])-5} more types")
            else:
                print(f"   Warning: edge_type_properties not found in summary")

    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_edge_type_endpoint()
