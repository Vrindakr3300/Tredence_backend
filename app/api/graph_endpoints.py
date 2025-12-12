"""
FastAPI endpoints for graph management and execution.
"""
from typing import Dict, Any
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, status
from app.core.models import (
    CreateGraphRequest,
    CreateGraphResponse,
    RunGraphRequest,
    RunGraphResponse,
    RunStateResponse
)
from app.core.engine import engine
from app.db.memory_store import store
from app.core.models import GraphDefinition


router = APIRouter(prefix="/graph", tags=["graph"])


@router.post(
    "/create",
    response_model=CreateGraphResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workflow graph",
    description="""
    Create a new workflow graph with nodes and edges.
    
    Nodes should map to async function paths (e.g., "workflows.code_review.extract_functions").
    Edges define the flow between nodes (can be a single node or list of nodes for branching).
    """
)
async def create_graph(request: CreateGraphRequest) -> CreateGraphResponse:
    """
    Create a new workflow graph.
    
    Args:
        request: Graph creation request with nodes and edges
        
    Returns:
        Graph ID of the created graph
        
    Raises:
        HTTPException: If graph creation fails
    """
    try:
        # Generate unique graph ID
        graph_id = uuid4()
        
        # Create graph definition
        graph_def = GraphDefinition(
            graph_id=graph_id,
            nodes=request.nodes,
            edges=request.edges,
            metadata=request.metadata
        )
        
        # Store graph
        graph_id_str = store.create_graph(graph_def)
        
        return CreateGraphResponse(graph_id=graph_id_str)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create graph: {str(e)}"
        )


@router.post(
    "/run",
    response_model=RunGraphResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute a workflow graph",
    description="""
    Execute a workflow graph with the given initial state.
    
    The graph will be executed asynchronously, and the final state and execution log
    will be returned upon completion.
    """
)
async def run_graph(request: RunGraphRequest) -> RunGraphResponse:
    """
    Execute a workflow graph.
    
    Args:
        request: Graph execution request with graph_id and initial state
        
    Returns:
        Run result with final state and execution log
        
    Raises:
        HTTPException: If graph execution fails
    """
    try:
        # Validate graph exists
        graph = store.get_graph(request.graph_id)
        if not graph:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Graph '{request.graph_id}' not found"
            )
        
        # Execute graph
        run_state = await engine.execute_graph(
            graph_id=request.graph_id,
            initial_state=request.initial_state,
            start_node=request.start_node
        )
        
        return RunGraphResponse(
            run_id=str(run_state.run_id),
            final_state=run_state.state,
            log=[entry.dict() for entry in run_state.log],
            status=run_state.status
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute graph: {str(e)}"
        )


@router.get(
    "/state/{run_id}",
    response_model=RunStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the state of a workflow run",
    description="""
    Retrieve the current state, execution log, and status of a workflow run.
    
    Useful for checking the progress of long-running workflows.
    """
)
async def get_run_state(run_id: str) -> RunStateResponse:
    """
    Get the state of a workflow run.
    
    Args:
        run_id: ID of the run to retrieve
        
    Returns:
        Current run state with logs
        
    Raises:
        HTTPException: If run not found
    """
    run_state = store.get_run(run_id)
    
    if not run_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found"
        )
    
    return RunStateResponse(
        run_id=str(run_state.run_id),
        state=run_state.state,
        log=[entry.dict() for entry in run_state.log],
        status=run_state.status,
        current_node=run_state.current_node,
        error=run_state.error
    )


@router.get(
    "/list",
    status_code=status.HTTP_200_OK,
    summary="List all graphs",
    description="Get a list of all stored graphs."
)
async def list_graphs() -> Dict[str, Any]:
    """
    List all stored graphs.
    
    Returns:
        Dictionary mapping graph IDs to graph metadata
    """
    graphs = store.list_graphs()
    return {
        "graphs": {
            graph_id: {
                "graph_id": str(graph_def.graph_id),
                "nodes": list(graph_def.nodes.keys()),
                "edges": graph_def.edges,
                "metadata": graph_def.metadata
            }
            for graph_id, graph_def in graphs.items()
        }
    }


@router.get(
    "/runs",
    status_code=status.HTTP_200_OK,
    summary="List all runs",
    description="Get a list of all workflow runs."
)
async def list_runs() -> Dict[str, Any]:
    """
    List all stored runs.
    
    Returns:
        Dictionary mapping run IDs to run summaries
    """
    runs = store.list_runs()
    return {
        "runs": {
            run_id: {
                "run_id": str(run_state.run_id),
                "graph_id": str(run_state.graph_id),
                "status": run_state.status,
                "current_node": run_state.current_node,
                "log_length": len(run_state.log)
            }
            for run_id, run_state in runs.items()
        }
    }

