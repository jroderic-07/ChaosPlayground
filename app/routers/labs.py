from docker.errors import DockerException
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.htmx import is_htmx_request
from app.core.labs import get_all_lab_metadata, get_lab_metadata
from app.core.logging_config import get_logger
from app.core.sandbox import sandbox_manager, stop_sandboxes_on_navigation
from app.core.templates import templates
from labs.registry import get_lab

logger = get_logger("labs")
router = APIRouter(tags=["labs"])


@router.get("/labs/{lab_id}", response_class=HTMLResponse)
async def lab_detail(request: Request, lab_id: str) -> HTMLResponse:
    stop_sandboxes_on_navigation(request, lab_id)

    lab = get_lab(lab_id)
    metadata = get_lab_metadata(lab_id)

    if lab is None or metadata is None:
        logger.warning("Lab detail requested for unknown lab_id=%s", lab_id)
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
        logger.debug(
            "Serving lab panel fragment lab_id=%s sandbox_active=%s",
            lab_id,
            sandbox_manager.is_active(lab_id),
        )
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
    logger.info("Sandbox start requested lab_id=%s client=%s", lab_id, request.client.host if request.client else "unknown")

    lab = get_lab(lab_id)
    metadata = get_lab_metadata(lab_id)

    if lab is None or metadata is None:
        logger.error("Sandbox start failed — lab not found lab_id=%s", lab_id)
        return templates.TemplateResponse(
            request=request,
            name="partials/lab_start_error.html",
            context={"message": f"Lab '{lab_id}' does not exist."},
            status_code=404,
        )

    try:
        session = sandbox_manager.start(lab)
        logger.info(
            "Sandbox start succeeded lab_id=%s container_id=%s",
            lab_id,
            session.container_id,
        )
    except DockerException as exc:
        logger.error(
            "Sandbox start failed — Docker error lab_id=%s image=%s error=%s",
            lab_id,
            lab.image_name,
            exc,
            exc_info=True,
        )
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
    except Exception as exc:
        logger.error(
            "Sandbox start failed — unexpected error lab_id=%s error=%s",
            lab_id,
            exc,
            exc_info=True,
        )
        return templates.TemplateResponse(
            request=request,
            name="partials/lab_start_error.html",
            context={
                "message": (
                    "Failed to provision sandbox due to an unexpected error. "
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


@router.post("/api/labs/{lab_id}/verify", response_class=HTMLResponse)
async def verify_lab(request: Request, lab_id: str) -> HTMLResponse:
    logger.info("Verification requested lab_id=%s client=%s", lab_id, request.client.host if request.client else "unknown")

    lab = get_lab(lab_id)
    metadata = get_lab_metadata(lab_id)

    if lab is None or metadata is None:
        logger.error("Verification failed — lab not found lab_id=%s", lab_id)
        return templates.TemplateResponse(
            request=request,
            name="partials/verify_response.html",
            context={
                "passed": False,
                "success_message": "",
                "failure_message": f"Lab '{lab_id}' does not exist.",
            },
            status_code=404,
        )

    container = sandbox_manager.get_container(lab_id)
    if container is None:
        logger.error(
            "Verification failed — no active sandbox lab_id=%s active_sessions=%s",
            lab_id,
            sandbox_manager.list_active_lab_ids(),
        )
        return templates.TemplateResponse(
            request=request,
            name="partials/verify_response.html",
            context={
                "passed": False,
                "success_message": "",
                "failure_message": "Sandbox is not active. Start the lab before verifying.",
            },
            status_code=400,
        )

    try:
        passed = lab.verify_fix(container)
    except Exception as exc:
        logger.error(
            "Verification check raised an error lab_id=%s container_id=%s error=%s",
            lab_id,
            container.id,
            exc,
            exc_info=True,
        )
        return templates.TemplateResponse(
            request=request,
            name="partials/verify_response.html",
            context={
                "passed": False,
                "success_message": "",
                "failure_message": f"Verification check failed unexpectedly. ({exc})",
            },
            status_code=500,
        )

    logger.info(
        "Verification complete lab_id=%s container_id=%s passed=%s",
        lab_id,
        container.id,
        passed,
    )

    return templates.TemplateResponse(
        request=request,
        name="partials/verify_response.html",
        context={
            "passed": passed,
            "success_message": lab.verification_success_message,
            "failure_message": lab.verification_failure_message,
        },
    )
