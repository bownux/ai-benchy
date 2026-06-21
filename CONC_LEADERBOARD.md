# ai-benchy concurrency leaderboard

<!-- generated: `python -m benchy compare-conc results/ > CONC_LEADERBOARD.md` -->

Aggregate output tok/s under concurrent load — higher means the server batches better. This is bound to **hardware AND server config**, so rows are grouped by backend, quant, and `max_num_seqs`; compare within a config, not across hardware.

| Model | Backend · Quant | max_seqs | Hardware | c=1 | c=4 | c=16 | c=32 | c=48 | c=64 | peak tok/s @ c |
|---|---|---|---|---|---|---|---|---|---|---|
| **Qwen3.6-27B** | vllm · FP8 | 64 | NVIDIA GeForce RTX 3090 24GB, NVIDIA RTX PRO 5000 Blackwell 47GB | 32 | 114 | 432 | 569 | 584 | 574 | 584 @ 48 |

