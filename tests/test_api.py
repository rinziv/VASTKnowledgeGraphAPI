"""
Comprehensive test suite for the NetworkX Graph API.

This test suite covers:
- Graph upload functionality
- Graph summary endpoint
- Node type counting
- Edge type counting
- Default graph functionality
- Health check endpoint
"""

import pytest
import networkx as nx
import json
import tempfile
import os
from pathlib import Path


class TestGraphUpload:
    """Test cases for graph upload functionality."""

    def test_upload_valid_graph(self, client, empty_registry, graph_storage_dir):
        """Test uploading a valid NetworkX graph."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3])
        G.add_edges_from([(1, 2), (2, 3)])

        data = nx.node_link_data(G)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_file = f.name

        try:
            with open(temp_file, 'rb') as f:
                response = client.post("/upload/", files={"file": f})

            assert response.status_code == 201
            assert "graph_id" in response.json()
            assert response.json()["message"] == "Graph uploaded successfully"

            graph_id = response.json()["graph_id"]
            graph_file = Path(graph_storage_dir) / f"{graph_id}.json"
            if os.path.exists(graph_file):
                graph_file.unlink()
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_upload_invalid_json(self, client):
        """Test uploading an invalid JSON file."""
        invalid_json = b"not valid json"

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            f.write(invalid_json)
            temp_file = f.name

        try:
            with open(temp_file, 'rb') as f:
                response = client.post("/upload/", files={"file": f})

            assert response.status_code == 400
            assert "Invalid JSON" in response.json()["detail"]
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_upload_non_json_file(self, client):
        """Test uploading a file without .json extension."""
        data = b"some data"

        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(data)
            temp_file = f.name

        try:
            with open(temp_file, 'rb') as f:
                response = client.post("/upload/", files={"file": f})

            assert response.status_code == 400
            assert "json extension" in response.json()["detail"]
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_upload_invalid_graph_format(self, client):
        """Test uploading a file with invalid NetworkX graph format."""
        invalid_graph = {"not": "a valid networkx graph"}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_graph, f)
            temp_file = f.name

        try:
            with open(temp_file, 'rb') as f:
                response = client.post("/upload/", files={"file": f})

            assert response.status_code == 400
            assert "Invalid NetworkX graph" in response.json()["detail"]
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestGraphSummary:
    """Test cases for graph summary endpoint."""

    def test_get_summary_for_uploaded_graph(self, client, uploaded_graph):
        """Test getting summary for an uploaded graph."""
        graph_id = uploaded_graph()
        response = client.get(f"/summary/{graph_id}")

        assert response.status_code == 200
        summary = response.json()

        assert summary["graph_id"] == graph_id
        assert "basic_properties" in summary
        assert "degree_properties" in summary
        assert "node_properties" in summary
        assert "edge_properties" in summary
        assert "edge_type_properties" in summary
        assert "node_type_properties" in summary

    def test_get_summary_for_nonexistent_graph(self, client):
        """Test getting summary for a non-existent graph."""
        response = client.get("/summary/nonexistent123")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_summary_basic_properties(self, client, uploaded_graph):
        """Test that basic properties are correctly calculated."""
        graph_id = uploaded_graph()
        response = client.get(f"/summary/{graph_id}")

        assert response.status_code == 200
        summary = response.json()

        basic = summary["basic_properties"]
        assert basic["number_of_nodes"] == 5
        assert basic["number_of_edges"] == 7
        assert basic["is_directed"] is True

    def test_summary_degree_properties(self, client, uploaded_graph):
        """Test that degree properties are correctly calculated."""
        graph_id = uploaded_graph()
        response = client.get(f"/summary/{graph_id}")

        assert response.status_code == 200
        summary = response.json()

        degree = summary["degree_properties"]
        assert "average_degree" in degree
        assert "degree_centrality_distribution" in degree
        assert degree["degree_centrality_distribution"]["stats"]["total_nodes"] == 5

    def test_summary_node_properties(self, client, uploaded_graph):
        """Test that node properties are correctly calculated."""
        graph_id = uploaded_graph()
        response = client.get(f"/summary/{graph_id}")

        assert response.status_code == 200
        summary = response.json()

        nodes = summary["node_properties"]
        assert nodes["node_count"] == 5
        assert "nodes_with_highest_degree" in nodes
        assert len(nodes["nodes_with_highest_degree"]) <= 5

    def test_summary_edge_properties(self, client, uploaded_graph):
        """Test that edge properties are correctly calculated."""
        graph_id = uploaded_graph()
        response = client.get(f"/summary/{graph_id}")

        assert response.status_code == 200
        summary = response.json()

        edges = summary["edge_properties"]
        assert edges["edge_count"] == 7
        assert "edges_with_highest_weight" in edges

    def test_summary_edge_types(self, client, uploaded_graph):
        """Test that edge types are correctly counted."""
        graph_id = uploaded_graph()
        response = client.get(f"/summary/{graph_id}")

        assert response.status_code == 200
        summary = response.json()

        edge_types = summary["edge_type_properties"]["edge_type_counts"]
        assert edge_types["Friendship"] == 2
        assert edge_types["Follows"] == 3
        assert edge_types["Family"] == 2

    def test_summary_node_types(self, client, uploaded_graph):
        """Test that node types are correctly counted."""
        graph_id = uploaded_graph()
        response = client.get(f"/summary/{graph_id}")

        assert response.status_code == 200
        summary = response.json()

        # The sample graph doesn't have node types, so should be 'Unknown'
        node_types = summary["node_type_properties"]["node_type_counts"]
        assert "Unknown" in node_types


class TestNodeTypes:
    """Test cases for node type counting endpoint."""

    def test_get_node_types_for_uploaded_graph(self, client, uploaded_graph):
        """Test getting node types for an uploaded graph."""
        graph_id = uploaded_graph()
        response = client.get(f"/node-types/{graph_id}")

        assert response.status_code == 200
        result = response.json()

        assert result["graph_id"] == graph_id
        assert "node_type_counts" in result
        assert "total_nodes" in result

    def test_get_node_types_with_actual_types(self, client, sample_graph_with_node_types, uploaded_graph):
        """Test node type counting with a graph that has node types."""
        data = nx.node_link_data(sample_graph_with_node_types)
        graph_id = uploaded_graph(data)
        response = client.get(f"/node-types/{graph_id}")
        assert response.status_code == 200

        result = response.json()
        assert result["node_type_counts"]["User"] == 2
        assert result["node_type_counts"]["Admin"] == 1
        assert result["node_type_counts"]["Service"] == 2
        assert result["total_nodes"] == 5

    def test_get_node_types_for_nonexistent_graph(self, client):
        """Test getting node types for a non-existent graph."""
        response = client.get("/node-types/nonexistent123")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestEdgeTypes:
    """Test cases for edge type counting endpoint."""

    def test_get_edge_types_for_uploaded_graph(self, client, uploaded_graph):
        """Test getting edge types for an uploaded graph."""
        graph_id = uploaded_graph()
        response = client.get(f"/edge-types/{graph_id}")

        assert response.status_code == 200
        result = response.json()

        assert result["graph_id"] == graph_id
        assert "edge_type_counts" in result
        assert "total_edges" in result

    def test_get_edge_types_with_actual_types(self, client, sample_graph, uploaded_graph):
        """Test edge type counting with a graph that has edge types."""
        data = nx.node_link_data(sample_graph)
        graph_id = uploaded_graph(data)
        response = client.get(f"/edge-types/{graph_id}")
        assert response.status_code == 200

        result = response.json()
        assert result["edge_type_counts"]["Friendship"] == 2
        assert result["edge_type_counts"]["Follows"] == 3
        assert result["edge_type_counts"]["Family"] == 2
        assert result["total_edges"] == 7

    def test_get_edge_types_for_nonexistent_graph(self, client):
        """Test getting edge types for a non-existent graph."""
        response = client.get("/edge-types/nonexistent123")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_edge_types_in_summary(self, client, uploaded_graph):
        """Test that edge types are included in summary endpoint."""
        graph_id = uploaded_graph()
        response = client.get(f"/summary/{graph_id}")

        assert response.status_code == 200
        summary = response.json()

        assert "edge_type_properties" in summary
        assert "edge_type_counts" in summary["edge_type_properties"]


class TestDefaultGraph:
    """Test cases for default graph functionality."""

    def test_set_default_graph(self, client, uploaded_graph):
        """Test setting a graph as default."""
        graph_id = uploaded_graph()
        response = client.post(f"/set-default/{graph_id}")

        assert response.status_code == 200
        assert response.json()["message"] == "Graph set as default successfully"

    def test_set_default_with_nonexistent_graph(self, client):
        """Test setting a non-existent graph as default."""
        response = client.post("/set-default/nonexistent123")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_access_default_graph_summary(self, client, default_graph):
        """Test accessing summary for default graph."""
        response = client.get("/summary/default")

        assert response.status_code == 200
        summary = response.json()

        assert "graph_id" in summary
        assert "basic_properties" in summary

    def test_access_default_graph_node_types(self, client, default_graph):
        """Test accessing node types for default graph."""
        response = client.get("/node-types/default")

        assert response.status_code == 200
        result = response.json()

        assert "node_type_counts" in result

    def test_access_default_graph_edge_types(self, client, default_graph):
        """Test accessing edge types for default graph."""
        response = client.get("/edge-types/default")

        assert response.status_code == 200
        result = response.json()

        assert "edge_type_counts" in result


class TestHealthCheck:
    """Test cases for health check endpoint."""

    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/health/")

        assert response.status_code == 200
        result = response.json()

        assert result["status"] == "healthy"
        assert "graph_count" in result


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_graph(self, client, uploaded_graph):
        """Test uploading and analyzing an empty graph."""
        G = nx.Graph()
        data = nx.node_link_data(G)
        graph_id = uploaded_graph(data)

        # Test summary
        response = client.get(f"/summary/{graph_id}")
        assert response.status_code == 200
        summary = response.json()
        assert summary["basic_properties"]["number_of_nodes"] == 0
        assert summary["basic_properties"]["number_of_edges"] == 0

        # Test node types
        response = client.get(f"/node-types/{graph_id}")
        assert response.status_code == 200
        result = response.json()
        assert result["total_nodes"] == 0

        # Test edge types
        response = client.get(f"/edge-types/{graph_id}")
        assert response.status_code == 200
        result = response.json()
        assert result["total_edges"] == 0

    def test_graph_with_no_edge_types(self, client, uploaded_graph):
        """Test a graph where edges don't have Edge Type attribute."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4])
        G.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 1)])

        data = nx.node_link_data(G)

        graph_id = uploaded_graph(data)
        response = client.get(f"/edge-types/{graph_id}")
        assert response.status_code == 200
        result = response.json()
        assert result["edge_type_counts"]["Unknown"] == 4

    def test_graph_with_no_node_types(self, client, uploaded_graph):
        """Test a graph where nodes don't have Node Type attribute."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4])
        G.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 1)])

        data = nx.node_link_data(G)

        graph_id = uploaded_graph(data)

        response = client.get(f"/node-types/{graph_id}")
        assert response.status_code == 200
        result = response.json()
        assert result["node_type_counts"]["Unknown"] == 4

    def test_undirected_graph(self, client, uploaded_graph):
        """Test with an undirected graph."""
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4])
        G.add_edges_from([(1, 2, {'weight': 1.0}), (2, 3, {'weight': 2.0}), (3, 4, {'weight': 1.5})])

        data = nx.node_link_data(G)

        graph_id = uploaded_graph(data)

        response = client.get(f"/summary/{graph_id}")
        assert response.status_code == 200
        summary = response.json()
        assert summary["basic_properties"]["is_directed"] is False



class TestComprehensive:
    """Comprehensive integration tests."""

    def test_full_workflow(self, client, empty_registry, graph_storage_dir):
        """Test a complete workflow from upload to analysis."""
        # 1. Upload a graph
        G = nx.DiGraph()
        G.add_nodes_from([
            (1, {'Node Type': 'User'}),
            (2, {'Node Type': 'User'}),
            (3, {'Node Type': 'Admin'}),
            (4, {'Node Type': 'Service'}),
            (5, {'Node Type': 'Service'})
        ])
        G.add_edges_from([
            (1, 2, {'weight': 2.5, 'Edge Type': 'Friendship'}),
            (1, 3, {'weight': 1.0, 'Edge Type': 'Friendship'}),
            (2, 3, {'weight': 0.5, 'Edge Type': 'Follows'}),
            (2, 4, {'weight': 1.5, 'Edge Type': 'Follows'}),
            (3, 4, {'weight': 3.0, 'Edge Type': 'Follows'}),
            (4, 5, {'weight': 2.0, 'Edge Type': 'Family'}),
            (5, 1, {'weight': 1.0, 'Edge Type': 'Family'})
        ])

        data = nx.node_link_data(G)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_file = f.name

        try:
            with open(temp_file, 'rb') as f:
                upload_response = client.post("/upload/", files={"file": f})

            assert upload_response.status_code == 201
            graph_id = upload_response.json()["graph_id"]

            # 2. Get summary
            response = client.get(f"/summary/{graph_id}")
            assert response.status_code == 200
            summary = response.json()
            assert summary["basic_properties"]["number_of_nodes"] == 5
            assert summary["basic_properties"]["number_of_edges"] == 7

            # 3. Get node types
            response = client.get(f"/node-types/{graph_id}")
            assert response.status_code == 200
            result = response.json()
            assert result["node_type_counts"]["User"] == 2
            assert result["node_type_counts"]["Admin"] == 1
            assert result["node_type_counts"]["Service"] == 2

            # 4. Get edge types
            response = client.get(f"/edge-types/{graph_id}")
            assert response.status_code == 200
            result = response.json()
            assert result["edge_type_counts"]["Friendship"] == 2
            assert result["edge_type_counts"]["Follows"] == 3
            assert result["edge_type_counts"]["Family"] == 2

            # 5. Set as default
            response = client.post(f"/set-default/{graph_id}")
            assert response.status_code == 200

            # 6. Access via default
            response = client.get("/summary/default")
            assert response.status_code == 200
            assert response.json()["basic_properties"]["number_of_nodes"] == 5

            response = client.get("/node-types/default")
            assert response.status_code == 200
            assert response.json()["node_type_counts"]["User"] == 2

            response = client.get("/edge-types/default")
            assert response.status_code == 200
            assert response.json()["edge_type_counts"]["Friendship"] == 2

            graph_file = Path(graph_storage_dir) / f'{graph_id}.json'
            if os.path.exists(graph_file):
                graph_file.unlink()

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
