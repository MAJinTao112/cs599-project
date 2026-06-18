from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    messages: List[ChatMessage] = Field(default_factory=list)
    max_iterations: int = Field(default=30, ge=1, le=100)


class ChatResponse(BaseModel):
    answer: str
    scenario_type: str
    needs_r1: bool
    extraction: Dict[str, Any] = Field(default_factory=dict)


class ToolStatusResponse(BaseModel):
    tools: List[str]
    count: int
    mcp_available: bool
    uploaded_files: List[str] = Field(default_factory=list)
    rag_total: int = 0


class UploadResponse(BaseModel):
    uploaded: int
    files: List[str]
    message: str


class HealthResponse(BaseModel):
    status: str
    service: str
    frontend: str
