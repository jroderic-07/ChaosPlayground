# ChaosPlayground

ChaosPlayground is an interactive, sandbox-style simulation tool designed for software and systems engineers to safely practice DevOps, Site Reliability Engineering (SRE), and operations workflows. By intentionally injecting controlled infrastructure failures, performance bottlenecks, and service outages, the platform creates a realistic "war room" environment.

*   **The Aim:** To bridge the gap between theoretical system design and hands-on crisis management. It provides aspiring and junior SREs with a safe, local environment to build troubleshooting muscle memory, interpret chaotic metrics, and build a verifiable portfolio of incident resolution experience.

---

## The Tech Stack

The architecture is deliberately lean, avoiding heavy JavaScript frameworks in favor of a fast, hyper-responsive, and maintainable backend-driven approach.

### Python
*   **Role:** Core Application Logic & Simulation Engine
*   **Why it's used:** Python serves as the backbone for orchestrating the chaos injection scripts, managing system state, and handling background worker tasks that simulate infrastructure loads or failures.

### FastAPI
*   **Role:** High-Performance Backend API
*   **Why it's used:** FastAPI delivers production-grade speed and asynchronous capabilities out of the box. It efficiently handles real-time telemetry data streams from the simulated "outages" and provides automatic, type-safe interactive documentation via OpenAPI.

### HTMX
*   **Role:** Dynamic, Single-Page Frontend Experience
*   **Why it's used:** HTMX allows the application to achieve slick, real-time UI updates (like live-updating metrics dashboards and interactive terminal logs) directly via HTML attributes. By swapping server-rendered HTML fragments over AJAX and WebSockets, it eliminates the need for complex, heavy frontend build steps like React or Vue.

---

## Getting Started

### Prerequisites

*   Python 3.10 or newer
*   `pip` (bundled with Python)

On Debian/Ubuntu, if `python3 -m venv` fails, install the venv package first:

```bash
sudo apt install python3-venv
```

### Setup

Clone the repository and create a virtual environment:

```bash
git clone <repository-url>
cd ChaosPlayground
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the application

Start the development server with auto-reload:

```bash
uvicorn main:app --reload
```

The app will be available at:

*   **Dashboard:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
*   **API docs (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
*   **Alternative API docs (ReDoc):** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

To bind to a different host or port:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

### Project layout

```
ChaosPlayground/
├── app/              # Application package (routers, core logic)
├── static/           # CSS, JS, and other static assets
├── templates/        # Jinja2 HTML templates
├── main.py           # FastAPI entry point
└── requirements.txt  # Python dependencies
```
