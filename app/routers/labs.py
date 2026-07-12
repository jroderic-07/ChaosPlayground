from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.htmx import is_htmx_request
from app.core.labs import LABS, get_lab
from app.core.templates import templates

router = APIRouter(tags=["labs"])


@router.get("/labs/{lab_id}", response_class=HTMLResponse)
async def lab_detail(request: Request, lab_id: str) -> HTMLResponse:
    lab = get_lab(lab_id)

    if lab is None:
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
                "labs": LABS,
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
            context={"lab": lab},
        )

    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context={
            "labs": LABS,
            "active_lab": lab,
            "page_title": lab["name"],
            "is_home": False,
        },
    )
