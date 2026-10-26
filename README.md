# NoctQ V4 (Qwen-Image 2.1) — RunPod Serverless worker

A ready-to-build [RunPod Serverless](https://runpod.io?ref=qpguwapm) worker for **[NoctQ V4](https://huggingface.co/Noctaluna/Noct-Q-Uncensored-Qwen-Image-2.1)**, an uncensored Qwen-Image 2.1 fine-tune. Based on the official [`runpod/worker-comfyui`](https://github.com/runpod-workers/worker-comfyui).

Models are baked into the image, so a cold start does not re-download anything.

> 18+ model. You download it and are responsible for following the model licenses.

## What's inside

| File | Source | Size |
|---|---|---|
| `diffusion_models/NoctQ_V4_int8_convrot.safetensors` | [Noctaluna/Noct-Q-Uncensored-Qwen-Image-2.1](https://huggingface.co/Noctaluna/Noct-Q-Uncensored-Qwen-Image-2.1) | 7.3 GB |
| `text_encoders/qwen3vl_8b_int8_convrot.safetensors` | [Comfy-Org/Qwen-Image-2.1](https://huggingface.co/Comfy-Org/Qwen-Image-2.1) | 9.4 GB |
| `vae/qwen_image_2.1_vae_bf16.safetensors` | [Comfy-Org/Qwen-Image-2.1](https://huggingface.co/Comfy-Org/Qwen-Image-2.1) | 0.7 GB |

Just the model as its creator released it — no LoRAs, no extra nodes. All files are checked by SHA-256 at build time. ComfyUI is upgraded to 0.39.0.

## Setup (about 5 minutes + build time)

New to this? Follow the [step-by-step setup guide](https://cobaltpear.github.io/guide.html).

1. **Make your own copy** — click **Use this template** → **Create a new repository**. No token is needed — the files come from Hugging Face.
   No RunPod account yet? [Sign up here](https://runpod.io?ref=qpguwapm) — a referral link: after you first add $10, RunPod gives you a bonus credit (usually $5–10) and this repo a small credit.
2. **Create the endpoint** — see [Create the endpoint](#create-the-endpoint) below.
3. **Create an API key** — RunPod → Settings → API Keys → **Restricted**, allow only this endpoint.

## Create the endpoint

RunPod → **Serverless** → **New Endpoint** → **Deploy from a GitHub repository** → pick your copy (the first time, **Edit connection** lets RunPod see it). Then, top to bottom on the page:

| Where on the page | What to set |
|---|---|
| **Endpoint name** | anything — your copy's name is fine |
| **GPU configuration** | tick a box of 24 GB or more (more boxes = easier to get a GPU) |
| **Max workers** | `1` |
| Click **Advanced settings** to open it: | |
| → **Active workers** | `0` — nothing to pay while idle |
| → **GPU count** | `1` |
| → **Idle timeout** | `5` sec |
| → **Enable FlashBoot** | on (the switch) · **Standard** |
| → **Enable execution timeout** | on · **Execution timeout** `600` sec |
| → click **Container configuration** to open it → **Container disk** | 40 GB |

Leave everything else as it is, then **Deploy** at the bottom. The first build takes about 30 minutes. The very first request after that waits another 10–15 minutes while a worker pulls the image; later cold starts are much faster.

## Updates

Your copy holds nothing of its own. The build steps (`build.sh`, `handler.py`) are downloaded from this repo on every build, so when something changes upstream (a model file is replaced, ComfyUI needs an update) it is fixed here — you just rebuild your endpoint.

To rebuild: commit any change to the `main` branch of your copy — RunPod builds again on every push to `main` (the endpoint's **Builds** tab shows it). Nothing to change? Edit `README.md` (✏️), add a line, **Commit changes…** → **Commit changes**.

### Model version

This repo always follows the version the model's creator currently recommends. Now: **V4 (Hugging Face commit a81b9af)**.
Each change of the build files is kept as a release (`files-…`). To stay on one, replace `latest/download` with `download/files-…` (that release's name) in both `ADD` lines of your `Dockerfile`.

## Use it

Any client that sends ComfyUI API-format workflows to RunPod works. `pack.json` in this repo holds the workflow and tells a client where the prompt, seed and size go (format `pack/1`, engine `comfyui`).

Raw request:

```bash
curl -X POST https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync \
  -H "Authorization: Bearer <API_KEY>" -H "Content-Type: application/json" \
  -d "{\"input\": {\"workflow\": $(jq .workflow pack.json | jq '.["4"].inputs.prompt = "a photo of a woman reading in a cafe" | .["6"].inputs.seed = 1')}}"
```

The image comes back as base64 in `output.images[0].data`.

Tips: 25 steps, CFG 3, Euler. A negative prompt is used.

### LoRAs

- **Per picture:** send up to 4 LoRAs with a request: `input.remote_loras` = `[{"name": "remote_<id>.safetensors", "url": "<download link>", "sha256": "<file sha256>"}]` plus a `LoraLoader` reading that name in the workflow — the worker downloads each once and keeps it while it runs. [Cobalt Pear](https://cobaltpear.github.io/) does all of this from a Civitai or Hugging Face link. For more than 4, set the environment variable `REMOTE_LORA_MAX` (e.g. `8`) on your endpoint (**Manage → Edit Endpoint → Environment Variables**).
- **Built in:** put links in the `LORAS` line of your `Dockerfile` — each followed by its strength — and rebuild. They are downloaded once at build time, so a fresh worker doesn't download them again. A request picks which ones it uses with `input.baked_loras` = `[{"link": "<link from LORAS>", "strength": 0.8}]` (`[]` = none); without it every one is used at its `LORAS` strength. Put their trigger words in your prompt yourself. To accept only built-in LoRAs, set `REMOTE_LORA_MAX` to `0`.
- Pick LoRAs made for this model's base model — the worker warns (`output.warning`) when one doesn't fit.

### Compatible clients

- [Cobalt Pear](https://cobaltpear.github.io/) — a one-page web app: add this repo's URL, your endpoint ID and API key, then just type a prompt. Everything stays in your browser. [Try the demo](https://cobaltpear.github.io/demo/) without RunPod.

Questions or ideas: [Discussions](https://github.com/cobaltpear/cobaltpear.github.io/discussions).
