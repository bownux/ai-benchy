# Contributing to ai-benchy

The goal: stay **simple, deterministic, and portable**. Anyone should be able to read
a task in 30 seconds and trust that it scores the same on every machine.

## Ground rules

1. **No model grades a model.** Every task must score with code: run-the-output,
   exact/normalized match, a number, valid JSON, or "did it emit the tool call".
2. **Deterministic inputs.** Hardcode prompts; render images from code. No network
   fetches, no datasets, no randomness (so a rerun is identical).
3. **Public-safe.** No private hosts, credentials, or proprietary content. The agentic
   scenarios use *mocked* shells — keep them generic.
4. **Version your changes.** If you change a task's scoring or inputs, bump the
   suite's `version` so old result files stay interpretable.

## Add a task to an existing suite

A task is a function `run(client) -> (score: float in [0,1], detail: str)`:

```python
# benchy/suites/reasoning.py
def t_capitals(client):
    r = client.chat([{"role": "user", "content":
        "What is the capital of France? Reply with only the city."}], max_tokens=50)
    ok = "paris" in r.content.lower()
    return (1.0 if ok else 0.0, f"raw={r.content.strip()[:40]!r}")

# then add it to the suite's task list:
SUITE = register(Suite(..., tasks=[ ..., Task("capitals", "core", t_capitals) ]))
```

- `client.chat(messages, max_tokens=…, tools=…)` returns a `Response` with
  `.content`, `.tool_calls`, `.timings`, `.gen_tps()`.
- The `tier` string just groups tasks in the output (e.g. `core`/`hard`). Use it to
  separate easy from discriminating tasks.
- Vision tasks build multimodal `content` (text + `image_url` data URL) — see
  `benchy/suites/vision.py` and render the image from Pillow so ground truth is exact.

## Add a whole suite

Create `benchy/suites/mysuite.py`, define tasks, and `register(Suite(...))`. Add the
module to the import in `benchy/suites/__init__.py:_load_all()`. Declare `needs="text"`
or `needs="vision"`.

## Test your change without burning tokens

```bash
python -m benchy list                       # your task shows up
python -m benchy selftest                   # vision images render (if you touched vision)
python -m benchy run <suite> --endpoint <any local model> --label test
```

## Submit a result for new hardware

Just run a suite and open a PR adding your `results/*.json` (or share the file). More
hardware data points = a more useful leaderboard. Don't hand-edit scores; only the
`model` metadata fields are yours to fill in (via the `--backend/--quant/...` flags).

## Style

Plain stdlib, small functions, comments that explain *why*. Keep dependencies to
Pillow. Match the surrounding code.
