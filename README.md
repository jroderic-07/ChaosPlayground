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
