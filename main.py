from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.core.htmx import is_htmx_request
from app.core.sandbox import stop_sandboxes_on_navigation
from app.core.labs import get_all_lab_metadata
from app.core.logging_config import setup_logging
from app.core.templates import templates
from app.routers import labs, terminal

BASE_DIR = Path(__file__).resolve().parent

setup_logging()

app = FastAPI(
    title="ChaosPlayground",
    description="Interactive SRE chaos engineering sandbox",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(labs.router)
app.include_router(terminal.router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    stop_sandboxes_on_navigation(request)

    if is_htmx_request(request):
        return templates.TemplateResponse(
            request=request,
            name="partials/home_panel.html",
        )

    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context={
            "labs": get_all_lab_metadata(),
            "active_lab": None,
            "page_title": "Home",
            "is_home": True,
        },
    )
