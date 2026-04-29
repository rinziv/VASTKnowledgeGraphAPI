"""
Comprehensive test for edge type counting functionality.
"""

import networkx as nx
import json
import tempfile
import os
import sys

# Add the parent directory to the path
sys.path.insert(0, '.')

from main import app, graph_registry
from fastapi.testclient import TestClient

def test_edge_type_comprehensive():
    """Comprehensive test for edge type counting."""
    client = TestClient(app)

    print("Comprehensive Edge Type Testing")
    print("=" * 60)

    # Test 1: Graph with no edge types (all edges should be 'Unknown')
    print("\n1. Testing graph with no edge types...")
    graph1 = nx.Graph()
    graph1.add_nodes_from([1, 2, 3, 4])
    graph1.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 1)])

    data1 = nx.node_link_data(graph1)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data1, f)
        temp_file1 = f.name

    try:
        with open(temp_file1, 'rb') as f:
            response = client.post("/upload/", files={"file": f})

        assert response.status_code == 201
        graph_id1 = response.json()["graph_id"]

        response = client.get(f"/edge-types/{graph_id1}")
        assert response.status_code == 200
        result = response.json()
        assert result["total_edges"] == 4
        assert "Unknown" in result["edge_type_counts"]
        assert result["edge_type_counts"]["Unknown"] == 4
        print("   ✓ All edges correctly marked as 'Unknown'")
    finally:
        if os.path.exists(temp_file1):
            os.unlink(temp_file1)

    # Test 2: Graph with mixed edge types
    print("\n2. Testing graph with mixed edge types...")
    graph2 = nx.DiGraph()
    graph2.add_nodes_from([1, 2, 3, 4, 5])
    graph2.add_edges_from([
        (1, 2, {"Edge Type": "Friendship"}),
        (2, 3, {"Edge Type": "Friendship"}),
        (3, 4, {"Edge Type": "Follows"}),
        (4, 5, {"Edge Type": "Follows"}),
        (5, 1, {"Edge Type": "Follows"}),
        (1, 3, {"Edge Type": "Family"}),
        (1, 4, {"Edge Type": "Work"})
    ])

    data2 = nx.node_link_data(graph2)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data2, f)
        temp_file2 = f.name

    try:
        with open(temp_file2, 'rb') as f:
            response = client.post("/upload/", files={"file": f})

        assert response.status_code == 201
        graph_id2 = response.json()["graph_id"]

        response = client.get(f"/edge-types/{graph_id2}")
        assert response.status_code == 200
        result = response.json()
        assert result["total_edges"] == 7
        assert result["edge_type_counts"]["Friendship"] == 2
        assert result["edge_type_counts"]["Follows"] == 3
        assert result["edge_type_counts"]["Family"] == 1
        assert result["edge_type_counts"]["Work"] == 1
        print("   ✓ Edge types correctly counted")
        print(f"      Friendship: 2, Follows: 3, Family: 1, Work: 1")
    finally:
        if os.path.exists(temp_file2):
            os.unlink(temp_file2)

    # Test 3: Empty graph
    print("\n3. Testing empty graph...")
    graph3 = nx.Graph()
    data3 = nx.node_link_data(graph3)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data3, f)
        temp_file3 = f.name

    try:
        with open(temp_file3, 'rb') as f:
            response = client.post("/upload/", files={"file": f})

        assert response.status_code == 201
        graph_id3 = response.json()["graph_id"]

        response = client.get(f"/edge-types/{graph_id3}")
        assert response.status_code == 200
        result = response.json()
        assert result["total_edges"] == 0
        assert len(result["edge_type_counts"]) == 0
        print("   ✓ Empty graph handled correctly")
    finally:
        if os.path.exists(temp_file3):
            os.unlink(temp_file3)

    # Test 4: Verify edge types in summary endpoint
    print("\n4. Testing edge types in summary endpoint...")
    response = client.get(f"/summary/{graph_id2}")
    assert response.status_code == 200
    summary = response.json()
    assert "edge_type_properties" in summary
    assert "edge_type_counts" in summary["edge_type_properties"]
    assert summary["edge_type_properties"]["edge_type_counts"]["Friendship"] == 2
    assert summary["edge_type_properties"]["edge_type_counts"]["Follows"] == 3
    print("   ✓ Edge types correctly included in summary")

    # Test 5: Test with default graph
    print("\n5. Testing with default graph...")
    # Set graph_id2 as default
    response = client.post(f"/set-default/{graph_id2}")
    assert response.status_code == 200

    response = client.get("/edge-types/default")
    assert response.status_code == 200
    result = response.json()
    assert result["total_edges"] == 7
    assert result["edge_type_counts"]["Friendship"] == 2
    print("   ✓ Default graph endpoint works correctly")

    print("\n" + "=" * 60)
    print("ALL COMPREHENSIVE TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    test_edge_type_comprehensive()
