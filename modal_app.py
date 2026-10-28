"""This worker on Modal (modal.com) instead of RunPod — the same Dockerfile, build and handler, the same requests.

It answers like a RunPod endpoint: POST <url>/run {"input": …} → {"id"} · GET <url>/status/<id> · POST <url>/cancel/<id>,
with the header «Authorization: Bearer <your password>». Setup: README.md → «Or run it on Modal».
"""
import importlib.util, os, subprocess, sys, time, urllib.request
from pathlib import Path
import modal

GPU = "A10"  # 24 GB — others: "L4" (24 GB), "L40S" (48 GB), "A100-80GB", "H100" — prices: modal.com/pricing
HERE = Path(__file__).parent

app = modal.App(HERE.name)  # your folder's name — the worker's URL starts with it
image = modal.Image.from_dockerfile(HERE / "Dockerfile", context_dir=HERE).pip_install("fastapi[standard]")
key = modal.Secret.from_name("cobaltpear-key")


@app.cls(image=image, gpu=GPU, secrets=[key], scaledown_window=60, timeout=1800)
class Worker:
    @modal.enter()
    def start(self):
        # ComfyUI as the RunPod base image starts it, then the worker's own handler.py (without its RunPod loop)
        subprocess.Popen(["python", "-u", "/comfyui/main.py", "--disable-auto-launch", "--disable-metadata", "--listen", "127.0.0.1", "--port", "8188"])
        import runpod
        runpod.serverless.start = lambda *a, **k: None
        spec = importlib.util.spec_from_file_location("handler", "/handler.py")
        self.h = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.h)

    @modal.method()
    def run(self, job: dict) -> dict:
        return self.h.handler({"id": "modal", "input": job.get("input") or {}})


@app.function(image=modal.Image.debian_slim().pip_install("fastapi[standard]"), secrets=[key])
@modal.asgi_app()
def api():
    import hmac
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    web, want = FastAPI(), "Bearer " + os.environ["CP_KEY"]

    @web.middleware("http")
    async def need_key(request: Request, call_next):  # a browser's preflight (OPTIONS) carries no key — CORS answers it
        if request.method != "OPTIONS" and not hmac.compare_digest(request.headers.get("authorization", ""), want):
            return JSONResponse({"error": "Wrong key"}, status_code=401)
        return await call_next(request)
    web.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])  # added last = runs first

    @web.post("/run")
    def run(job: dict):
        return {"id": Worker().run.spawn(job).object_id, "status": "IN_QUEUE"}

    @web.get("/status/{call_id}")
    def status(call_id: str):
        try:
            out = modal.FunctionCall.from_id(call_id).get(timeout=0)
        except TimeoutError:
            return {"id": call_id, "status": "IN_PROGRESS"}
        except Exception as e:
            return {"id": call_id, "status": "FAILED", "error": str(e)[:300]}
        if isinstance(out, dict) and out.get("error") and not out.get("images"):
            return {"id": call_id, "status": "FAILED", "error": out["error"], "output": out}
        return {"id": call_id, "status": "COMPLETED", "output": out}

    @web.post("/cancel/{call_id}")
    def cancel(call_id: str):
        modal.FunctionCall.from_id(call_id).cancel()
        return {"id": call_id, "status": "CANCELLED"}

    return web
