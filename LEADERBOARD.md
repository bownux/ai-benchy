# ai-benchy leaderboard

<!-- generated: `python -m benchy compare results/ > LEADERBOARD.md` — do not hand-edit -->

Scores are out of each suite's task count; tiers show the breakdown. `gen tok/s` is throughput on the **runner's** hardware (shown in the last column), so compare capability across rows and speed only within the same hardware.

## agentic  (suite v1, 22 runs, 1 older deduped)

| Model | Score | Tiers | gen tok/s | Backend · Quant | Hardware | Run |
|---|---|---|---|---|---|---|
| **gpt-oss-120b-Q8** | 4/4 | core 2/2 · agentic 2/2 | 181.88 | llama.cpp · Q8 | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **Qwen3.6-35B-A3B-UD-Q6_K_XL-nothink** | 4/4 | core 2/2 · agentic 2/2 | 173.35 | llama.cpp · UD-Q6_K_XL | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **gpt-oss-120b** | 4/4 | core 2/2 · agentic 2/2 | 172.78 | llama.cpp · MXFP4 | NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA GeForce RTX 3080 Ti 12GB, NVIDIA RTX PRO 4500 Blackwell 31GB | 2026-06-14 |
| **Qwen3.6-35B-A3B-Q6-nothink** | 4/4 | core 2/2 · agentic 2/2 | 169.59 | llama.cpp · Q6_K | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-13 |
| **Qwen3-Coder-Next-UD-Q6_K** | 4/4 | core 2/2 · agentic 2/2 | 159.49 | llama.cpp · UD-Q6_K | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **Qwen3-Coder-Next** | 4/4 | core 2/2 · agentic 2/2 | 90.16 | llama.cpp · UD-IQ4_XS | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-14 |
| **Qwen3.6-35B-A3B-UD-Q8_K_XL-nothink** | 4/4 | core 2/2 · agentic 2/2 | 82.99 | llama.cpp · UD-Q8_K_XL | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **gpt-oss-120b** | 4/4 | core 2/2 · agentic 2/2 | 78.7 | llama.cpp · MXFP4 | NVIDIA GeForce RTX 3080 Ti 12GB, AMD Radeon AI PRO R9700 31GB, AMD Radeon AI PRO R9700 31GB, AMD Radeon AI PRO R9700 31GB | 2026-06-11 |
| **Qwen3.6-35B-A3B-UD-Q8_K_XL** | 4/4 | core 2/2 · agentic 2/2 | 54.76 | llama.cpp · UD-Q8_K_XL | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **Qwen3.6-27B-nothink** | 4/4 | core 2/2 · agentic 2/2 | 46.41 | llama.cpp | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-13 |
| **Qwen3.6-27B-FP8-nothink** | 4/4 | core 2/2 · agentic 2/2 | 39.46 | vllm · FP8 | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-19 |
| **deepseek-v4-flash-iq3xxs** | 4/4 | core 2/2 · agentic 2/2 | 29.3 | llama.cpp · UD-IQ3_XXS | NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB | 2026-07-10 |
| **deepseek-v4-flash-q4kxl-spill** | 4/4 | core 2/2 · agentic 2/2 | 22.2 | llama.cpp · UD-Q4_K_XL | NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB | 2026-07-11 |
| **Qwen3.6-27B-BF16-nothink** | 4/4 | core 2/2 · agentic 2/2 | 18.63 | llama.cpp · BF16 | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **Qwen3.6-35B-A3B-UD-Q6_K_XL** | 3/4 | core 1/2 · agentic 2/2 | 218.25 | llama.cpp · UD-Q6_K_XL | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **Qwen3.6-35B-A3B** | 3/4 | core 1/2 · agentic 2/2 | 193.8 | llama.cpp | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-13 |
| **Qwen3.6-27B** | 3/4 | core 1/2 · agentic 2/2 | 64.86 | llama.cpp | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-13 |
| **Qwen3.6-27B-FP8** | 3/4 | core 2/2 · agentic 1/2 | 59.52 | vllm · FP8 | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-19 |
| **gemma-4-31B-UD-Q8_K_XL** | 3/4 | core 2/2 · agentic 1/2 | 38.29 | llama.cpp · UD-Q8_K_XL | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **gemma-4-31B** | 3/4 | core 2/2 · agentic 1/2 | 31.51 | llama.cpp · Q8_0 | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-21 |
| **gemma-4-31B-UD-Q8_K_XL** | 3/4 | core 2/2 · agentic 1/2 | 30.35 | llama.cpp · UD-Q8_K_XL | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-21 |
| **Qwen3.6-27B-BF16** | 2/4 | core 1/2 · agentic 1/2 | 27.82 | llama.cpp · BF16 | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |

## coding  (suite v1, 22 runs, 1 older deduped)

