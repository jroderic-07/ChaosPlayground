import json
import logging
from pathlib import Path

from pydantic import BaseModel, Field

from labs.base import BaseChaosLab, LabMetadata
from labs.scenarios import (
    DiskExhaustionLab,
    HighCpuZombieLab,
    PlaceholderLab,
)

logger = logging.getLogger("chaosplayground.registry")

CATEGORY_ORDER = [
    "Linux Fundamentals",
    "Database Ops",
    "Middleware (WebLogic)",
    "Networking",
]

DIFFICULTY_ORDER = {"Easy": 0, "Medium": 1, "Hard": 2}


class LabSolution(BaseModel):
    reasoning: str
    commands: list[str]


class LabManifest(BaseModel):
    id: str
    title: str
    description: str
    category: str
    difficulty: str
    scenario: str = Field(
        default="placeholder",
        description="Key mapping to a Python chaos scenario implementation.",
    )
    solution: LabSolution


class LabCategory(BaseModel):
    name: str
    labs: list[LabManifest]


class ManifestBackedLab(BaseChaosLab):
    """Combines a JSON manifest with a Python scenario implementation."""

    def __init__(self, manifest: LabManifest, backend: BaseChaosLab) -> None:
        self._manifest = manifest
        self._backend = backend

    @property
    def metadata(self) -> LabMetadata:
        return LabMetadata(
            id=self._manifest.id,
            title=self._manifest.title,
            description=self._manifest.description,
            category=self._manifest.category,
            difficulty=self._manifest.difficulty,
        )

    @property
    def solution(self) -> LabSolution:
        return self._manifest.solution

    @property
    def image_name(self) -> str:
        return self._backend.image_name

    def inject_chaos(self, container) -> None:
        self._backend.inject_chaos(container)

    def verify_fix(self, container) -> bool:
        return self._backend.verify_fix(container)

    @property
    def verification_success_message(self) -> str:
        return self._backend.verification_success_message

    @property
    def verification_failure_message(self) -> str:
        return self._backend.verification_failure_message


SCENARIO_BACKENDS: dict[str, type[BaseChaosLab]] = {
    "disk_exhaustion": DiskExhaustionLab,
    "zombie_process": HighCpuZombieLab,
    "placeholder": PlaceholderLab,
}


class LabRegistry:
    def __init__(self, labs_dir: Path | None = None) -> None:
        self._labs_dir = labs_dir or Path(__file__).resolve().parent
        self._manifests: dict[str, LabManifest] = {}
        self._labs: dict[str, ManifestBackedLab] = {}
        self._discover_manifests()
        self._build_lab_instances()

    def _discover_manifests(self) -> None:
        manifests_dir = self._labs_dir / "manifests"
        if not manifests_dir.exists():
            logger.warning("Lab manifests directory missing path=%s", manifests_dir)
            return

        for manifest_path in sorted(manifests_dir.glob("**/*.json")):
            try:
                raw = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest = LabManifest.model_validate(raw)
            except (json.JSONDecodeError, ValueError) as exc:
                logger.error(
                    "Invalid lab manifest path=%s error=%s",
                    manifest_path,
                    exc,
                    exc_info=True,
                )
                continue

            if manifest.id in self._manifests:
                logger.error(
                    "Duplicate lab id=%s in manifest path=%s — skipping",
                    manifest.id,
                    manifest_path,
                )
                continue

            self._manifests[manifest.id] = manifest
            logger.debug(
                "Discovered lab manifest id=%s category=%s difficulty=%s path=%s",
                manifest.id,
                manifest.category,
                manifest.difficulty,
                manifest_path,
            )

        logger.info(
            "Lab manifest discovery complete count=%d categories=%s",
            len(self._manifests),
            sorted({manifest.category for manifest in self._manifests.values()}),
        )

    def _build_lab_instances(self) -> None:
        for manifest in self._manifests.values():
            backend_cls = SCENARIO_BACKENDS.get(manifest.scenario, PlaceholderLab)
            if manifest.scenario not in SCENARIO_BACKENDS:
                logger.warning(
                    "Unknown scenario key=%s for lab id=%s — using placeholder",
                    manifest.scenario,
                    manifest.id,
                )
            backend = backend_cls()
            self._labs[manifest.id] = ManifestBackedLab(manifest, backend)

    def get_manifest(self, lab_id: str) -> LabManifest | None:
        return self._manifests.get(lab_id)

    def get_lab(self, lab_id: str) -> ManifestBackedLab | None:
        return self._labs.get(lab_id)

    def list_manifests(self) -> list[LabManifest]:
        return list(self._manifests.values())

    def list_categories(self) -> list[LabCategory]:
        grouped: dict[str, list[LabManifest]] = {name: [] for name in CATEGORY_ORDER}

        for manifest in self._manifests.values():
            grouped.setdefault(manifest.category, []).append(manifest)

        categories: list[LabCategory] = []
        for name in CATEGORY_ORDER:
            labs = grouped.get(name, [])
            if not labs:
                continue
            labs.sort(key=lambda lab: DIFFICULTY_ORDER.get(lab.difficulty, 99))
            categories.append(LabCategory(name=name, labs=labs))

        for name, labs in grouped.items():
            if name in CATEGORY_ORDER or not labs:
                continue
            labs.sort(key=lambda lab: DIFFICULTY_ORDER.get(lab.difficulty, 99))
            categories.append(LabCategory(name=name, labs=labs))

        return categories


lab_registry = LabRegistry()


def get_lab(lab_id: str) -> ManifestBackedLab | None:
    return lab_registry.get_lab(lab_id)


def list_labs() -> list[ManifestBackedLab]:
    return list(lab_registry._labs.values())
