from docker.errors import DockerException
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.htmx import is_htmx_request
from app.core.labs import get_all_lab_metadata, get_lab_metadata
from app.core.sandbox import sandbox_manager
from app.core.templates import templates
from labs.registry import get_lab

router = APIRouter(tags=["labs"])


@router.get("/labs/{lab_id}", response_class=HTMLResponse)
async def lab_detail(request: Request, lab_id: str) -> HTMLResponse:
    lab = get_lab(lab_id)
    metadata = get_lab_metadata(lab_id)

    if lab is None or metadata is None:
        if is_htmx_request(request):
            return templates.TemplateResponse(
                request=request,
                name="partials/lab_not_found.html",
                context={"lab_id": lab_id},
                status_code=404,
            )

        return templates.TemplateResponse(
            request=request,
            name="base.html",
            context={
                "labs": get_all_lab_metadata(),
                "active_lab": None,
                "page_title": "Lab Not Found",
                "is_home": False,
                "error": f"Lab '{lab_id}' does not exist.",
            },
            status_code=404,
        )

    if is_htmx_request(request):
        return templates.TemplateResponse(
            request=request,
            name="partials/lab_panel.html",
            context={
                "lab": metadata,
                "sandbox_active": sandbox_manager.is_active(lab_id),
            },
        )

    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context={
            "labs": get_all_lab_metadata(),
            "active_lab": metadata,
            "page_title": metadata.title,
            "is_home": False,
            "sandbox_active": sandbox_manager.is_active(lab_id),
        },
    )


@router.post("/api/labs/{lab_id}/start", response_class=HTMLResponse)
async def start_lab(request: Request, lab_id: str) -> HTMLResponse:
    lab = get_lab(lab_id)
    metadata = get_lab_metadata(lab_id)

    if lab is None or metadata is None:
        return templates.TemplateResponse(
            request=request,
            name="partials/lab_start_error.html",
            context={"message": f"Lab '{lab_id}' does not exist."},
            status_code=404,
        )

    try:
        sandbox_manager.start(lab)
    except DockerException as exc:
        return templates.TemplateResponse(
            request=request,
            name="partials/lab_start_error.html",
            context={
                "message": (
                    "Failed to provision sandbox. Ensure Docker is running and accessible. "
                    f"({exc})"
                ),
            },
            status_code=500,
        )

    return templates.TemplateResponse(
        request=request,
        name="partials/lab_started.html",
        context={"lab": metadata},
    )
