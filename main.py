"""
FastAPI application for handling NetworkX graphs.

This application provides endpoints for:
- Uploading JSON files containing NetworkX graphs
- Retrieving graph summaries by unique ID
- Setting a default graph that can be accessed without uploading a file
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import networkx as nx
import json
import os
import uuid
from typing import Dict, Any
from pathlib import Path
import logging
from anyio import open_file


# Log to uvicorn general-purpose server logger
logger = logging.getLogger('uvicorn.error')


app = FastAPI(
    title="NetworkX Graph API",
    description="API for uploading and analyzing NetworkX graphs",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:5173", "http://127.0.0.1", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to store uploaded graph files
GRAPH_STORAGE_DIR = "graph_storage"

# Create storage directory if it doesn't exist
Path(GRAPH_STORAGE_DIR).mkdir(exist_ok=True)

# Dictionary to map graph IDs to file paths
# In production, this would be a database
graph_registry: Dict[str, str] = {}

# Default graph ID - special constant to access the default graph
default_graph_id = "default"


def create_degree_centrality_distribution(graph):
    """
    Create a distribution of degree centrality values instead of per-node values.
    This is more compact and suitable for large graphs.
    Uses adaptive binning based on actual degree centrality values.

    Returns:
        A dictionary with bins of degree centrality values and their counts.
    """
    degree_centrality_values = list(nx.degree_centrality(graph).values())

    if not degree_centrality_values:
        return {
            "stats": {
                "min": 0,
                "max": 0,
                "mean": 0,
                "median": 0,
                "total_nodes": 0
            }
        }

    # Get min and max values
    min_val = min(degree_centrality_values)
    max_val = max(degree_centrality_values)

    # Use adaptive binning based on actual values
    # Create 10 bins that cover the actual range of values
    if min_val == max_val:
        # All values are the same, just use one bin
        bins = [min_val, min_val]
    else:
        # Create 10 evenly spaced bins covering the actual range
        bins = [min_val + i * (max_val - min_val) / 10 for i in range(11)]

    distribution = {}

    for i in range(len(bins) - 1):
        lower = bins[i]
        upper = bins[i + 1]
        bin_key = f"{lower:.4f}-{upper:.4f}"
        count = sum(1 for value in degree_centrality_values if lower <= value < upper)
        distribution[bin_key] = count

    # Add statistics about the distribution
    distribution["stats"] = {
        "min": min_val,
        "max": max_val,
        "mean": sum(degree_centrality_values) / len(degree_centrality_values),
        "median": sorted(degree_centrality_values)[len(degree_centrality_values) // 2],
        "total_nodes": len(degree_centrality_values)
    }

    return distribution


@app.post("/upload/", summary="Upload a NetworkX graph JSON file")
async def upload_graph(file: UploadFile = File(...)):
    """
    Upload a JSON file containing a NetworkX graph.

    The file should contain a NetworkX graph in JSON format (e.g., from nx.readwrite.json_graph.node_link_data).

    Returns:
        A unique ID that can be used to reference this graph in other endpoints.
    """
    # Check if file has .json extension
    if not file.filename.lower().endswith('.json'):
        raise HTTPException(status_code=400, detail="File must have .json extension")

    try:
        # Read the file content
        contents = await file.read()
        data = json.loads(contents)

        # Validate that it's a NetworkX graph by trying to load it
        try:
            graph = nx.node_link_graph(data)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid NetworkX graph format: {str(e)}"
            )

        # Generate a unique ID for this graph
        graph_id = str(uuid.uuid4())

        # Save the file with the graph ID as filename
        file_path = os.path.join(GRAPH_STORAGE_DIR, f"{graph_id}.json")
        with open(file_path, 'w') as f:
            json.dump(data, f)

        # Register the graph
        graph_registry[graph_id] = file_path

        return JSONResponse(
            status_code=201,
            content={
                "graph_id": graph_id,
                "message": "Graph uploaded successfully",
                "filename": file.filename
            }
        )

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@app.post("/set-default/{graph_id}", summary="Set a graph as the default graph")
async def set_default_graph(graph_id: str):
    """
    Set a graph as the default graph that can be accessed without uploading a file.

    Args:
        graph_id: The unique ID of the graph to set as default, or the filename in graph_storage (without .json extension).

    Returns:
        Confirmation that the graph is now the default.
    """
    # Check if graph ID exists in registry
    if graph_id in graph_registry:
        # Graph ID found in registry, use it
        file_path = graph_registry[graph_id]
    else:
        # Graph ID not in registry, check if it's a file in graph_storage
        # Try with .json extension first
        file_path = os.path.join(GRAPH_STORAGE_DIR, f"{graph_id}.json")
        if not os.path.exists(file_path):
            # Also try without extension (for backward compatibility)
            file_path = os.path.join(GRAPH_STORAGE_DIR, graph_id)
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="Graph ID not found in registry or storage")

        # Add to registry for future reference
        graph_registry[graph_id] = file_path

    # Set this graph as the default
    graph_registry[default_graph_id] = file_path

    return JSONResponse(
        status_code=200,
        content={
            "message": "Graph set as default successfully",
            "default_graph_id": default_graph_id,
            "graph_id": graph_id
        }
    )


@app.get("/summary/{graph_id}", summary="Get graph summary by ID")
async def get_graph_summary(graph_id: str):
    """
    Get a summary of the properties of a NetworkX graph.

    Args:
        graph_id: The unique ID returned when uploading the graph, or "default" to access the default graph.

    Returns:
        A JSON object containing various properties of the graph.
    """
    # Check if graph ID exists in registry
    if graph_id not in graph_registry:
        raise HTTPException(status_code=404, detail="Graph ID not found")

    try:
        # Load the graph from file
        file_path = graph_registry[graph_id]
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Load as NetworkX graph
        graph = nx.node_link_graph(data)

        # Calculate graph properties
        summary = {
            "graph_id": graph_id,
            "basic_properties": {
                "number_of_nodes": graph.number_of_nodes(),
                "number_of_edges": graph.number_of_edges(),
                "is_directed": nx.is_directed(graph),
                "is_weakly_connected": nx.is_weakly_connected(graph) if (nx.is_directed(graph) and graph.number_of_nodes() > 0) else None,
                "is_strongly_connected": nx.is_strongly_connected(graph) if (nx.is_directed(graph) and graph.number_of_nodes() > 0) else None,
                "is_connected": nx.is_connected(graph) if (not nx.is_directed(graph) and graph.number_of_nodes() > 0) else None,
            },
            "degree_properties": {
                "average_degree": sum(dict(graph.degree()).values()) / graph.number_of_nodes() if graph.number_of_nodes() > 0 else 0,
                "degree_centrality_distribution": create_degree_centrality_distribution(graph) if graph.number_of_nodes() > 0 else {},
            },
            "node_properties": {
                "node_count": graph.number_of_nodes(),
                "nodes_with_highest_degree": sorted(
                    graph.degree(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]  # Top 5 nodes by degree
            },
            "edge_properties": {
                "edge_count": graph.number_of_edges(),
                "edges_with_highest_weight": sorted(
                    graph.edges(data='weight', default=1),
                    key=lambda x: x[2],
                    reverse=True
                )[:5]  # Top 5 edges by weight (if weighted)
            },
            "edge_type_properties": {
                "edge_type_counts": {
                    edge_type: sum(1 for edge in graph.edges(data=True) if 'Edge Type' in edge[2] and edge[2]['Edge Type'] == edge_type)
                    for edge_type in set(edge[2].get('Edge Type', 'Unknown') for edge in graph.edges(data=True))
                }
            },
            "node_type_properties": {
                "node_type_counts": {
                    node_type: sum(1 for node in graph.nodes(data=True) if 'Node Type' in node[1] and node[1]['Node Type'] == node_type)
                    for node_type in set(node[1].get('Node Type', 'Unknown') for node in graph.nodes(data=True))
                }
            }
        }

        return JSONResponse(content=summary)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing graph: {str(e)}")


@app.get("/node-types/{graph_id}", summary="Get node type counts by graph ID")
async def get_node_type_counts(graph_id: str):
    """
    Get the count of nodes for each type in a NetworkX graph.

    Args:
        graph_id: The unique ID returned when uploading the graph, or "default" to access the default graph.

    Returns:
        A JSON object containing the count of nodes for each type.
    """
    logger.debug("Calling.")
    # Check if graph ID exists in registry
    if graph_id not in graph_registry:
        raise HTTPException(status_code=404, detail="Graph ID not found")

    try:
        # Load the graph from file
        file_path = graph_registry[graph_id]
        async with await open_file(file_path, 'r') as f:
            logger.debug("Opening file.")
            content = await f.read()
            logger.debug("Closing file.")

        data = json.loads(content)
        # Load as NetworkX graph
        graph = nx.node_link_graph(data)

        # Count nodes by type
        node_type_counts = {}

        for node in graph.nodes(data=True):
            node_data = node[1]
            if 'Node Type' in node_data:
                node_type = node_data['Node Type']
                node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1
            else:
                node_type_counts['Unknown'] = node_type_counts.get('Unknown', 0) + 1

        return JSONResponse(content={
            "graph_id": graph_id,
            "node_type_counts": node_type_counts,
            "total_nodes": graph.number_of_nodes()
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing graph: {str(e)}")


@app.get("/edge-types/{graph_id}", summary="Get edge type counts by graph ID")
async def get_edge_type_counts(graph_id: str):
    """
    Get the count of edges for each type in a NetworkX graph.

    Args:
        graph_id: The unique ID returned when uploading the graph, or "default" to access the default graph.

    Returns:
        A JSON object containing the count of edges for each type.
    """
    logger.debug("Calling.")
    # Check if graph ID exists in registry
    if graph_id not in graph_registry:
        raise HTTPException(status_code=404, detail="Graph ID not found")

    try:
        # Load the graph from file
        file_path = graph_registry[graph_id]
        async with await open_file(file_path, 'r') as f:
            logger.debug("Opening file.")
            content = await f.read()
            logger.debug("Closing file.")

        data = json.loads(content)
        # Load as NetworkX graph
        graph = nx.node_link_graph(data)

        # Count edges by type
        edge_type_counts = {}

        for edge in graph.edges(data=True):
            edge_data = edge[2]
            if 'Edge Type' in edge_data:
                edge_type = edge_data['Edge Type']
                edge_type_counts[edge_type] = edge_type_counts.get(edge_type, 0) + 1
            else:
                edge_type_counts['Unknown'] = edge_type_counts.get('Unknown', 0) + 1

        return JSONResponse(content={
            "graph_id": graph_id,
            "edge_type_counts": edge_type_counts,
            "total_edges": graph.number_of_edges()
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing graph: {str(e)}")
    """
    Health check endpoint to verify the API is running.

    Returns:
        Status of the API.
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "graph_count": len(graph_registry)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)