from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="ChaosPlayground",
    description="Interactive SRE chaos engineering sandbox",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "templates")

LABS = [
    {"id": "latency-spike", "name": "Latency Spike", "status": "idle"},
    {"id": "memory-leak", "name": "Memory Leak", "status": "idle"},
    {"id": "cascade-failure", "name": "Cascade Failure", "status": "idle"},
]


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context={
            "labs": LABS,
            "active_lab": None,
            "page_title": "Home",
            "is_home": True,
        },
    )


@app.get("/labs/{lab_id}", response_class=HTMLResponse)
async def lab_detail(request: Request, lab_id: str) -> HTMLResponse:
    lab = next((item for item in LABS if item["id"] == lab_id), None)
    if lab is None:
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
