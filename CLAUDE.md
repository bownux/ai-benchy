# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

ai-benchy is a small, hardware-agnostic benchmark for local LLMs/VLMs. It hits any
OpenAI-compatible `/v1/chat/completions` endpoint and writes a self-describing result
JSON (scores + auto-detected hardware + model metadata) that can be dropped next to
anyone else's and compared directly. The defining constraint: **scoring is judge-free
and deterministic** — every task scores with code (run-the-output / exact-match /
valid-JSON / tool-call-emitted), never with a second model. Keep it that way.

## Commands

```bash
# Run suites against a served endpoint (writes results/<suite>__<label>__<host>__<ts>.json)
python -m benchy run <suite> --endpoint http://127.0.0.1:8080 --label NAME \
    --backend llama.cpp --quant Q4_K_M --params-b 8 --ctx 8192
#   <suite> = coding | reasoning | agentic | vision | text (all 3 text suites) | all (text+vision)

python -m benchy run text ... --no-think     # send chat_template_kwargs enable_thinking=false
python -m benchy run coding ... --no-exec     # skip code-EXECUTION tasks (don't run model output)

python -m benchy compare results/ > LEADERBOARD.md   # regenerate the leaderboard
python -m benchy list                                # all suites + tasks (cheap, no model)
python -m benchy selftest                            # render vision images locally to eyeball ground truth
python -m benchy.hwinfo                              # print the auto-detected hardware block

# Concurrency / serving load test (stdlib-only module in the package)
python -m benchy.concbench --endpoint http://127.0.0.1:1234 --model NAME --no-think \
    --concurrency 16 --num-prompts 64 --max-tokens 256
# add --out results/ to write concresult JSON, then: python -m benchy compare-conc results/
```

On this machine the venv interpreter is `./.venv/Scripts/python.exe` (Windows). There
is **no test suite, linter, or build step** — it's plain stdlib Python (3.9+); the only
dependency is Pillow, used solely by the vision suite. To "test" a change, run
`benchy list` / `benchy selftest`, or run a suite against any local model with
`--label test`.

## Architecture

The data flow is one direction: **CLI → runner → suite tasks → client → server**, with
results stamped by hwinfo and merged by compare.

- `benchy/client.py` — the **only** module that talks to a model server. Tasks never see
  a URL; they get a `Client` and call `.chat(messages, max_tokens=, tools=)`, which
  returns a `Response` (`.content`, `.tool_calls`, `.timings`, `.usage`,
  `.finish_reason`, `.gen_tps()`). `--no-think` is implemented here by adding
  `chat_template_kwargs={"enable_thinking": False}` to the request body (a Qwen3-style
  chat-template toggle — it only takes effect if the served model's template honors it).
- `benchy/runner.py` — runs a suite's tasks in order, accumulates per-tier scores, and
  writes the result JSON. **Truncation handling lives here**: if a response's
  `finish_reason == "length"`, the detail is tagged `[trunc:length]` so a reasoning
  model that blew its token budget reads as a truncation, not a capability miss. (This is
  why thinking-on runs often crater on reasoning — the CoT eats the budget. `--no-think`
  fixes it.)
- `benchy/suites/__init__.py` — the Suite/Task framework + lazy registry. A `Task` is
  `(id, tier, run)` where `run(client) -> (score: float in [0,1], detail: str)`. A
  `Suite` is `(name, version, needs, tasks, blurb)`; `needs` is `"text"` or `"vision"`.
  Suites self-register via `register()` on import; `_load_all()` imports every suite
  module — **a new suite file must be added to that import list** to be discoverable.
- `benchy/suites/{coding,reasoning,agentic,vision}.py` — the actual tasks. Inputs are
  hardcoded or rendered from code (vision images via Pillow), never fetched — so a rerun
  is byte-identical. `tier` is just a grouping label (`core`/`hard`, `code`/`agentic`,
  etc.) to show *where* a model breaks.
- `benchy/sandbox.py` — runs model-generated Python for the coding suite in a fresh
  `subprocess` (`-I` isolated mode) with a timeout and rlimits. **rlimits are Unix-only
  and silently skipped on Windows**, so the coding suite executes untrusted model output
  with weaker isolation here — use `--no-exec` or a container/VM if that matters.
- `benchy/hwinfo.py` — auto-detects host/CPU/RAM/GPUs (nvidia-smi, rocm-smi, Linux /sys
  fallback) and stamps it into every result. This is what makes cross-machine comparison
  fair without anyone keeping notes. Degrades to "unknown" rather than failing.
- `benchy/compare.py` — merges `results/*.json` into one Markdown table per suite.
  **Dedup is by `(label, gpu_summary)`**, keeping the best by (score, gen_tps, recency) —
  so re-running a model *replaces* its row, but a distinct label (e.g. a `-nothink`
  variant, or a different backend/quant you want shown separately) is kept as its own row.
  Choose labels deliberately: same label + same hardware collapses to one row.

## Result file = the unit of sharing

`results/<suite>__<label>__<host>__<timestamp>.json` carries scores, per-task detail,
throughput, model metadata (what you pass via `--backend/--quant/--ctx/--params-b/
--notes`), and auto-detected hardware. Schema id is `ai-benchy/result/1` (`benchy/__init__.py`).
Don't hand-edit scores — only the `model` metadata fields are author-provided. Committing
result files for new hardware is a primary, welcome contribution (see recent
`feat(results): …` commits).

## Conventions that matter

- **Judge-free & deterministic** (above) — non-negotiable; it's why results are comparable.
- **Version your scoring changes.** If you change a task's inputs or scoring, bump that
  suite's `version` so old result files stay interpretable.
- **Throughput is not apples-to-apples across backends.** llama.cpp returns a `timings`
  block (true `predicted_per_second`); vLLM/ollama don't, so `gen_tps` falls back to
  wall-clock (`completion_tokens / elapsed`), which folds in network/queue overhead.
  Compare speed only within the same backend+hardware.
- **Windows console is cp1252** — non-ASCII characters (arrows, `·`, em-dashes) in
  `print()` raise `UnicodeEncodeError`. Keep stdout ASCII in any script meant to run here.
- **Stay stdlib.** Small functions, comments explain *why*. Pillow is the only dependency.

## Adding work

- New task: write `def t_x(client) -> (float, str)` in a suite module, append
  `Task("x", "tier", t_x)` to its task list. See `CONTRIBUTING.md`.
- New suite: new `benchy/suites/<name>.py` that calls `register(Suite(...))`, then add it
  to the import in `benchy/suites/__init__.py:_load_all()`.
- Serving any backend (llama.cpp/vLLM/ollama/LM Studio/hosted): see `docs/serving.md`.
  Note: ollama's base is passed **without** `/v1` (benchy appends the path itself).
