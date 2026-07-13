from labs.base import LabMetadata
from labs.registry import LabSolution, lab_registry


def _manifest_to_metadata(manifest) -> LabMetadata:
    return LabMetadata(
        id=manifest.id,
        title=manifest.title,
        description=manifest.description,
        category=manifest.category,
        difficulty=manifest.difficulty,
    )


def get_all_lab_metadata() -> list[LabMetadata]:
    return [_manifest_to_metadata(manifest) for manifest in lab_registry.list_manifests()]


def get_lab_metadata(lab_id: str) -> LabMetadata | None:
    manifest = lab_registry.get_manifest(lab_id)
    if manifest is None:
        return None
    return _manifest_to_metadata(manifest)


def get_lab_solution(lab_id: str) -> LabSolution | None:
    manifest = lab_registry.get_manifest(lab_id)
    if manifest is None:
        return None
    return manifest.solution


def get_lab_categories():
    return lab_registry.list_categories()
