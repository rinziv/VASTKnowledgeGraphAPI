"""
FastAPI application for handling NetworkX graphs.

This application provides endpoints for:
- Uploading JSON files containing NetworkX graphs
- Retrieving graph summaries by unique ID
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import networkx as nx
import json
import os
import uuid
from typing import Dict, Any
from pathlib import Path

app = FastAPI(
    title="NetworkX Graph API",
    description="API for uploading and analyzing NetworkX graphs",
    version="1.0.0"
)

# Directory to store uploaded graph files
GRAPH_STORAGE_DIR = "graph_storage"

# Create storage directory if it doesn't exist
Path(GRAPH_STORAGE_DIR).mkdir(exist_ok=True)

# Dictionary to map graph IDs to file paths
# In production, this would be a database
graph_registry: Dict[str, str] = {}


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


@app.get("/summary/{graph_id}", summary="Get graph summary by ID")
async def get_graph_summary(graph_id: str):
    """
    Get a summary of the properties of a NetworkX graph.

    Args:
        graph_id: The unique ID returned when uploading the graph.

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
                "is_weakly_connected": nx.is_weakly_connected(graph) if nx.is_directed(graph) else None,
                "is_strongly_connected": nx.is_strongly_connected(graph) if nx.is_directed(graph) else None,
                "is_connected": nx.is_connected(graph) if not nx.is_directed(graph) else None,
            },
            "degree_properties": {
                "average_degree": sum(dict(graph.degree()).values()) / graph.number_of_nodes() if graph.number_of_nodes() > 0 else 0,
                "degree_centrality": dict(nx.degree_centrality(graph)) if graph.number_of_nodes() > 0 else {},
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
            }
        }

        return JSONResponse(content=summary)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing graph: {str(e)}")


@app.get("/health/", summary="Health check endpoint")
async def health_check():
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
