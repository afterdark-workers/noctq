#!/bin/sh
# NoctQ V4 (Qwen-Image 2.1) — everything the worker image needs. The Dockerfile in your copy downloads this file
# from the original repo on every build, so fixes made there reach you with a rebuild.
set -eu

# file <dest> <url> <sha256>
file() {
  wget -q -O "$1" "$2"
  echo "$3  $1" | sha256sum -c - || { echo "ERROR: $1 changed upstream — wait for an update of the original repo, then rebuild" >&2; exit 1; }
}

# Noctaluna/Noct-Q-Uncensored-Qwen-Image-2.1 (7.3 GB)
file /comfyui/models/diffusion_models/NoctQ_V4_int8_convrot.safetensors \
  "https://huggingface.co/Noctaluna/Noct-Q-Uncensored-Qwen-Image-2.1/resolve/a81b9af51120a78e285e57906f2250a2a02080e9/NoctQ_V4_int8_convrot.safetensors" \
  4d92d5538253ab36e6a73b056cce5f697950f4303cb9e6686a3198d0ea13f9e8

# Comfy-Org/Qwen-Image-2.1 (9.4 GB)
file /comfyui/models/text_encoders/qwen3vl_8b_int8_convrot.safetensors \
  "https://huggingface.co/Comfy-Org/Qwen-Image-2.1/resolve/df94239739eef7205973a145ffa6f441f7b64e84/text_encoders/qwen3vl_8b_int8_convrot.safetensors" \
  8bfd0f6e12abf2d2d697ecc888e5e90b0d6741d6708f05799f53afa560452e8f

# Comfy-Org/Qwen-Image-2.1 (0.7 GB)
file /comfyui/models/vae/qwen_image_2.1_vae_bf16.safetensors \
  "https://huggingface.co/Comfy-Org/Qwen-Image-2.1/resolve/df94239739eef7205973a145ffa6f441f7b64e84/vae/qwen_image_2.1_vae_bf16.safetensors" \
  bb21f7473051e1ac368515dd3f2e15cd44d7a11748ee8823e1ddca3e4876b7c9

# ComfyUI 0.34.0 (base image) → 0.39.0 — Qwen-Image 2.1 needs 0.39. Install into /opt/venv (the one ComfyUI actually runs with).
cd /comfyui
git fetch --depth 1 https://github.com/Comfy-Org/ComfyUI.git tag v0.39.0
git checkout -f v0.39.0
uv pip install --python /opt/venv/bin/python -r requirements.txt "transformers>=4.50.3,<5" "huggingface-hub<1.0"
timeout 300 /opt/venv/bin/python main.py --quick-test-for-ci --cpu
