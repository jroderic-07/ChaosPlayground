from labs.base import LabMetadata
from labs.registry import get_lab as get_registry_lab, list_labs


def get_all_lab_metadata() -> list[LabMetadata]:
    return [lab.metadata for lab in list_labs()]


def get_lab_metadata(lab_id: str) -> LabMetadata | None:
    lab = get_registry_lab(lab_id)
    return lab.metadata if lab else None
