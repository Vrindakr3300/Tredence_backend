"""
Workflow/graph execution engine.

Supports:
- Async node execution
- State flow between nodes
- Branching based on state values
- Looping (nodes can return "repeat" to run again)
- Execution logging
"""
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID
from app.core.models import (
    GraphDefinition,
    RunState,
    ExecutionLogEntry
)
from app.core.registry import registry
from app.db.memory_store import store


class WorkflowEngine:
    """
    Engine for executing workflow graphs.
    
    Nodes are async functions that accept and modify state.
    State flows from node to node via edges.
    Supports branching and looping.
    """
    
    def __init__(self):
        """Initialize the workflow engine."""
        self.max_iterations = 1000  # Prevent infinite loops
        self.max_loop_iterations = 100  # Max iterations for a single loop
    
    async def execute_node(
        self,
        node_name: str,
        node_func: callable,
        state: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Execute a single node.
        
        Args:
            node_name: Name of the node
            node_func: The async function to execute
            state: Current state dictionary
            
        Returns:
            Tuple of (updated_state, next_action)
            next_action can be:
            - None: continue to next node
            - "repeat": loop back to this node
            - node_name: jump to specific node
            - List of node names: branch to multiple nodes (not supported in simple execution)
            
        Raises:
            Exception: If node execution fails
        """
        try:
            # Create a copy of state to pass to node
            state_copy = state.copy()
            
            # Execute the node function
            result = await node_func(state_copy)
            
            # If result is a dict, merge it into state
            if isinstance(result, dict):
                state.update(result)
            # If result is a string, it might be a control flow instruction
            elif isinstance(result, str):
                if result == "repeat":
                    return state, "repeat"
                elif result.startswith("goto:"):
                    return state, result[5:]  # Extract node name after "goto:"
            
            return state, None
            
        except Exception as e:
            raise Exception(f"Error executing node '{node_name}': {str(e)}")
    
    def get_next_nodes(
        self,
        current_node: str,
        edges: Dict[str, Union[str, List[str]]],
        state: Dict[str, Any]
    ) -> Optional[Union[str, List[str]]]:
        """
        Determine the next node(s) based on edges and state.
        
        Supports:
        - Simple edge: {"node1": "node2"}
        - Branching edge: {"node1": ["node2", "node3"]}
        - Conditional branching: edges can be functions (not implemented in MVP)
        
        Args:
            current_node: Current node name
            edges: Edge definitions
            state: Current state (for future conditional branching)
            
        Returns:
            Next node name(s) or None if no edge found
        """
        return edges.get(current_node)
    
    async def execute_graph(
        self,
        graph_id: str,
        initial_state: Dict[str, Any],
        start_node: Optional[str] = None
    ) -> RunState:
        """
        Execute a complete workflow graph.
        
        Args:
            graph_id: ID of the graph to execute
            initial_state: Initial state dictionary
            start_node: Optional starting node (defaults to first node in graph)
            
        Returns:
            RunState with final state and execution log
        """
        # Get graph definition
        graph = store.get_graph(graph_id)
        if not graph:
            raise ValueError(f"Graph '{graph_id}' not found")
        
        # Create a new run
        run_id_str = store.create_run(UUID(graph_id), initial_state)
        run_state = store.get_run(run_id_str)
        
        if not run_state:
            raise RuntimeError("Failed to create run")
        
        # Determine starting node
        if start_node:
            if start_node not in graph.nodes:
                raise ValueError(f"Start node '{start_node}' not found in graph")
            current_node = start_node
        else:
            # Use first node as default
            if not graph.nodes:
                raise ValueError("Graph has no nodes")
            current_node = list(graph.nodes.keys())[0]
        
        # Execution loop
        iteration_count = 0
        loop_count = 0
        visited_nodes = set()
        
        try:
            while iteration_count < self.max_iterations:
                iteration_count += 1
                
                # Check if we've completed (no next node)
                if current_node is None:
                    run_state.status = "completed"
                    break
                
                # Load node function
                node_path = graph.nodes.get(current_node)
                if not node_path:
                    raise ValueError(f"Node '{current_node}' not found in graph definition")
                
                try:
                    node_func = registry.load_from_path(node_path)
                except ImportError as e:
                    raise ValueError(f"Failed to load node function '{node_path}': {e}")
                
                # Execute node
                run_state.current_node = current_node
                updated_state, next_action = await self.execute_node(
                    current_node,
                    node_func,
                    run_state.state
                )
                
                # Log execution
                log_entry = ExecutionLogEntry(
                    node_name=current_node,
                    state_snapshot=updated_state.copy(),
                    timestamp=time.time(),
                    status="completed"
                )
                run_state.log.append(log_entry)
                visited_nodes.add(current_node)
                
                # Handle next action
                if next_action == "repeat":
                    loop_count += 1
                    if loop_count >= self.max_loop_iterations:
                        raise RuntimeError(f"Loop iteration limit ({self.max_loop_iterations}) exceeded")
                    # Stay on current node
                    continue
                elif next_action and next_action.startswith("goto:"):
                    current_node = next_action[5:]
                    loop_count = 0  # Reset loop counter on node change
                elif next_action:
                    current_node = next_action
                    loop_count = 0
                else:
                    # Get next node from edges
                    next_nodes = self.get_next_nodes(current_node, graph.edges, run_state.state)
                    
                    if next_nodes is None:
                        # No more edges, execution complete
                        run_state.status = "completed"
                        break
                    elif isinstance(next_nodes, str):
                        # Simple edge to single node
                        current_node = next_nodes
                        loop_count = 0
                    elif isinstance(next_nodes, list):
                        # Branching: for MVP, take first node
                        # In a full implementation, this would evaluate conditions
                        if next_nodes:
                            current_node = next_nodes[0]
                            loop_count = 0
                        else:
                            run_state.status = "completed"
                            break
                    else:
                        run_state.status = "completed"
                        break
            else:
                # Loop ended due to max iterations
                run_state.status = "failed"
                run_state.error = f"Maximum iterations ({self.max_iterations}) exceeded"
            
            # Update final state
            run_state.current_node = None
            store.update_run(run_id_str, run_state)
            
        except Exception as e:
            # Handle errors
            run_state.status = "failed"
            run_state.error = str(e)
            run_state.current_node = None
            
            # Log error
            if run_state.log:
                run_state.log[-1].status = "error"
            else:
                log_entry = ExecutionLogEntry(
                    node_name=current_node or "unknown",
                    state_snapshot=run_state.state.copy(),
                    timestamp=time.time(),
                    status="error"
                )
                run_state.log.append(log_entry)
            
            store.update_run(run_id_str, run_state)
        
        return run_state


# Global engine instance
engine = WorkflowEngine()

