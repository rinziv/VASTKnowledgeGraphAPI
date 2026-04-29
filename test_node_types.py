"""
Test script to verify the node type counting endpoint.
"""

import requests
import json

def test_node_type_endpoint():
    """Test the node type counting endpoint."""
    base_url = "http://localhost:8000"

    print("Testing Node Type Counting Endpoint")
    print("=" * 50)

    # Test 1: Get node types for default graph
    print("\n1. Testing node type counts for default graph...")
    try:
        response = requests.get(f"{base_url}/node-types/default")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Graph ID: {result['graph_id']}")
            print(f"   Total Nodes: {result['total_nodes']}")
            print(f"   Node Type Counts:")
            for node_type, count in sorted(result['node_type_counts'].items(), key=lambda x: x[1], reverse=True):
                print(f"      {node_type}: {count}")

    except Exception as e:
        print(f"   Error: {e}")

    # Test 2: Get node types for a specific graph ID
    print("\n2. Testing node type counts for a specific graph ID...")
    try:
        # First, upload a simple graph
        sample_graph = {
            "directed": True,
            "multigraph": False,
            "graph": {},
            "nodes": [
                {"id": 1, "Node Type": "User"},
                {"id": 2, "Node Type": "User"},
                {"id": 3, "Node Type": "Admin"},
                {"id": 4, "Node Type": "Service"},
                {"id": 5, "Node Type": "Service"}
            ],
            "links": [
                {"source": 1, "target": 2, "weight": 1.0},
                {"source": 2, "target": 3, "weight": 2.0},
                {"source": 3, "target": 4, "weight": 1.5},
                {"source": 4, "target": 5, "weight": 2.5},
                {"source": 5, "target": 1, "weight": 1.0}
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

                # Now test the node type endpoint with this graph
                response = requests.get(f"{base_url}/node-types/{graph_id}")
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"   Graph ID: {result['graph_id']}")
                    print(f"   Total Nodes: {result['total_nodes']}")
                    print(f"   Node Type Counts:")
                    for node_type, count in sorted(result['node_type_counts'].items()):
                        print(f"      {node_type}: {count}")
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    except Exception as e:
        print(f"   Error: {e}")

    # Test 3: Also check that node types are included in summary
    print("\n3. Testing that node types are included in summary endpoint...")
    try:
        response = requests.get(f"{base_url}/summary/default")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            summary = response.json()
            if 'node_type_properties' in summary:
                print(f"   Node type properties found in summary!")
                print(f"   Node Type Counts:")
                for node_type, count in sorted(summary['node_type_properties']['node_type_counts'].items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"      {node_type}: {count}")
                print(f"      ... and {len(summary['node_type_properties']['node_type_counts'])-5} more types")
            else:
                print(f"   Warning: node_type_properties not found in summary")

    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_node_type_endpoint()
