from typing import List

from fastapi import APIRouter, File, UploadFile

from backend.schemas.chat import UploadResponse
from backend.services.agent_service import agent_service

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)) -> UploadResponse:
    loaded = []
    for file in files:
        loaded.append((file.filename or "document.txt", await file.read()))
    result = agent_service.index_documents(loaded)
    return UploadResponse(**result)
