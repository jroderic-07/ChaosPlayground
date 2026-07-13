from labs.base import LabMetadata
from labs.registry import lab_registry


def get_all_lab_metadata() -> list[LabMetadata]:
    return [
        LabMetadata(**manifest.model_dump())
        for manifest in lab_registry.list_manifests()
    ]


def get_lab_metadata(lab_id: str) -> LabMetadata | None:
    manifest = lab_registry.get_manifest(lab_id)
    if manifest is None:
        return None
    return LabMetadata(**manifest.model_dump())


def get_lab_categories():
    return lab_registry.list_categories()