| Model | Score | Tiers | gen tok/s | Backend · Quant | Hardware | Run |
|---|---|---|---|---|---|---|
| **gpt-oss-120b** | 6/6 | code 2/2 · hard 4/4 | 172.81 | llama.cpp · MXFP4 | NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA GeForce RTX 3080 Ti 12GB, NVIDIA RTX PRO 4500 Blackwell 31GB | 2026-06-14 |
| **Qwen3-Coder-Next-UD-Q6_K** | 6/6 | code 2/2 · hard 4/4 | 156.69 | llama.cpp · UD-Q6_K | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **gpt-oss-120b** | 6/6 | code 2/2 · hard 4/4 | 93.45 | llama.cpp · MXFP4 | NVIDIA GeForce RTX 3080 Ti 12GB, AMD Radeon AI PRO R9700 31GB, AMD Radeon AI PRO R9700 31GB, AMD Radeon AI PRO R9700 31GB | 2026-06-11 |
| **gemma-4-31B-UD-Q8_K_XL** | 6/6 | code 2/2 · hard 4/4 | 38.94 | llama.cpp · UD-Q8_K_XL | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **gemma-4-31B** | 6/6 | code 2/2 · hard 4/4 | 31.46 | llama.cpp · Q8_0 | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-21 |
| **gemma-4-31B-UD-Q8_K_XL** | 6/6 | code 2/2 · hard 4/4 | 30.18 | llama.cpp · UD-Q8_K_XL | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-21 |
| **deepseek-v4-flash-iq3xxs** | 6/6 | code 2/2 · hard 4/4 | 29.21 | llama.cpp · UD-IQ3_XXS | NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB | 2026-07-10 |
| **deepseek-v4-flash-q4kxl-spill** | 6/6 | code 2/2 · hard 4/4 | 22.12 | llama.cpp · UD-Q4_K_XL | NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB | 2026-07-11 |
| **Qwen3.6-35B-A3B** | 5/6 | code 2/2 · hard 3/4 | 198.43 | llama.cpp | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-13 |
| **Qwen3.6-35B-A3B-UD-Q6_K_XL** | 5/6 | code 1/2 · hard 4/4 | 196.47 | llama.cpp · UD-Q6_K_XL | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **gpt-oss-120b-Q8** | 5/6 | code 2/2 · hard 3/4 | 184.44 | llama.cpp · Q8 | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **Qwen3.6-35B-A3B-UD-Q6_K_XL-nothink** | 5/6 | code 2/2 · hard 3/4 | 175.02 | llama.cpp · UD-Q6_K_XL | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **Qwen3.6-35B-A3B-Q6-nothink** | 5/6 | code 2/2 · hard 3/4 | 171.0 | llama.cpp · Q6_K | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-13 |
| **Qwen3-Coder-Next** | 5/6 | code 1/2 · hard 4/4 | 118.22 | llama.cpp · UD-IQ4_XS | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-14 |
| **Qwen3.6-35B-A3B-UD-Q8_K_XL-nothink** | 5/6 | code 2/2 · hard 3/4 | 80.62 | llama.cpp · UD-Q8_K_XL | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **Qwen3.6-35B-A3B-UD-Q8_K_XL** | 5/6 | code 1/2 · hard 4/4 | 69.16 | llama.cpp · UD-Q8_K_XL | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **Qwen3.6-27B** | 5/6 | code 1/2 · hard 4/4 | 64.15 | llama.cpp | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-13 |
| **Qwen3.6-27B-nothink** | 5/6 | code 2/2 · hard 3/4 | 44.93 | llama.cpp | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-13 |
| **Qwen3.6-27B-FP8-nothink** | 5/6 | code 2/2 · hard 3/4 | 33.58 | vllm · FP8 | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-19 |
| **Qwen3.6-27B-BF16** | 5/6 | code 1/2 · hard 4/4 | 28.01 | llama.cpp · BF16 | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **Qwen3.6-27B-BF16-nothink** | 5/6 | code 2/2 · hard 3/4 | 18.63 | llama.cpp · BF16 | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **Qwen3.6-27B-FP8** | 4/6 | code 2/2 · hard 2/4 | 60.13 | vllm · FP8 | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-19 |

## frontier  (suite v2, 5 runs)

| Model | Score | Tiers | gen tok/s | Backend · Quant | Hardware | Run |
|---|---|---|---|---|---|---|
| **gpt-oss-120b-Q8** | 3/3 | code 1/1 · recall 1/1 · agentic 1/1 | 182.51 | llama.cpp · Q8 | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **gemma-4-31B-UD-Q8_K_XL-nothink** | 2.96/3 | code 0.96/1 · recall 1/1 · agentic 1/1 | 39.05 | llama.cpp · UD-Q8_K_XL | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **Qwen3.6-35B-A3B-UD-Q6_K_XL-nothink** | 2.7/3 | code 1/1 · recall 1/1 · agentic 0.7/1 | 249.61 | llama.cpp · UD-Q6_K_XL | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **Qwen3-Coder-Next-UD-Q6_K** | 2.7/3 | code 1/1 · recall 1/1 · agentic 0.7/1 | 183.75 | llama.cpp · UD-Q6_K | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **Qwen3.6-27B-BF16-nothink** | 2/3 | code 1/1 · recall 1/1 · agentic 0/1 | 23.86 | llama.cpp · BF16 | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |

