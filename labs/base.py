from abc import ABC, abstractmethod
from typing import Any, Protocol

from pydantic import BaseModel


class LabMetadata(BaseModel):
    id: str
    title: str
    description: str
    difficulty: str


class DockerContainer(Protocol):
    """Subset of the python-docker Container API used by chaos labs."""

    def exec_run(
        self,
        cmd: str | list[str],
        detach: bool = False,
        tty: bool = False,
        stdin: bool = False,
        privileged: bool = False,
        user: str = "",
        environment: dict[str, str] | list[str] | None = None,
        workdir: str | None = None,
    ) -> Any:
        ...


def exec_exit_code(result: Any) -> int:
    if hasattr(result, "exit_code"):
        return int(result.exit_code)
    return int(result[0])


class BaseChaosLab(ABC):
    @property
    @abstractmethod
    def metadata(self) -> LabMetadata:
        """Return identifying metadata for this lab scenario."""

    @property
    @abstractmethod
    def image_name(self) -> str:
        """Return the Docker image used to provision the lab container."""

    @abstractmethod
    def inject_chaos(self, container: DockerContainer) -> None:
        """Execute chaos injection commands inside the lab container."""

    @abstractmethod
    def verify_fix(self, container: DockerContainer) -> bool:
        """Return True when the operator has resolved the injected issue."""

    @property
    def verification_success_message(self) -> str:
        return f"Task Completed! {self.metadata.title} has been resolved."

    @property
    def verification_failure_message(self) -> str:
        return "Still broken — keep investigating and try again."
