from dataclasses import dataclass

from docker.errors import DockerException, ImageNotFound, NotFound
from fastapi import Request

from app.core.htmx import is_htmx_request
from app.core.logging_config import get_logger
from labs.base import BaseChaosLab

logger = get_logger("sandbox")


@dataclass
class SandboxSession:
    container_id: str
    lab_id: str


class SandboxManager:
    def __init__(self) -> None:
        self._sessions: dict[str, SandboxSession] = {}
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import docker

                self._client = docker.from_env()
                logger.info("Docker client initialized successfully")
            except DockerException as exc:
                logger.error(
                    "Failed to initialize Docker client — is the Docker daemon running and accessible? error=%s",
                    exc,
                    exc_info=True,
                )
                raise
        return self._client

    def is_active(self, lab_id: str) -> bool:
        active = lab_id in self._sessions
        logger.debug("Sandbox active check lab_id=%s active=%s", lab_id, active)
        return active

    def start(self, lab: BaseChaosLab) -> SandboxSession:
        lab_id = lab.metadata.id
        image_name = lab.image_name
        container_name = f"chaosplayground-{lab_id}"

        logger.info(
            "Starting sandbox lab_id=%s image=%s container_name=%s",
            lab_id,
            image_name,
            container_name,
        )

        client = self._get_client()

        try:
            existing = client.containers.get(container_name)
            logger.warning(
                "Removing pre-existing container before start lab_id=%s container_id=%s",
                lab_id,
                existing.id,
            )
            existing.remove(force=True)
        except NotFound:
            logger.debug("No pre-existing container found lab_id=%s name=%s", lab_id, container_name)
        except DockerException as exc:
            logger.error(
                "Failed while checking for pre-existing container lab_id=%s name=%s error=%s",
                lab_id,
                container_name,
                exc,
                exc_info=True,
            )
            raise

        try:
            client.images.get(image_name)
            logger.debug("Image already present lab_id=%s image=%s", lab_id, image_name)
        except ImageNotFound:
            logger.info("Pulling image lab_id=%s image=%s", lab_id, image_name)
            try:
                client.images.pull(image_name)
                logger.info("Image pull complete lab_id=%s image=%s", lab_id, image_name)
            except DockerException as exc:
                logger.error(
                    "Image pull failed lab_id=%s image=%s error=%s",
                    lab_id,
                    image_name,
                    exc,
                    exc_info=True,
                )
                raise

        try:
            container = client.containers.run(
                image=image_name,
                name=container_name,
                detach=True,
                tty=True,
                stdin_open=True,
                labels={"chaosplayground.lab_id": lab_id},
            )
            logger.info(
                "Container created lab_id=%s container_id=%s name=%s status=%s",
                lab_id,
                container.id,
                container_name,
                container.status,
            )
        except DockerException as exc:
            logger.error(
                "Container creation failed lab_id=%s image=%s name=%s error=%s",
                lab_id,
                image_name,
                container_name,
                exc,
                exc_info=True,
            )
            raise

        try:
            lab.inject_chaos(container)
            logger.info("Chaos injected successfully lab_id=%s container_id=%s", lab_id, container.id)
        except Exception as exc:
            logger.error(
                "Chaos injection failed lab_id=%s container_id=%s error=%s — removing container",
                lab_id,
                container.id,
                exc,
                exc_info=True,
            )
            try:
                container.remove(force=True)
            except DockerException as cleanup_exc:
                logger.error(
                    "Failed to remove container after chaos injection error lab_id=%s container_id=%s error=%s",
                    lab_id,
                    container.id,
                    cleanup_exc,
                    exc_info=True,
                )
            raise

        session = SandboxSession(container_id=container.id, lab_id=lab_id)
        self._sessions[lab_id] = session
        logger.info(
            "Sandbox session registered lab_id=%s container_id=%s active_sessions=%d",
            lab_id,
            container.id,
            len(self._sessions),
        )
        return session

    def get_session(self, lab_id: str) -> SandboxSession | None:
        session = self._sessions.get(lab_id)
        if session is None:
            logger.warning(
                "No sandbox session found lab_id=%s active_sessions=%s",
                lab_id,
                list(self._sessions.keys()) or "none",
            )
        return session

    def get_container(self, lab_id: str):
        session = self.get_session(lab_id)
        if session is None:
            return None

        try:
            container = self._get_client().containers.get(session.container_id)
        except NotFound:
            logger.error(
                "Container missing for active session lab_id=%s container_id=%s — session may be stale, removing",
                lab_id,
                session.container_id,
            )
            self._sessions.pop(lab_id, None)
            return None
        except DockerException as exc:
            logger.error(
                "Docker API error while fetching container lab_id=%s container_id=%s error=%s",
                lab_id,
                session.container_id,
                exc,
                exc_info=True,
            )
            return None

        container.reload()
        if container.status != "running":
            logger.error(
                "Container is not running lab_id=%s container_id=%s status=%s",
                lab_id,
                container.id,
                container.status,
            )
            return None

        logger.debug(
            "Container resolved lab_id=%s container_id=%s status=%s",
            lab_id,
            container.id,
            container.status,
        )
        return container

    def stop(self, lab_id: str) -> None:
        session = self._sessions.pop(lab_id, None)
        if session is None:
            logger.debug("Stop requested but no active session lab_id=%s", lab_id)
            return

        try:
            container = self._get_client().containers.get(session.container_id)
            container.remove(force=True)
            logger.info(
                "Sandbox stopped lab_id=%s container_id=%s",
                lab_id,
                session.container_id,
            )
        except NotFound:
            logger.warning(
                "Container already removed during stop lab_id=%s container_id=%s",
                lab_id,
                session.container_id,
            )
        except DockerException as exc:
            logger.error(
                "Failed to stop sandbox lab_id=%s container_id=%s error=%s",
                lab_id,
                session.container_id,
                exc,
                exc_info=True,
            )

    def stop_all(self) -> None:
        if not self._sessions:
            return

        active_labs = list(self._sessions.keys())
        logger.info("Stopping all active sandboxes count=%d labs=%s", len(active_labs), active_labs)
        for lab_id in active_labs:
            self.stop(lab_id)

    def list_active_lab_ids(self) -> list[str]:
        return list(self._sessions.keys())


def stop_sandboxes_on_navigation(request: Request, target_lab_id: str | None = None) -> None:
    """Stop running sandboxes when the user leaves an active lab view."""
    if not is_htmx_request(request):
        sandbox_manager.stop_all()
        return

    current_url = request.headers.get("HX-Current-URL", "").rstrip("/")

    if target_lab_id is None:
        if sandbox_manager.list_active_lab_ids():
            logger.info("Navigation to home — stopping active sandboxes")
        sandbox_manager.stop_all()
        return

    if current_url.endswith(f"/labs/{target_lab_id}"):
        logger.debug("Navigation within same lab view lab_id=%s — keeping sandbox", target_lab_id)
        return

    if sandbox_manager.list_active_lab_ids():
        logger.info(
            "Navigation away from lab to lab_id=%s current_url=%s — stopping active sandboxes",
            target_lab_id,
            current_url or "unknown",
        )
    sandbox_manager.stop_all()


sandbox_manager = SandboxManager()
