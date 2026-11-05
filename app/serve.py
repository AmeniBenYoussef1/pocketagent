"""Run everything locally: build the web app if needed, then serve it with the API.

    python -m app.serve              # http://localhost:8000, GPU if available
    python -m app.serve --cpu        # CPU only
    python -m app.serve --rebuild    # force a new build of app/web

Needs Node.js (npm) the first time, to build app/web into app/web/dist.
"""

import argparse
import os
import shutil
import subprocess
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "app" / "web"


def needs_build() -> bool:
    dist = WEB / "dist" / "index.html"
    if not dist.exists():
        return True
    built = dist.stat().st_mtime
    sources = [p for p in (WEB / "src").rglob("*") if p.is_file()] + [WEB / "index.html", WEB / "package.json"]
    return any(p.stat().st_mtime > built for p in sources)


def build() -> None:
    npm = shutil.which("npm")
    if npm is None:
        raise SystemExit("npm not found: install Node.js 20+ to build the web app (https://nodejs.org)")
    if not (WEB / "node_modules").exists():
        subprocess.run([npm, "install"], cwd=WEB, check=True)
    subprocess.run([npm, "run", "build"], cwd=WEB, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cpu", action="store_true", help="never use the GPU")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    if args.cpu:
        os.environ["POCKETAGENT_DEVICE"] = "cpu"
    if args.rebuild or needs_build():
        print("building the web app...")
        build()
    import uvicorn
    url = f"http://localhost:{args.port}"
    print(f"PocketAgent on {url}")
    if not args.no_browser:
        webbrowser.open(url)
    uvicorn.run("app.api.main:app", host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
