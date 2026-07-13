from labs.base import BaseChaosLab, DockerContainer, LabMetadata, exec_exit_code

DISK_EXHAUSTION_LOG_PATH = "/var/log/app/debug_trace.log"
CPU_ZOMBIE_PATTERN = "while true; do true; done"
PLACEHOLDER_FLAG_PATH = "/tmp/chaos-placeholder"


class DiskExhaustionLab(BaseChaosLab):
    @property
    def metadata(self) -> LabMetadata:
        raise NotImplementedError("Metadata is provided by lab manifest")

    @property
    def image_name(self) -> str:
        return "alpine:latest"

    def inject_chaos(self, container: DockerContainer) -> None:
        container.exec_run(
            [
                "sh",
                "-c",
                (
                    f"mkdir -p /var/log/app && "
                    f"dd if=/dev/zero of={DISK_EXHAUSTION_LOG_PATH} bs=1M count=300 2>/dev/null"
                ),
            ]
        )

    def verify_fix(self, container: DockerContainer) -> bool:
        result = container.exec_run(["test", "!", "-f", DISK_EXHAUSTION_LOG_PATH])
        return exec_exit_code(result) == 0

    @property
    def verification_success_message(self) -> str:
        return "Task Completed! The debug trace log has been removed and disk pressure is relieved."

    @property
    def verification_failure_message(self) -> str:
        return "Still broken — /var/log/app/debug_trace.log is still present. Delete it and try again."


class HighCpuZombieLab(BaseChaosLab):
    @property
    def metadata(self) -> LabMetadata:
        raise NotImplementedError("Metadata is provided by lab manifest")

    @property
    def image_name(self) -> str:
        return "alpine:latest"

    def inject_chaos(self, container: DockerContainer) -> None:
        container.exec_run(
            [
                "sh",
                "-c",
                f'nohup sh -c "{CPU_ZOMBIE_PATTERN}" > /dev/null 2>&1 &',
            ]
        )

    def verify_fix(self, container: DockerContainer) -> bool:
        result = container.exec_run(
            [
                "sh",
                "-c",
                f"ps aux | grep -v grep | grep -q '{CPU_ZOMBIE_PATTERN}'",
            ]
        )
        return exec_exit_code(result) != 0

    @property
    def verification_success_message(self) -> str:
        return "Task Completed! The rogue CPU loop has been terminated."

    @property
    def verification_failure_message(self) -> str:
        return "Still broken — a zombie shell loop is still running. Find and kill it, then try again."


class PlaceholderLab(BaseChaosLab):
    @property
    def metadata(self) -> LabMetadata:
        raise NotImplementedError("Metadata is provided by lab manifest")

    @property
    def image_name(self) -> str:
        return "alpine:latest"

    def inject_chaos(self, container: DockerContainer) -> None:
        container.exec_run(
            [
                "sh",
                "-c",
                f"echo 'Scenario placeholder active' > {PLACEHOLDER_FLAG_PATH}",
            ]
        )

    def verify_fix(self, container: DockerContainer) -> bool:
        result = container.exec_run(["test", "!", "-f", PLACEHOLDER_FLAG_PATH])
        return exec_exit_code(result) == 0

    @property
    def verification_success_message(self) -> str:
        return "Task Completed! Placeholder scenario cleared."

    @property
    def verification_failure_message(self) -> str:
        return "Still broken — remove /tmp/chaos-placeholder to complete this placeholder lab."
