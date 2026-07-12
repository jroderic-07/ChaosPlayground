from dataclasses import dataclass

from docker.errors import DockerException, ImageNotFound, NotFound

from labs.base import BaseChaosLab


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
            import docker

            self._client = docker.from_env()
        return self._client

    def is_active(self, lab_id: str) -> bool:
        return lab_id in self._sessions

    def start(self, lab: BaseChaosLab) -> SandboxSession:
        lab_id = lab.metadata.id
        client = self._get_client()
        container_name = f"chaosplayground-{lab_id}"

        try:
            existing = client.containers.get(container_name)
            existing.remove(force=True)
        except NotFound:
            pass

        try:
            client.images.get(lab.image_name)
        except ImageNotFound:
            client.images.pull(lab.image_name)

        container = client.containers.run(
            image=lab.image_name,
            name=container_name,
            detach=True,
            tty=True,
            stdin_open=True,
            labels={"chaosplayground.lab_id": lab_id},
        )
        lab.inject_chaos(container)

        session = SandboxSession(container_id=container.id, lab_id=lab_id)
        self._sessions[lab_id] = session
        return session

    def get_session(self, lab_id: str) -> SandboxSession | None:
        return self._sessions.get(lab_id)


sandbox_manager = SandboxManager()
