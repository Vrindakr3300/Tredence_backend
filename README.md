# Workflow Graph Engine - FastAPI Backend

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd Tradence
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install fastapi uvicorn pydantic
   ```

4. **Run the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

   Or using Python directly:
   ```bash
   python -m app.main
   ```

5. **Access the API:**
   - API Documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc
   - Root endpoint: http://localhost:8000/

## 📁 Project Structure

```
app/
├── main.py                 # FastAPI application entry point
├── api/
│   ├── __init__.py
│   └── graph_endpoints.py  # Graph management and execution endpoints
├── core/
│   ├── __init__.py
│   ├── engine.py          # Workflow execution engine
│   ├── registry.py        # Tool/function registry
│   └── models.py          # Pydantic models for requests/responses
├── workflows/
│   ├── __init__.py
│   └── code_review.py     # Sample code review workflow
└── db/
    ├── __init__.py
    └── memory_store.py    # In-memory storage for graphs and runs
```

## 🔧 How the Engine Works

### Core Concepts

1. **Nodes**: Async Python functions that accept and modify a state dictionary
2. **State**: A dictionary that flows from node to node, accumulating data
3. **Edges**: Mappings that define the flow between nodes
4. **Execution Log**: Records each node execution with state snapshots

### Execution Flow

1. **Graph Creation**: Define nodes (function paths) and edges (flow connections)
2. **Graph Execution**: 
   - Start with initial state
   - Execute nodes sequentially based on edges
   - Each node receives and modifies the state
   - Execution is logged at each step
3. **Branching**: Edges can point to a single node or a list of nodes (for future conditional branching)
4. **Looping**: Nodes can return `"repeat"` to loop back to themselves, or use `"goto:node_name"` to jump to a specific node

### Node Function Signature

Nodes must be async functions that:
- Accept a `state: Dict[str, Any]` parameter
- Modify the state dictionary in-place or return updates
- Can return:
  - `None` or a dict: Continue to next node
  - `"repeat"`: Loop back to current node
  - `"goto:node_name"`: Jump to specific node

Example:
```python
async def my_node(state: Dict[str, Any]) -> Dict[str, Any]:
    state["processed"] = True
    state["count"] = state.get("count", 0) + 1
    return state
