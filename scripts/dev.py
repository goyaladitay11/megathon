#!/usr/bin/env python3
"""Run the Green Home Twin frontend and API as one checked local development stack.

Usage (from the repository root): python3 scripts/dev.py
The script will NEVER kill processes it did not start.
"""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
SAMPLE = {
    "property_id": "LOCAL-STARTUP-CHECK",
    "property_type": "terraced",
    "age": 1910,
    "floor_area_m2": 92,
    "region": "North West",
    "bedrooms": 3,
    "energy_rating": "E",
    "insulation": "poor",
    "heating": "gas_boiler",
    "glazing": "single",
    "solar": "none",
    "smart_controls": False,
    "annual_electricity_kwh": 3800,
    "annual_gas_kwh": 16500,
    "current_property_value_gbp": 210000,
}


def available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def choose_port(preferred: int, attempts: int = 20) -> int:
    for port in range(preferred, preferred + attempts):
        if available(port):
            return port
    raise RuntimeError(f"No available port in {preferred}..{preferred + attempts - 1}")


def request(url: str, payload=None, origin=None, preflight=False):
    headers = {}
    if origin:
        headers["Origin"] = origin
    if preflight:
        headers.update({
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        })
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = Request(
        url,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers=headers,
        method="OPTIONS" if preflight else ("POST" if payload is not None else "GET"),
    )
    with urlopen(req, timeout=6) as response:
        return response.status, {key.lower(): value for key, value in response.headers.items()}, response.read()


def wait_ready(url: str, process: subprocess.Popen, description: str, timeout: int = 45):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        if process.poll() is not None:
            raise RuntimeError(f"{description} exited with code {process.returncode}; see logs above")
        try:
            status, _, _ = request(url)
            if status == 200:
                return
        except (HTTPError, URLError, TimeoutError, OSError):
            pass
        time.sleep(0.5)
    raise RuntimeError(f"{description} did not become ready at {url} within {timeout}s")


def main() -> int:
    python = BACKEND / ".venv" / "bin" / "python"
    if not python.exists():
        print("Missing backend/.venv. Create it and install backend/requirements.txt.", file=sys.stderr)
        return 1
    if not (FRONTEND / "node_modules").exists():
        print("Missing frontend/node_modules. Run: cd frontend && npm ci", file=sys.stderr)
        return 1

    api_port = choose_port(8766)
    web_port = choose_port(3020)
    api_url = f"http://127.0.0.1:{api_port}"
    web_url = f"http://localhost:{web_port}"
    origins = ",".join([web_url, f"http://127.0.0.1:{web_port}"])
    api_env = os.environ.copy()
    api_env["CORS_ORIGINS"] = origins
    web_env = os.environ.copy()
    web_env["NEXT_PUBLIC_API_URL"] = api_url

    processes = []
    try:
        print(f"Starting FastAPI on {api_url}", flush=True)
        api = subprocess.Popen(
            [str(python), "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(api_port)],
            cwd=BACKEND, env=api_env, start_new_session=True,
        )
        processes.append(api)
        wait_ready(api_url + "/health", api, "FastAPI")

        endpoint = api_url + "/api/v1/analyze"
        status, _, body = request(endpoint, SAMPLE, web_url)
        result = json.loads(body)
        if status != 200 or not isinstance(result.get("score_details", {}).get("final_score"), int):
            raise RuntimeError("FastAPI assessment returned an invalid response")
        status, cors_headers, _ = request(endpoint, origin=web_url, preflight=True)
        if status != 200 or cors_headers.get("access-control-allow-origin") != web_url:
            raise RuntimeError("FastAPI CORS preflight check failed")
        simulation = api_url + "/api/v1/simulate"
        status, _, sim_body = request(simulation, {
            "property_input": SAMPLE,
            "selected_retrofit_ids": ["roof_insulation", "solar_pv"],
        }, web_url)
        if status != 200 or "energy" not in json.loads(sim_body):
            raise RuntimeError("Retrofit simulation smoke test failed")
        print("FastAPI assessment, retrofit simulation, and CORS: OK", flush=True)

        print(f"Starting Next.js on {web_url}", flush=True)
        web = subprocess.Popen(
            ["npm", "run", "dev", "--", "--hostname", "127.0.0.1", "--port", str(web_port)],
            cwd=FRONTEND, env=web_env, start_new_session=True,
        )
        processes.append(web)
        wait_ready(web_url, web, "Next.js", timeout=90)
        print(f"\nREADY: {web_url}", flush=True)
        print(f"API:   {api_url}/docs", flush=True)
        print("Press Ctrl+C to stop both servers. Do not start separate copies.", flush=True)
        while True:
            for name, process in [("FastAPI", api), ("Next.js", web)]:
                if process.poll() is not None:
                    raise RuntimeError(f"{name} stopped unexpectedly (exit code {process.returncode})")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping both development servers...", flush=True)
        return 0
    except Exception as exc:
        print(f"Startup/runtime error: {exc}", file=sys.stderr, flush=True)
        return 1
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                # Terminate the whole child process group, including Next's worker.
                os.killpg(process.pid, signal.SIGTERM)
        for process in reversed(processes):
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()


if __name__ == "__main__":
    sys.exit(main())
