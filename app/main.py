
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.analyzer import analyze_code

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="CodeLens",
    description="Explainable AI-assisted code review",
    version="1.0.0"
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)


class ReviewRequest(BaseModel):
    code: str = Field(min_length=1, max_length=50000)
    language: str = "python"
    problem: str = "general"


@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE_DIR / "static" / "index.html").read_text(
        encoding="utf-8"
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/review")
def review(request: ReviewRequest):
    if request.language.lower() != "python":
        return {
            "error": "Only Python is currently supported."
        }

    return analyze_code(request.code, request.problem)