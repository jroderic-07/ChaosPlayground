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
*   Docker (required for lab sandboxes and the interactive terminal)

On Debian/Ubuntu, if `python3 -m venv` fails, install the venv package first:

```bash
sudo apt install python3-venv
```

### Docker setup

Lab sandboxes provision real containers via the Docker API. Docker must be installed, running, and accessible from the same environment where you run `uvicorn`.

Verify Docker is working before starting the app:

```bash
ls -la /var/run/docker.sock   # socket should exist
docker ps                     # should succeed without sudo
```

Choose **one** of the two setups below. Do not mix Docker Desktop socket forwarding with a separately installed `docker.io` daemon unless you know what you are doing.

---

#### Option A: Docker Desktop (Windows, macOS, or WSL)

Use this if you already have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed on Windows or macOS.

**On Windows with WSL2 (recommended for this project)**

1. Start **Docker Desktop** on Windows and wait until it shows **Running**.
2. Open **Docker Desktop → Settings → General** and ensure **Use the WSL 2 based engine** is enabled.
3. Open **Settings → Resources → WSL Integration**:
   - Enable **Enable integration with my default WSL distro**
   - Toggle **ON** for your distro (e.g. Ubuntu)
4. Click **Apply & Restart**.
5. From Windows PowerShell or CMD, restart WSL:

   ```cmd
   wsl --shutdown
   ```

6. Reopen your WSL terminal and verify:

   ```bash
   ls -la /var/run/docker.sock
   docker ps
   ```

If `docker` prints *"activate the WSL integration in Docker Desktop settings"*, the integration step above was not completed or WSL was not restarted.

**On macOS**

Install and start Docker Desktop, then verify `docker ps` works in your terminal.

---

#### Option B: Native Docker inside WSL / Linux

Use this if you want Docker running directly inside your WSL distro (or native Linux) without Docker Desktop.

**Install and start the daemon (Debian/Ubuntu/WSL)**

```bash
sudo apt update
sudo apt install -y docker.io
sudo service docker start
```

**Allow your user to run Docker without sudo**

```bash
sudo usermod -aG docker $USER
```

Reload your group membership — open a new terminal, log out of WSL and back in, or run:

```bash
newgrp docker
```

**Verify**

```bash
groups                    # should include "docker"
ls -la /var/run/docker.sock
docker ps                 # should succeed without sudo
```

**Start Docker automatically (optional)**

If `docker ps` fails after reopening WSL, the daemon may not be running:

```bash
sudo service docker start
```

To start Docker whenever WSL launches, add this to your `~/.bashrc` or `~/.profile`:

```bash
# Start Docker daemon if not already running (native WSL install)
if ! pgrep -x dockerd > /dev/null 2>&1; then
    sudo service docker start
fi
```

Note: this prompts for your password on first shell open unless you configure passwordless `service docker start` via `sudoers`.

---

#### Troubleshooting Docker errors

| Symptom | Likely cause | Fix |
|---|---|---|
| `FileNotFoundError: No such file or directory` on `/var/run/docker.sock` | Docker daemon not running, or Docker Desktop WSL integration not enabled | Follow Option A or B above, then confirm `ls /var/run/docker.sock` succeeds |
| `PermissionError(13, 'Permission denied')` on `/var/run/docker.sock` | Socket exists but your user is not in the `docker` group | `sudo usermod -aG docker $USER`, then `newgrp docker` |
| `docker: command could not be found in this WSL 2 distro` | Docker Desktop installed on Windows but WSL integration disabled | Enable WSL Integration in Docker Desktop settings |

Do **not** use `sudo uvicorn` or `chmod 666 /var/run/docker.sock` as workarounds.

After Docker is working, restart the application:

```bash
uvicorn main:app --reload
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
├── labs/             # Chaos lab scenarios and registry
├── static/           # CSS, JS, and other static assets
├── templates/        # Jinja2 HTML templates
├── main.py           # FastAPI entry point
└── requirements.txt  # Python dependencies
```
