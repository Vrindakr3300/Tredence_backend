"""
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.graph_endpoints import router as graph_router


# Create FastAPI app
app = FastAPI(
    title="Workflow Graph Engine API",
    description="A minimal but clean workflow/graph execution engine built with FastAPI",
    version="1.0.0"
)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(graph_router)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Workflow Graph Engine API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "create_graph": "POST /graph/create",
            "run_graph": "POST /graph/run",
            "get_run_state": "GET /graph/state/{run_id}",
            "list_graphs": "GET /graph/list",
            "list_runs": "GET /graph/runs"
        }
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

