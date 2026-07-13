import asyncio

from docker.errors import APIError, DockerException
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging_config import get_logger
from app.core.sandbox import sandbox_manager

logger = get_logger("terminal")
router = APIRouter(tags=["terminal"])


def _unwrap_exec_socket(sock):
    if hasattr(sock, "_sock"):
        return sock._sock
    return sock


def _client_host(websocket: WebSocket) -> str:
    if websocket.client is None:
        return "unknown"
    return f"{websocket.client.host}:{websocket.client.port}"


@router.websocket("/ws/labs/{lab_id}")
async def lab_terminal(websocket: WebSocket, lab_id: str) -> None:
    client_host = _client_host(websocket)
    logger.info("Terminal WebSocket connection requested lab_id=%s client=%s", lab_id, client_host)

    await websocket.accept()
    logger.info("Terminal WebSocket accepted lab_id=%s client=%s", lab_id, client_host)

    container = sandbox_manager.get_container(lab_id)
    if container is None:
        logger.error(
            "Terminal connection rejected — sandbox not available lab_id=%s client=%s "
            "(start the lab sandbox first, or the container may have stopped)",
            lab_id,
            client_host,
        )
        await websocket.close(code=4404, reason="Sandbox not active")
        return

    exec_id = None
    sock = None

    try:
        exec_id = container.client.api.exec_create(
            container.id,
            "/bin/sh",
            stdin=True,
            tty=True,
            stdout=True,
            stderr=True,
            environment={"TERM": "xterm-256color"},
        )["Id"]
        logger.info(
            "Exec session created lab_id=%s container_id=%s exec_id=%s",
            lab_id,
            container.id,
            exec_id,
        )
    except (APIError, DockerException) as exc:
        logger.error(
            "Failed to create container exec session lab_id=%s container_id=%s error=%s",
            lab_id,
            container.id,
            exc,
            exc_info=True,
        )
        await websocket.close(code=1011, reason="Failed to create shell session")
        return

    try:
        sock = _unwrap_exec_socket(
            container.client.api.exec_start(
                exec_id,
                detach=False,
                tty=True,
                socket=True,
            )
        )
        logger.info(
            "Exec socket attached lab_id=%s container_id=%s exec_id=%s",
            lab_id,
            container.id,
            exec_id,
        )
    except (APIError, DockerException) as exc:
        logger.error(
            "Failed to attach exec socket lab_id=%s container_id=%s exec_id=%s error=%s",
            lab_id,
            container.id,
            exec_id,
            exc,
            exc_info=True,
        )
        await websocket.close(code=1011, reason="Failed to attach shell session")
        return

    loop = asyncio.get_running_loop()

    async def pump_container_to_browser() -> None:
        try:
            while True:
                chunk = await loop.run_in_executor(None, sock.recv, 4096)
                if not chunk:
                    logger.info(
                        "Container stdout stream ended lab_id=%s container_id=%s exec_id=%s",
                        lab_id,
                        container.id,
                        exec_id,
                    )
                    break
                await websocket.send_text(chunk.decode("utf-8", errors="replace"))
        except (OSError, ConnectionError) as exc:
            logger.warning(
                "Container read stream error lab_id=%s container_id=%s exec_id=%s error=%s",
                lab_id,
                container.id,
                exec_id,
                exc,
                exc_info=True,
            )
        except Exception as exc:
            logger.error(
                "Unexpected error reading container output lab_id=%s container_id=%s exec_id=%s error=%s",
                lab_id,
                container.id,
                exec_id,
                exc,
                exc_info=True,
            )
            raise

    async def pump_browser_to_container() -> None:
        try:
            while True:
                message = await websocket.receive()
                if message["type"] == "websocket.disconnect":
                    logger.info(
                        "Browser disconnected lab_id=%s container_id=%s exec_id=%s client=%s",
                        lab_id,
                        container.id,
                        exec_id,
                        client_host,
                    )
                    break

                payload = message.get("bytes")
                if payload is None and message.get("text") is not None:
                    payload = message["text"].encode("utf-8")
                if not payload:
                    continue

                await loop.run_in_executor(None, sock.sendall, payload)
        except WebSocketDisconnect:
            logger.info(
                "WebSocket disconnect received lab_id=%s container_id=%s exec_id=%s client=%s",
                lab_id,
                container.id,
                exec_id,
                client_host,
            )
        except (OSError, ConnectionError) as exc:
            logger.warning(
                "Container write stream error lab_id=%s container_id=%s exec_id=%s error=%s",
                lab_id,
                container.id,
                exec_id,
                exc,
                exc_info=True,
            )
        except Exception as exc:
            logger.error(
                "Unexpected error writing to container stdin lab_id=%s container_id=%s exec_id=%s error=%s",
                lab_id,
                container.id,
                exec_id,
                exc,
                exc_info=True,
            )
            raise

    read_task = asyncio.create_task(pump_container_to_browser())
    write_task = asyncio.create_task(pump_browser_to_container())

    try:
        done, pending = await asyncio.wait(
            {read_task, write_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in done:
            if task.exception():
                logger.error(
                    "Terminal stream task failed lab_id=%s container_id=%s exec_id=%s error=%s",
                    lab_id,
                    container.id,
                    exec_id,
                    task.exception(),
                    exc_info=task.exception(),
                )
    finally:
        logger.info(
            "Closing terminal session lab_id=%s container_id=%s exec_id=%s client=%s",
            lab_id,
            container.id,
            exec_id,
            client_host,
        )

        for task in (read_task, write_task):
            task.cancel()
        await asyncio.gather(read_task, write_task, return_exceptions=True)

        if sock is not None:
            try:
                sock.close()
            except OSError as exc:
                logger.warning(
                    "Error closing exec socket lab_id=%s exec_id=%s error=%s",
                    lab_id,
                    exec_id,
                    exc,
                )

        try:
            await websocket.close()
        except Exception as exc:
            logger.debug(
                "WebSocket already closed lab_id=%s client=%s error=%s",
                lab_id,
                client_host,
                exc,
            )
