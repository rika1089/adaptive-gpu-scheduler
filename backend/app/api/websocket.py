import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services import runner

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    q = runner.subscribe_logs()

    # Helper: try to drain queue into websocket, non-blocking
    async def drain():
        sent = 0
        while sent < 20:          # max 20 lines per drain to avoid starvation
            try:
                line = q.get_nowait()
                await websocket.send_text(line)
                sent += 1
            except asyncio.QueueEmpty:
                break

    try:
        # Greet with current status
        status = runner.get_status()
        await websocket.send_text(
            json.dumps({"type": "status", "data": status})
        )
        await websocket.send_text(
            f"[connected] Status: {status['status']}"
        )

        while True:
            # Drain any pending log lines first
            await drain()

            # Wait up to 1 second for new items, then send heartbeat
            try:
                line = await asyncio.wait_for(q.get(), timeout=1.0)
                await websocket.send_text(line)
                # Drain any additional buffered lines immediately
                await drain()
            except asyncio.TimeoutError:
                # Heartbeat + live status update every second
                current = runner.get_status()
                await websocket.send_text(
                    json.dumps({"type": "status", "data": current})
                )

    except (WebSocketDisconnect, Exception):
        pass
    finally:
        runner.unsubscribe_logs(q)
