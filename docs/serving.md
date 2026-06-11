# Serving a model for ai-benchy

ai-benchy talks to any **OpenAI-compatible** `/v1/chat/completions` endpoint. Start a
server for your model, note its URL, and pass it as `--endpoint`. Below are the common
ones. Whatever you use, fill in `--backend/--quant/--ctx/--params-b` so your result is
comparable.

> Vision suite: the server must accept image content parts (`image_url`) and you must
> load the model's **mmproj/vision projector** alongside the weights.

## llama.cpp (`llama-server`)

```bash
# text
llama-server --model model.gguf --host 127.0.0.1 --port 8080 \
    --n-gpu-layers 99 --ctx-size 8192 --flash-attn on --jinja --alias mymodel
python -m benchy run text --endpoint http://127.0.0.1:8080 --label mymodel --backend llama.cpp --quant Q4_K_M

# vision (note --mmproj)
llama-server --model vlm.gguf --mmproj mmproj.gguf --host 127.0.0.1 --port 8081 \
    --n-gpu-layers 99 --ctx-size 4096 --flash-attn on --jinja
python -m benchy run vision --endpoint http://127.0.0.1:8081 --label myvlm --backend llama.cpp --quant Q4_K_M
```
Pin to a specific GPU with the backend's device env (e.g. `CUDA_VISIBLE_DEVICES=0`,
or `GGML_VK_VISIBLE_DEVICES=0` for Vulkan).

## vLLM

```bash
vllm serve <hf-model-id> --port 8000 --max-model-len 8192
python -m benchy run text --endpoint http://127.0.0.1:8000 --label <model> --backend vllm
```
For vision, serve a VLM vLLM supports; the OpenAI image_url path works the same.
(vLLM may not return llama.cpp-style `timings`; ai-benchy falls back to wall-clock
tok/s automatically.)

## ollama

```bash
ollama serve                        # exposes an OpenAI-compatible API on :11434
ollama pull llama3.2-vision
python -m benchy run vision --endpoint http://127.0.0.1:11434 --label llama3.2-vision --backend ollama
```
Ollama's OpenAI endpoint lives at `http://127.0.0.1:11434/v1` — but ai-benchy adds the
`/v1/...` path itself, so pass the base **without** `/v1` (i.e. `:11434`). If your
build differs, pass whatever base makes `<base>/v1/chat/completions` valid.

## LM Studio

Start the local server (it serves OpenAI-compatible on `:1234` by default):
```bash
python -m benchy run text --endpoint http://127.0.0.1:1234 --label <model> --backend lmstudio
```

## Hosted APIs

Any OpenAI-compatible host works; pass `--endpoint https://host` and `--api-key …`.
(You're then benchmarking the provider's serving, not your hardware — note that.)

## GPU pinning / "benchmark mode"

To bench one model while keeping others running, give the benchmark target its own
GPU (separate `--port` + device pin) and point `--endpoint` at it. On multi-GPU rigs,
pick the device by **free VRAM**, not a fixed index — some drivers reorder indices
across power states.
