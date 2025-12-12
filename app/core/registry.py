"""
Tool registry for storing and accessing workflow tools/functions.
"""
from typing import Any, Callable, Dict, Optional
import importlib
import inspect


class ToolRegistry:
    """
    Simple dict-based registry for storing and accessing tools/functions.
    
    Tools can be registered programmatically or loaded from module paths.
    """
    
    def __init__(self):
        """Initialize an empty registry."""
        self._tools: Dict[str, Callable] = {}
    
    def register(self, name: str, func: Callable) -> None:
        """
        Register a tool/function in the registry.
        
        Args:
            name: Unique name for the tool
            func: The function to register (should be async)
        """
        if not inspect.iscoroutinefunction(func):
            raise ValueError(f"Tool '{name}' must be an async function")
        self._tools[name] = func
    
    def get(self, name: str) -> Optional[Callable]:
        """
        Get a tool by name.
        
        Args:
            name: Name of the tool to retrieve
            
        Returns:
            The registered function or None if not found
        """
        return self._tools.get(name)
    
    def load_from_path(self, path: str) -> Callable:
        """
        Load a function from a module path string.
        
        Args:
            path: Dot-separated path (e.g., "workflows.code_review.extract_functions")
            
        Returns:
            The loaded function
            
        Raises:
            ImportError: If the module or function cannot be imported
        """
        if path in self._tools:
            return self._tools[path]
        
        try:
            module_path, func_name = path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            func = getattr(module, func_name)
            
            if not inspect.iscoroutinefunction(func):
                raise ValueError(f"Function '{path}' must be async")
            
            # Cache it for future use
            self._tools[path] = func
            return func
        except (ImportError, AttributeError, ValueError) as e:
            raise ImportError(f"Failed to load function from path '{path}': {e}")
    
    def list_tools(self) -> Dict[str, str]:
        """
        List all registered tools.
        
        Returns:
            Dictionary mapping tool names to their string representations
        """
        return {name: str(func) for name, func in self._tools.items()}
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()


# Global registry instance
registry = ToolRegistry()

