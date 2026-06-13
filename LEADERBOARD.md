# ai-benchy leaderboard

<!-- generated: `python -m benchy compare results/ > LEADERBOARD.md` — do not hand-edit -->

Scores are out of each suite's task count; tiers show the breakdown. `gen tok/s` is throughput on the **runner's** hardware (shown in the last column), so compare capability across rows and speed only within the same hardware.

## agentic  (suite v1, 2 runs)

| Model | Score | Tiers | gen tok/s | Backend · Quant | Hardware | Run |
|---|---|---|---|---|---|---|
| **gpt-oss-120b** | 4/4 | core 2/2 · agentic 2/2 | 78.7 | llama.cpp · MXFP4 | NVIDIA GeForce RTX 3080 Ti 12GB, AMD Radeon AI PRO R9700 31GB, AMD Radeon AI PRO R9700 31GB, AMD Radeon AI PRO R9700 31GB | 2026-06-11 |
| **Qwen3.6-35B-A3B** | 3/4 | core 1/2 · agentic 2/2 | 193.8 | llama.cpp | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-13 |

## coding  (suite v1, 2 runs)

| Model | Score | Tiers | gen tok/s | Backend · Quant | Hardware | Run |
|---|---|---|---|---|---|---|
| **gpt-oss-120b** | 6/6 | code 2/2 · hard 4/4 | 93.45 | llama.cpp · MXFP4 | NVIDIA GeForce RTX 3080 Ti 12GB, AMD Radeon AI PRO R9700 31GB, AMD Radeon AI PRO R9700 31GB, AMD Radeon AI PRO R9700 31GB | 2026-06-11 |
| **Qwen3.6-35B-A3B** | 5/6 | code 2/2 · hard 3/4 | 198.43 | llama.cpp | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-13 |

## reasoning  (suite v1, 2 runs)

| Model | Score | Tiers | gen tok/s | Backend · Quant | Hardware | Run |
|---|---|---|---|---|---|---|
| **gpt-oss-120b** | 3/4 | core 3/4 | 91.81 | llama.cpp · MXFP4 | NVIDIA GeForce RTX 3080 Ti 12GB, AMD Radeon AI PRO R9700 31GB, AMD Radeon AI PRO R9700 31GB, AMD Radeon AI PRO R9700 31GB | 2026-06-11 |
| **Qwen3.6-35B-A3B** | 2/4 | core 2/4 | 188.86 | llama.cpp | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-13 |

## vision  (suite v1, 1 runs)

| Model | Score | Tiers | gen tok/s | Backend · Quant | Hardware | Run |
|---|---|---|---|---|---|---|
| **qwen3-vl-8b** | 24/27 | core 12/13 · hard 12/14 | 9.66 | llama.cpp · IQ4_XS | NVIDIA GeForce RTX 3080 Ti 12GB, AMD Radeon AI PRO R9700 31GB, AMD Radeon AI PRO R9700 31GB, AMD Radeon AI PRO R9700 31GB | 2026-06-11 |

