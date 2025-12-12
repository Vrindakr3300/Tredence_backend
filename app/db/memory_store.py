"""
In-memory storage for graphs and workflow runs.
"""
from typing import Dict, Optional
from uuid import UUID, uuid4
from app.core.models import GraphDefinition, RunState


class MemoryStore:
    """
    Simple in-memory storage for graphs and runs.
    
    Uses dictionaries keyed by UUID strings for easy serialization.
    """
    
    def __init__(self):
        """Initialize empty storage."""
        self._graphs: Dict[str, GraphDefinition] = {}
        self._runs: Dict[str, RunState] = {}
    
    def create_graph(self, graph_def: GraphDefinition) -> str:
        """
        Store a new graph definition.
        
        Args:
            graph_def: The graph definition to store
            
        Returns:
            The graph ID as a string
        """
        graph_id_str = str(graph_def.graph_id)
        self._graphs[graph_id_str] = graph_def
        return graph_id_str
    
    def get_graph(self, graph_id: str) -> Optional[GraphDefinition]:
        """
        Retrieve a graph definition by ID.
        
        Args:
            graph_id: The graph ID (as string)
            
        Returns:
            The graph definition or None if not found
        """
        return self._graphs.get(graph_id)
    
    def list_graphs(self) -> Dict[str, GraphDefinition]:
        """
        List all stored graphs.
        
        Returns:
            Dictionary mapping graph IDs to graph definitions
        """
        return self._graphs.copy()
    
    def create_run(self, graph_id: UUID, initial_state: dict) -> str:
        """
        Create a new workflow run.
        
        Args:
            graph_id: The graph ID to run
            initial_state: Initial state for the run
            
        Returns:
            The run ID as a string
        """
        run_id = uuid4()
        run_state = RunState(
            run_id=run_id,
            graph_id=graph_id,
            state=initial_state.copy(),
            status="running"
        )
        run_id_str = str(run_id)
        self._runs[run_id_str] = run_state
        return run_id_str
    
    def get_run(self, run_id: str) -> Optional[RunState]:
        """
        Retrieve a run state by ID.
        
        Args:
            run_id: The run ID (as string)
            
        Returns:
            The run state or None if not found
        """
        return self._runs.get(run_id)
    
    def update_run(self, run_id: str, run_state: RunState) -> None:
        """
        Update a run state.
        
        Args:
            run_id: The run ID (as string)
            run_state: The updated run state
        """
        self._runs[run_id] = run_state
    
    def list_runs(self) -> Dict[str, RunState]:
        """
        List all stored runs.
        
        Returns:
            Dictionary mapping run IDs to run states
        """
        return self._runs.copy()
    
    def delete_run(self, run_id: str) -> bool:
        """
        Delete a run by ID.
        
        Args:
            run_id: The run ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        if run_id in self._runs:
            del self._runs[run_id]
            return True
        return False


# Global storage instance
store = MemoryStore()