## reasoning  (suite v1, 23 runs, 1 older deduped)

| Model | Score | Tiers | gen tok/s | Backend · Quant | Hardware | Run |
|---|---|---|---|---|---|---|
| **gpt-oss-120b-Q8** | 4/4 | core 4/4 | 182.05 | llama.cpp · Q8 | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **Qwen3.6-35B-A3B-UD-Q6_K_XL-nothink** | 4/4 | core 4/4 | 177.95 | llama.cpp · UD-Q6_K_XL | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **gpt-oss-120b** | 4/4 | core 4/4 | 172.87 | llama.cpp · MXFP4 | NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA GeForce RTX 3080 Ti 12GB, NVIDIA RTX PRO 4500 Blackwell 31GB | 2026-06-14 |
| **Qwen3.6-35B-A3B-Q6-nothink** | 4/4 | core 4/4 | 168.77 | llama.cpp · Q6_K | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-13 |
| **Qwen3-Coder-Next-UD-Q6_K** | 4/4 | core 4/4 | 163.25 | llama.cpp · UD-Q6_K | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **Qwen3-Coder-Next** | 4/4 | core 4/4 | 126.21 | llama.cpp · UD-IQ4_XS | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-14 |
| **Qwen3.6-35B-A3B-UD-Q8_K_XL-nothink** | 4/4 | core 4/4 | 80.8 | llama.cpp · UD-Q8_K_XL | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **Qwen3.6-27B-nothink** | 4/4 | core 4/4 | 45.08 | llama.cpp | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-13 |
| **gemma-4-31B-UD-Q8_K_XL** | 4/4 | core 4/4 | 38.81 | llama.cpp · UD-Q8_K_XL | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **Qwen3.6-27B-FP8-nothink** | 4/4 | core 4/4 | 38.74 | vllm · FP8 | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-19 |
| **gemma-4-31B** | 4/4 | core 4/4 | 31.52 | llama.cpp · Q8_0 | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-21 |
| **gemma-4-31B-UD-Q8_K_XL** | 4/4 | core 4/4 | 30.07 | llama.cpp · UD-Q8_K_XL | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-21 |
| **deepseek-v4-flash-iq3xxs** | 4/4 | core 4/4 | 21.94 | llama.cpp · UD-IQ3_XXS | NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB | 2026-07-10 |
| **deepseek-v4-flash-q4kxl-spill** | 4/4 | core 4/4 | 21.46 | llama.cpp · UD-Q4_K_XL | NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB | 2026-07-11 |
| **Qwen3.6-27B-BF16-nothink** | 4/4 | core 4/4 | 18.64 | llama.cpp · BF16 | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **glm-5.2-iq1s** | 4/4 | core 4/4 | — | llama.cpp · UD-IQ1_S | NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB | 2026-07-10 |
| **gpt-oss-120b** | 3/4 | core 3/4 | 91.81 | llama.cpp · MXFP4 | NVIDIA GeForce RTX 3080 Ti 12GB, AMD Radeon AI PRO R9700 31GB, AMD Radeon AI PRO R9700 31GB, AMD Radeon AI PRO R9700 31GB | 2026-06-11 |
| **Qwen3.6-35B-A3B-UD-Q6_K_XL** | 2/4 | core 2/4 | 190.41 | llama.cpp · UD-Q6_K_XL | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **Qwen3.6-35B-A3B** | 2/4 | core 2/4 | 188.86 | llama.cpp | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-13 |
| **Qwen3.6-35B-A3B-UD-Q8_K_XL** | 2/4 | core 2/4 | 48.96 | llama.cpp · UD-Q8_K_XL | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |
| **Qwen3.6-27B** | 1/4 | core 1/4 | 63.37 | llama.cpp | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-13 |
| **Qwen3.6-27B-FP8** | 1/4 | core 1/4 | 58.07 | vllm · FP8 | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 2026-06-19 |
| **Qwen3.6-27B-BF16** | 1/4 | core 1/4 | 27.87 | llama.cpp · BF16 | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 6000 Blackwell Workstation Edition 95GB | 2026-06-22 |

## vision  (suite v1, 2 runs)

| Model | Score | Tiers | gen tok/s | Backend · Quant | Hardware | Run |
|---|---|---|---|---|---|---|
| **qwen3-vl-8b** | 24/27 | core 12/13 · hard 12/14 | 144.89 | llama.cpp · IQ4_XS | NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA RTX PRO 4500 Blackwell 31GB, NVIDIA GeForce RTX 3080 Ti 12GB, NVIDIA RTX PRO 4500 Blackwell 31GB | 2026-06-14 |
| **qwen3-vl-8b** | 24/27 | core 12/13 · hard 12/14 | 119.49 | llama.cpp · IQ4_XS | NVIDIA GeForce RTX 3080 Ti 12GB, AMD Radeon AI PRO R9700 31GB, AMD Radeon AI PRO R9700 31GB, AMD Radeon AI PRO R9700 31GB | 2026-06-13 |

