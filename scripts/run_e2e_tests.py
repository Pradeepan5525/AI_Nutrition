"""End-to-End Test Orchestrator for AI Nutrition Intelligence System.

Starts backend API and Vite frontend if not already running,
executes the automated Playwright E2E suite, generates responsive screenshots,
and reports results.
"""

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT_DIR / "web"


def is_service_ready(url: str, timeout: float = 2.0) -> bool:
    """Check if an HTTP service is responding."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "E2E-HealthCheck"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 304)
    except Exception:
        return False


def main() -> None:
    api_proc = None
    web_proc = None

    try:
        # 1. Ensure API is running
        api_url = "http://127.0.0.1:8000/health"
        if not is_service_ready(api_url):
            print("[E2E] Starting FastAPI backend on port 8000...")
            api_proc = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8000"],
                cwd=str(ROOT_DIR),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Wait for API readiness
            for _ in range(30):
                if is_service_ready(api_url):
                    print("[E2E] FastAPI backend is ready.")
                    break
                time.sleep(0.5)
            else:
                print("[E2E] ERROR: Backend failed to start within 15 seconds.")
                sys.exit(1)
        else:
            print("[E2E] Backend API is already running.")

        # 2. Ensure Web frontend is running
        web_url = "http://localhost:5173"
        if not is_service_ready(web_url):
            print("[E2E] Starting Vite dev server on port 5173...")
            web_cmd = "npm.cmd run dev" if sys.platform == "win32" else "npm run dev"
            web_proc = subprocess.Popen(
                web_cmd,
                cwd=str(WEB_DIR),
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            for _ in range(30):
                if is_service_ready(web_url):
                    print("[E2E] Vite frontend is ready.")
                    break
                time.sleep(0.5)
            else:
                print("[E2E] ERROR: Frontend failed to start within 15 seconds.")
                sys.exit(1)
        else:
            print("[E2E] Frontend Vite server is already running.")

        # 3. Run Playwright E2E Runner
        print("[E2E] Executing Playwright E2E suite & screenshot generator...")
        runner_script = WEB_DIR / "scripts" / "e2e_runner.cjs"
        result = subprocess.run(
            ["node", str(runner_script)],
            cwd=str(WEB_DIR),
        )

        if result.returncode != 0:
            print("[E2E] Playwright E2E tests encountered failures.")
            sys.exit(result.returncode)
        else:
            print("\n[E2E] All Playwright E2E tests PASSED successfully!")

    finally:
        # Clean up child processes if we started them
        if api_proc:
            print("[E2E] Stopping spawned backend process...")
            api_proc.terminate()
            try:
                api_proc.wait(timeout=3)
            except Exception:
                api_proc.kill()
        if web_proc:
            print("[E2E] Stopping spawned frontend process...")
            # On windows shell=True might need taskkill
            if sys.platform == "win32":
                subprocess.run(f"taskkill /F /T /PID {web_proc.pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                web_proc.terminate()


if __name__ == "__main__":
    main()
