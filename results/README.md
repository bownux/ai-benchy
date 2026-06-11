# results/

Every `benchy run` drops a self-describing JSON here, named
`<suite>__<label>__<host>__<timestamp>.json`. `benchy compare results/` merges them
into a leaderboard.

The `*.json` files committed here are **baseline runs from the maintainer's box**
(3× AMD R9700 + RTX 3080 Ti, llama.cpp/Vulkan+CUDA) — useful as a reference point and
a format example.

## Submitting your numbers

Run a suite, then commit (or send) the produced JSON:

```bash
python -m benchy run text   --endpoint <your-endpoint> --label <model> --backend <…> --quant <…>
python -m benchy run vision --endpoint <your-endpoint> --label <model> --backend <…> --quant <…>
# open a PR adding results/*.json
```

Don't hand-edit scores or task results — only the `model` metadata (the
`--backend/--quant/--ctx/--params-b/--notes` flags) is yours to set. The hardware
block is auto-detected so the comparison stays fair.
