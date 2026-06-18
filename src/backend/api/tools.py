from fastapi import APIRouter

from backend.schemas.chat import ToolStatusResponse
from backend.services.agent_service import agent_service

router = APIRouter(prefix="/api", tags=["tools"])


@router.get("/tools", response_model=ToolStatusResponse)
def get_tools() -> ToolStatusResponse:
    return ToolStatusResponse(**agent_service.tool_status())
