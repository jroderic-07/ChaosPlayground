from labs.base import BaseChaosLab, DockerContainer, LabMetadata, exec_exit_code

DISK_EXHAUSTION_LOG_PATH = "/var/log/app/debug_trace.log"
CPU_ZOMBIE_PATTERN = "while true; do true; done"


class DiskExhaustionLab(BaseChaosLab):
    @property
    def metadata(self) -> LabMetadata:
        return LabMetadata(
            id="disk-exhaustion",
            title="Disk Exhaustion",
            description=(
                "An unmanaged logging process has written a 300MB debug trace file, "
                "filling the container filesystem and threatening service stability."
            ),
            difficulty="beginner",
        )

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


class HighCpuZombieLab(BaseChaosLab):
    @property
    def metadata(self) -> LabMetadata:
        return LabMetadata(
            id="high-cpu-zombie",
            title="High CPU Zombie",
            description=(
                "A rogue background shell loop is consuming CPU inside the container, "
                "mimicking a runaway process left behind after a bad deploy."
            ),
            difficulty="intermediate",
        )

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
