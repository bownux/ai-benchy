# ai-benchy

A small, **hardware-agnostic** benchmark for local LLMs and vision models that's
easy to **run, repeat, compare, and extend**. Point it at any OpenAI-compatible
endpoint (llama.cpp, vLLM, ollama, LM Studio, …), and it produces a self-describing
result file you can drop next to anyone else's and compare directly.

**Why it exists:** "which model should I run on my GPU?" is hard to answer across
different hardware. ai-benchy makes the answer *repeatable* — every task is scored
**programmatically** (run-the-code / exact-match / valid-JSON / tool-call-made), with
**no second model grading the output**, so a run on a 3× R9700 box and a run on 2×
Blackwell 5000s mean the same thing. Each result stamps in your **auto-detected
hardware**, so the comparison is fair without anyone keeping notes.

📊 **[Current results → LEADERBOARD.md](LEADERBOARD.md)** (regenerate with `python -m benchy compare results/ > LEADERBOARD.md`).

## What it measures

| Suite | Needs | Tasks |
|---|---|---|
| `coding` | text | write-and-**run** Python: fib, bugfix + 4 hard algorithmic tasks |
| `reasoning` | text | strict-output JSON, a logic trap, SQL synthesis, context recall |
| `agentic` | text | tool-calling, doc-following, and two **multi-turn mocked-shell** incident loops |
| `vision` | multimodal | 27 **synthetic-image** tasks (OCR, counting, charts, spatial, tables) |

Tasks are tiered (`core`/`hard`, etc.) so you can see *where* a model breaks, not
just a single number.

## Install

```bash
git clone https://github.com/bownux/ai-benchy.git && cd ai-benchy
pip install -r requirements.txt        # only dependency is Pillow (for the vision suite)
```
Python 3.9+. No GPU or framework required on the machine running the benchmark — it
only needs to reach a model endpoint over HTTP.

## Quickstart

First, **serve a model** so there's an OpenAI-compatible endpoint (see
[`docs/serving.md`](docs/serving.md) for llama.cpp / vLLM / ollama / LM Studio).
Then:

```bash
# text suites (coding + reasoning + agentic) against a text model on :8080
python -m benchy run text --endpoint http://127.0.0.1:8080 --label gpt-oss-120b \
    --backend llama.cpp --quant MXFP4 --params-b 117

# the vision suite against a multimodal model on :8081
python -m benchy run vision --endpoint http://127.0.0.1:8081 --label qwen3-vl-8b \
    --backend llama.cpp --quant Q4_K_M

# build a leaderboard from every result file
python -m benchy compare results/
```

Each run writes `results/<suite>__<label>__<host>__<timestamp>.json`. Run a single
suite (`coding`/`reasoning`/`agentic`/`vision`), all text suites (`text`), or
everything (`all`). The `--backend/--quant/--ctx/--params-b/--notes` flags are
optional metadata that show up in the leaderboard — fill them in so comparisons are
meaningful.

```bash
python -m benchy list           # show every suite and task
python -m benchy selftest       # render the vision images locally to eyeball ground truth (no model)
```

## Concurrency / serving load test

The suites above are **single-stream** (one request at a time), so they measure model
*capability*, not how your server holds up under load. `benchy.concbench` is a small
companion module for that: it fires N prompts through a pool of `--concurrency`
workers and reports **aggregate output tok/s**, request throughput, **TTFT**
(time-to-first-token), and per-request latency at p50/p99 — the numbers that show
whether a backend actually batches.

```bash
python -m benchy.concbench --endpoint http://127.0.0.1:1234 --model qwen3-27b \
    --no-think --concurrency 16 --num-prompts 64 --max-tokens 256

# sweep concurrency to find where throughput plateaus and TTFT blows up
for c in 1 4 16 32; do python -m benchy.concbench --endpoint http://127.0.0.1:1234 \
    --model qwen3-27b --no-think --concurrency $c --num-prompts $((c*4)); done
```

Stdlib-only and OpenAI-compatible like the rest of benchy. Pass `--no-think` on a
reasoning model so output length is bounded and TTFT is meaningful. Note: llama.cpp
serializes requests unless you start `llama-server` with `--parallel N`.

## Comparing across machines

The result JSON is the unit of sharing. To compare with a friend:
1. You each `run` the same suite against your model and commit the result file (or send it).
2. `python -m benchy compare results/` merges them into one table per suite, sorted by
   score, showing model + quant + **your hardware** + throughput.

Because the images/inputs are fixed and scoring is deterministic, the only variables
are **the model** and **the hardware** — which is exactly what you want to compare.

## Result format

```jsonc
{
  "schema": "ai-benchy/result/1",
  "suite": "vision", "suite_version": "1",
  "label": "qwen3-vl-8b",
  "endpoint": "...", "served_model_id": "qwen3-vl-8b",
  "model":   { "backend": "llama.cpp", "quant": "Q4_K_M", "params_b": 8, ... },  // you provide
  "hardware":{ "gpus": [{"name":"RTX 3080 Ti","vram_mb":12288}], "cpu":"...", "ram_gb":125 },  // auto
  "scores":  { "total": 24, "max": 27, "tiers": { "core": [12,13], "hard": [12,14] } },
  "throughput": { "gen_tps": 20.1, "prefill_tps": 39.1 },
  "tasks":   [ { "id":"ocr_code", "tier":"core", "score":0, "latency_s":1.1, "detail":"..." }, ... ]
}
```

## Extending it

Adding a task is a few lines; adding a suite is a new file. See
[`CONTRIBUTING.md`](CONTRIBUTING.md). PRs with new tasks, new suites, bug fixes, and
**result files for new hardware** are all welcome.

## Design principles

- **Judge-free.** No LLM grades another LLM. Every score is `run-it` / exact-match /
  numeric / valid-JSON / tool-call-emitted. Reproducible and cheap.
- **Endpoint-agnostic.** One thin OpenAI-compatible client; nothing else knows a URL.
- **Self-describing results.** Hardware + model metadata travel with every score.
- **Synthetic where possible.** The vision images are drawn from code — no datasets to
  download or license, identical on every machine.
- **Honest tiers.** `core` vs `hard` so a saturated total doesn't hide a real gap.

## Safety note

The `coding` suite **executes model-generated Python** to score it (in a separate
process with CPU/memory/time limits). Use `--no-exec` to skip those tasks, or run the
whole thing in a container/VM if you don't trust the model.

## License

MIT — see [LICENSE](LICENSE).
