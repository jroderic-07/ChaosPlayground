from labs.base import BaseChaosLab
from labs.scenarios import DiskExhaustionLab, HighCpuZombieLab

LAB_REGISTRY: dict[str, BaseChaosLab] = {
    "disk-exhaustion": DiskExhaustionLab(),
    "high-cpu-zombie": HighCpuZombieLab(),
}


def get_lab(lab_id: str) -> BaseChaosLab | None:
    return LAB_REGISTRY.get(lab_id)


def list_labs() -> list[BaseChaosLab]:
    return list(LAB_REGISTRY.values())
