import subprocess
import sys
from pathlib import Path 
 
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
 
APP_ROOT = Path(__file__).parent
MAIN_SCRIPT = APP_ROOT / "main.py"
OUTPUT_DIR = APP_ROOT / "output"
 
app = FastAPI(title="Shorts Generator API")
 
# Allows the web UI (served on a different port) to call this API.
# Tighten allow_origins to your actual frontend URL before deploying anywhere
# other than your own machine.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
 
 
class GenerateRequest(BaseModel):
    target: str          # YouTube link or local file path
    n: int = 3
    ratio: str = "9:16"
    resolution: str = "720"
    language: str = ""   # empty = auto-detect
    hook: bool = True
 
 
class GenerateResponse(BaseModel):
    target: str
    success: bool
    output_files: list[str]
    log: str
 
 
@app.get("/api/health")
def health():
    return {"status": "ok"}
 
 
@app.post("/api/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    if not req.target.strip():
        raise HTTPException(status_code=400, detail="target is required")
 
    before = _existing_output_files()
 
    cmd = [
        sys.executable, str(MAIN_SCRIPT), req.target,
        "--n", str(req.n),
        "--ratio", req.ratio,
        "--resolution", str(req.resolution),
    ]
    if req.language.strip():
        cmd += ["--language", req.language.strip()]
    if not req.hook:
        cmd.append("--no-hook")
 
    result = subprocess.run(cmd, cwd=APP_ROOT, capture_output=True, text=True)
 
    after = _existing_output_files()
    new_files = sorted(after - before)
 
    return GenerateResponse(
        target=req.target,
        success=result.returncode == 0,
        output_files=new_files,
        log=(result.stdout + result.stderr)[-4000:],  # trim for the response
    )
 
 
def _existing_output_files() -> set[str]:
    if not OUTPUT_DIR.exists():
        return set()
    return {p.name for p in OUTPUT_DIR.glob("*.mp4")}
 
 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
