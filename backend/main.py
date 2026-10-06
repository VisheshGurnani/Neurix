"""
FastAPI Backend for GitHub Repository Code Explainer

Entry point: backend/main.py
"""

import os
import sys
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from fastapi.middleware.cors import CORSMiddleware

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import local services
from backend.services.repository_processor import IGNORE_DIRS, RepositoryProcessor
from backend.services.llm_service import LLMService

# Initialize FastAPI app
app = FastAPI(
    title="GitHub Repository Code Explainer",
    description="A local GenAI application that analyzes GitHub repositories and generates explanations.",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (can be restricted in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
repository_processor = RepositoryProcessor()
llm_service = LLMService()


# Request/Response models
class GitHubURLRequest(BaseModel):
    """Request model for GitHub URL."""
    url: HttpUrl
    max_files: Optional[int] = Field(default=10, ge=1, le=50)


class ExplanationResponse(BaseModel):
    """Response model with generated explanation."""
    success: bool
    message: str
    explanation: Optional[str] = None
    error: Optional[str] = None
    repository: Optional[str] = None
    files_analyzed: int = 0
    context_truncated: bool = False
    model_used: Optional[str] = None
    tech_stack: list[str] = Field(default_factory=list)
    detected_files: list[dict] = Field(default_factory=list)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "GitHub Repository Code Explainer",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "/explain": "Analyze a GitHub repository and generate explanation",
            "/analyze": "Compatibility alias for /explain",
            "/health": "Health check endpoint",
            "/models": "List available Groq models"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/models")
async def list_models():
    """List available Groq models."""
    try:
        models = llm_service.list_models()
        return {
            "success": True,
            "message": f"Found {len(models)} model(s)",
            "models": models
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }



def _categorize_file(rel_path: str) -> str:
    """Return the UI-facing category for an analyzed file."""
    from pathlib import Path as _Path
    filename = _Path(rel_path).name.lower()
    ext = _Path(rel_path).suffix.lower()
    if filename in {"readme.md", "license", "copying", "contributing.md"} or ext in {".md", ".txt"}:
        return "Documentation"
    if filename in {"package.json", "requirements.txt", "pyproject.toml", "cargo.toml", "go.mod", "tsconfig.json"} or ext in {".yaml", ".yml", ".toml", ".json"}:
        return "Config"
    if filename in {"main.py", "app.py", "server.py", "index.js", "index.ts", "server.ts", "wsgi.py", "asgi.py"}:
        return "Entry Point"
    if ext in {".html", ".css", ".scss"}:
        return "Asset"
    return "Source"


def _detect_tech_stack(files_context: list[dict]) -> list[str]:
    """Infer a compact technology stack from filenames and readable content."""
    paths = [str(item.get("path", "")).lower() for item in files_context]
    contents = " ".join(str(item.get("content", "")).lower() for item in files_context)
    techs = []
    def add(name: str):
        if name not in techs:
            techs.append(name)
    if any(p.endswith(".py") for p in paths): add("Python")
    if any(p.endswith((".js", ".jsx")) for p in paths): add("JavaScript")
    if any(p.endswith((".ts", ".tsx")) for p in paths): add("TypeScript")
    if any(p.endswith((".tsx", ".jsx")) for p in paths) or "react" in contents: add("React")
    if "fastapi" in contents: add("FastAPI")
    if "streamlit" in contents: add("Streamlit")
    if "express" in contents: add("Express")
    if "vite" in contents or any("vite.config" in p for p in paths): add("Vite")
    if "tailwind" in contents: add("Tailwind CSS")
    if "gitpython" in contents or "from git import repo" in contents: add("GitPython")
    if "groq" in contents: add("Groq")
    if "ollama" in contents: add("Ollama")
    if "mongodb" in contents or "mongoose" in contents: add("MongoDB")
    if "postgres" in contents or "postgresql" in contents: add("PostgreSQL")
    return techs


@app.post("/explain", response_model=ExplanationResponse)
@app.post("/analyze", response_model=ExplanationResponse)
async def analyze_repository(request: GitHubURLRequest):
    """
    Analyze a GitHub repository and generate an explanation.

    Args:
        url: GitHub repository URL (e.g., https://github.com/username/repo)
        max_files: Maximum number of files to include in analysis (default: 10)

    Returns:
        ExplanationResponse with the generated explanation or error message.
    """
    try:
        repository_name = "/".join(str(request.url).rstrip("/").split("/")[-2:])

        # Validate the Groq connection only for the analysis request;
        # /health is independent of the model provider.
        if not llm_service.check_model_available():
            return ExplanationResponse(
                success=False,
                message="Groq configuration check failed",
                error="Groq is unavailable or the configured model cannot be used. "
                      "Check GROQ_API_KEY and GROQ_MODEL."
            )

        # Clone and process repository
        print(f"Cloning repository: {request.url}")
        clone_success = repository_processor.clone_repository(str(request.url))

        if not clone_success:
            return ExplanationResponse(
                success=False,
                message="Repository cloning failed",
                error=f"Failed to clone repository: {request.url}"
            )

        # Process repository and extract files
        print("Processing repository...")
        files_context = repository_processor.process_repository()

        # Limit to requested number of files while preserving processor order.
        files_context = files_context[:request.max_files]
        context_truncated = sum(len(item['content']) for item in files_context) > 60000

        print(f"Extracted {len(files_context)} files for analysis")

        # Generate explanation
        print("Generating explanation with Groq...")
        explanation = llm_service.generate_explanation(files_context)

        if not explanation:
            return ExplanationResponse(
                success=False,
                message="Explanation generation failed",
                repository=repository_name,
                files_analyzed=len(files_context),
                context_truncated=context_truncated,
                error="Failed to generate explanation from Groq"
            )

        return ExplanationResponse(
            success=True,
            message=f"Successfully analyzed repository with {len(files_context)} files",
            explanation=explanation,
            repository=repository_name,
            files_analyzed=len(files_context),
            context_truncated=context_truncated,
            model_used=llm_service.model,
            tech_stack=_detect_tech_stack(files_context),
            detected_files=[
                {
                    "path": item["path"],
                    "priority": item["priority"],
                    "size": len(item["content"]),
                    "category": _categorize_file(item["path"]),
                    "snippet": item["content"][:400],
                }
                for item in files_context
            ],
        )

    except HTTPException:
        raise
    except ValueError as e:
        return ExplanationResponse(
            success=False,
            message="Invalid input",
            error=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error: {e}")
        return ExplanationResponse(
            success=False,
            message="An unexpected error occurred",
            error=f"An unexpected error occurred: {str(e)}"
        )
    finally:
        # Cleanup must also happen after Groq, cloning, or processing errors.
        repository_processor.cleanup()


@app.get("/config")
async def get_config():
    """Get current configuration."""
    return {
        "llm_provider": "Groq",
        "groq_api_url": llm_service.host,
        "groq_model": llm_service.model,
        "supported_extensions": [
            ".py", ".js", ".ts", ".java", ".c", ".cpp",
            ".html", ".css", ".json", ".md", ".yaml", ".toml"
        ],
        "ignored_dirs": list(sorted(IGNORE_DIRS))[:5],
        "priority_levels": {
            "high_priority_files": 10,
            "medium_priority_files": 8,
            "source_code": 6,
            "documentation": 5,
            "web_assets": 3
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