```

## 📡 API Endpoints

### 1. Create Graph

**POST** `/graph/create`

Create a new workflow graph.

**Request Body:**
```json
{
  "nodes": {
    "extract": "workflows.code_review.extract_functions",
    "analyze": "workflows.code_review.check_complexity"
  },
  "edges": {
    "extract": "analyze",
    "analyze": "complete"
  },
  "metadata": {
    "name": "Code Review Workflow",
    "version": "1.0"
  }
}
```

**Response:**
```json
{
  "graph_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 2. Run Graph

**POST** `/graph/run`

Execute a workflow graph.

**Request Body:**
```json
{
  "graph_id": "550e8400-e29b-41d4-a716-446655440000",
  "initial_state": {
    "code": "def hello():\n    print('world')",
    "quality_threshold": 70
  },
  "start_node": "extract"
}
```

**Response:**
```json
{
  "run_id": "660e8400-e29b-41d4-a716-446655440001",
  "final_state": {
    "code": "...",
    "functions": [...],
    "quality_score": 85
  },
  "log": [
    {
      "node_name": "extract",
      "state_snapshot": {...},
      "timestamp": 1234567890.123,
      "status": "completed"
    }
  ],
  "status": "completed"
}
```

### 3. Get Run State

**GET** `/graph/state/{run_id}`

Retrieve the current state of a workflow run.

**Response:**
```json
{
  "run_id": "660e8400-e29b-41d4-a716-446655440001",
  "state": {...},
  "log": [...],
  "status": "completed",
  "current_node": null,
  "error": null
}
```

### 4. List Graphs

**GET** `/graph/list`

List all stored graphs.

### 5. List Runs

**GET** `/graph/runs`

List all workflow runs.

## 🎯 Supported Features

### ✅ Implemented

- **Async Node Execution**: All nodes are executed asynchronously
- **State Flow**: State dictionary flows between nodes
- **Simple Edges**: Direct node-to-node connections
- **Branching Edges**: Support for multiple next nodes (takes first in MVP)
- **Looping**: Nodes can return `"repeat"` to loop
- **Execution Logging**: Complete log of node executions with state snapshots
- **Error Handling**: Failed nodes are logged with error information
- **Tool Registry**: Register and load functions from module paths
- **In-Memory Storage**: Store graphs and runs with UUID-based IDs

### 🔄 Control Flow

- **Continue**: Return `None` or a dict to proceed to next node
- **Loop**: Return `"repeat"` to execute current node again
- **Jump**: Return `"goto:node_name"` to jump to a specific node
- **Branch**: Edges can specify multiple next nodes (future: conditional branching)

## 📝 Sample Workflow: Code Review

The included `workflows/code_review.py` demonstrates a complete workflow:

1. **extract_functions**: Extracts function definitions from code
2. **check_complexity**: Calculates complexity scores for each function
3. **detect_issues**: Identifies code quality issues
4. **suggest_improvements**: Generates improvement suggestions and quality score
5. **check_quality_threshold**: Loops if quality score is below threshold

### Example Usage

```python
# Create the graph
POST /graph/create
{
  "nodes": {
    "extract": "workflows.code_review.extract_functions",
    "complexity": "workflows.code_review.check_complexity",
    "detect": "workflows.code_review.detect_issues",
    "suggest": "workflows.code_review.suggest_improvements",
    "check": "workflows.code_review.check_quality_threshold"
  },
  "edges": {
    "extract": "complexity",
    "complexity": "detect",
    "detect": "suggest",
    "suggest": "check",
    "check": "suggest"  # Loop back if threshold not met
  }
}

# Run the graph
POST /graph/run
{
  "graph_id": "...",
  "initial_state": {
    "code": "def complex_function():\n    # lots of code...",
    "quality_threshold": 70
  }
}
```

## 🔮 Future Improvements

If given more time, the following enhancements would be valuable:

### 1. **Conditional Branching**
   - Evaluate conditions in edges based on state values
   - Support for expressions like `"if state.score > 70: node_a else: node_b"`

### 2. **Parallel Execution**
   - Execute multiple nodes in parallel when edges branch
   - Merge state from parallel branches

### 3. **Persistence**
   - Replace in-memory storage with a database (PostgreSQL, MongoDB)
   - Support for graph versioning
   - Run history and analytics

### 4. **Advanced Control Flow**
   - Support for sub-graphs/nested workflows
   - Error recovery and retry mechanisms
   - Timeout handling for long-running nodes

### 5. **Node Types**
   - Input/output validation for nodes
   - Node metadata (description, parameters, etc.)
   - Visual graph representation

### 6. **Performance**
   - Caching of loaded functions
   - State compression for large states
   - Streaming execution logs

### 7. **Developer Experience**
   - Graph validation before execution
   - Better error messages with stack traces
   - Graph visualization API
   - Workflow templates and examples

### 8. **Security**
   - Sandboxed node execution
   - Authentication and authorization
   - Rate limiting

## 🧪 Testing

Example test workflow:

```bash
# Start the server
uvicorn app.main:app --reload

# Create a graph (using curl or the Swagger UI)
curl -X POST "http://localhost:8000/graph/create" \
  -H "Content-Type: application/json" \
  -d '{
    "nodes": {
      "extract": "workflows.code_review.extract_functions",
      "complexity": "workflows.code_review.check_complexity"
    },
    "edges": {
      "extract": "complexity"
    }
  }'

# Run the graph
curl -X POST "http://localhost:8000/graph/run" \
  -H "Content-Type: application/json" \
  -d '{
    "graph_id": "<graph_id_from_previous_response>",
    "initial_state": {
      "code": "def hello():\n    return \"world\""
    }
  }'
```

## 📚 Code Quality

- **Type Hints**: All functions include type hints
- **Pydantic Models**: Request/response validation
- **Async/Await**: Proper async patterns throughout
- **Error Handling**: Comprehensive error handling and logging
- **Modular Design**: Clear separation of concerns
- **Documentation**: Inline comments and docstrings

## 🤝 Contributing

This is an MVP implementation. For production use, consider:
- Adding comprehensive tests
- Implementing proper logging
- Adding monitoring and metrics
- Security hardening
- Performance optimization

## 📄 License

This project is provided as-is for demonstration purposes.

