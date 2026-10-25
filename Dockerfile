# NoctQ V4 (Qwen-Image 2.1) — RunPod Serverless ComfyUI worker
# Build on RunPod from your own copy of this repo (Dockerfile path = Dockerfile, build context = .).
# The build steps are downloaded from the original repo, so there is nothing to edit.

FROM runpod/worker-comfyui:5.10.0-base
ADD https://github.com/afterdark-workers/noctq/releases/latest/download/build.sh /build.sh
RUN sh /build.sh
ADD https://github.com/afterdark-workers/noctq/releases/latest/download/handler.py /handler.py
