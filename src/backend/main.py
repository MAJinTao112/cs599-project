from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import chat, documents, tools
from backend.schemas.chat import HealthResponse

app = FastAPI(title="Travel Planning Agent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(tools.router)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="travel-agent-api", frontend="vue")
