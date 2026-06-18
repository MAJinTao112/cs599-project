import asyncio
from typing import Dict

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.agent_service import agent_service
from backend.services.sse import sse_event

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    result = await asyncio.to_thread(
        agent_service.run_chat,
        request.message,
        [item.model_dump() for item in request.messages],
        request.max_iterations,
        None,
    )
    return ChatResponse(**result)


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    async def generate():
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[Dict[str, object]] = asyncio.Queue()

        def push_status(message: str) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, {"event": "status", "data": {"message": message}})

        def run_agent() -> None:
            try:
                result = agent_service.run_chat(
                    request.message,
                    [item.model_dump() for item in request.messages],
                    request.max_iterations,
                    push_status,
                )
                loop.call_soon_threadsafe(
                    queue.put_nowait,
                    {
                        "event": "analysis",
                        "data": {
                            "scenario_type": result["scenario_type"],
                            "needs_r1": result["needs_r1"],
                            "extraction": result["extraction"],
                        },
                    },
                )
                loop.call_soon_threadsafe(queue.put_nowait, {"event": "final", "data": result})
            except Exception as exc:
                loop.call_soon_threadsafe(queue.put_nowait, {"event": "error", "data": {"message": str(exc)}})
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, {"event": "done", "data": {}})

        task = asyncio.create_task(asyncio.to_thread(run_agent))
        yield sse_event("status", {"message": "已收到请求，正在启动旅行规划引擎..."})

        while True:
            item = await queue.get()
            event = str(item["event"])
            if event == "done":
                break
            yield sse_event(event, item["data"])

        await task

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
