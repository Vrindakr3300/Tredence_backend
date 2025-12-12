"""
Pydantic models for the workflow engine.
"""
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from pydantic import BaseModel, Field


class NodeDefinition(BaseModel):
    """Definition of a node in a workflow graph."""
    name: str
    function_path: Optional[str] = None  # e.g., "workflows.code_review.extract_functions"
    function: Optional[Any] = None  # Direct function reference (for internal use)


class EdgeDefinition(BaseModel):
    """Definition of an edge connecting nodes."""
    from_node: str
    to_node: Union[str, List[str]]  # Can be single node or list for branching


class GraphDefinition(BaseModel):
    """Complete graph definition with nodes and edges."""
    graph_id: UUID
    nodes: Dict[str, str] = Field(
        ..., 
        description="Mapping of node names to function paths"
    )
    edges: Dict[str, Union[str, List[str]]] = Field(
        ...,
        description="Mapping of node names to next node(s)"
    )
    metadata: Optional[Dict[str, Any]] = None


class ExecutionLogEntry(BaseModel):
    """Single entry in the execution log."""
    node_name: str
    state_snapshot: Dict[str, Any]
    timestamp: float
    status: str = "completed"  # "completed", "error", "skipped"


class RunState(BaseModel):
    """State of a workflow run."""
    run_id: UUID
    graph_id: UUID
    state: Dict[str, Any] = Field(default_factory=dict)
    log: List[ExecutionLogEntry] = Field(default_factory=list)
    status: str = "running"  # "running", "completed", "failed", "paused"
    current_node: Optional[str] = None
    error: Optional[str] = None


class CreateGraphRequest(BaseModel):
    """Request model for creating a new graph."""
    nodes: Dict[str, str] = Field(
        ...,
        description="Mapping of node names to function paths (e.g., 'extract': 'workflows.code_review.extract_functions')"
    )
    edges: Dict[str, Union[str, List[str]]] = Field(
        ...,
        description="Mapping of node names to next node(s)"
    )
    metadata: Optional[Dict[str, Any]] = None


class CreateGraphResponse(BaseModel):
    """Response model for graph creation."""
    graph_id: str


class RunGraphRequest(BaseModel):
    """Request model for running a graph."""
    graph_id: str
    initial_state: Dict[str, Any] = Field(default_factory=dict)
    start_node: Optional[str] = None  # Optional starting node


class RunGraphResponse(BaseModel):
    """Response model for graph execution."""
    run_id: str
    final_state: Dict[str, Any]
    log: List[ExecutionLogEntry]
    status: str


class RunStateResponse(BaseModel):
    """Response model for getting run state."""
    run_id: str
    state: Dict[str, Any]
    log: List[ExecutionLogEntry]
    status: str
    current_node: Optional[str] = None
    error: Optional[str] = None

