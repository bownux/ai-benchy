#!/usr/bin/env python3
"""Concurrent-throughput probe for an OpenAI-compatible endpoint (llama.cpp etc.).

WHY THIS EXISTS
---------------
Single-stream decode tok/s is memory-bandwidth-bound on the WEIGHTS: every decode
step streams all ~59 GiB of model weights through the GPU once to produce ONE token.
With layer-split across N GPUs and no NVLink, only one GPU is active at a time per
stream, so adding GPUs buys VRAM, not single-stream speed (this is the ~2x ceiling we
saw post-migration).

Continuous batching changes the accounting: the server reads those same weights once
to advance EVERY active slot by a token. So AGGREGATE tok/s should scale ~linearly
with the number of concurrent streams until you hit a compute wall or run out of
slots (--parallel). This probe fires N identical sustained generations at the same
instant and reports aggregate vs per-stream tok/s across a concurrency sweep, so you
can see exactly where the curve bends and what the real aggregate ceiling is.

USAGE
-----
    python concurrency_probe.py --endpoint http://127.0.0.1:8080 \
        --concurrencies 1,2,4,6,8 --max-tokens 512 --label gpt-oss-120b

Reads server-reported `timings` (llama.cpp) for exact per-stream tok/s; falls back to
wall-clock. Writes a JSON next to the suite results for the record.
"""
from __future__ import annotations
import argparse, json, os, sys, threading, time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from benchy.client import Client          # noqa: E402
from benchy import hwinfo                  # noqa: E402

DEFAULT_PROMPT = (
    "Write a thorough, multi-paragraph technical explanation (about 400 words) of how "
    "a modern CPU executes instructions out of order: cover the reorder buffer, "
    "reservation stations, register renaming, branch prediction, speculative execution, "
    "and how results are retired in program order. Be precise and detailed."
)


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def one_stream(client, prompt, max_tokens, barrier):
    """Block on the barrier so all streams hit the server together, then generate."""
    barrier.wait()
    t0 = time.time()
    r = client.chat([{"role": "user", "content": prompt}], max_tokens=max_tokens)
    t1 = time.time()
    n = r.timings.get("predicted_n") or r.usage.get("completion_tokens") or 0
    return {
        "start": t0, "end": t1, "tokens": int(n),
        "server_tps": r.gen_tps(),            # per-stream tok/s as the server timed it
        "finish_reason": r.finish_reason,
    }


def run_level(endpoint, model, concurrency, prompt, max_tokens, timeout):
    """Fire `concurrency` simultaneous generations; return aggregate + per-stream stats."""
    barrier = threading.Barrier(concurrency)
    clients = [Client(endpoint, model=model, timeout=timeout) for _ in range(concurrency)]
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs = [ex.submit(one_stream, clients[i], prompt, max_tokens, barrier)
                for i in range(concurrency)]
        rows = [f.result() for f in futs]
    ok = [r for r in rows if r["tokens"] > 0]
    if not ok:
        return {"concurrency": concurrency, "error": "no tokens generated"}
    window = max(r["end"] for r in ok) - min(r["start"] for r in ok)
    total_tokens = sum(r["tokens"] for r in ok)
    server_tps = [r["server_tps"] for r in ok if r["server_tps"]]
    return {
        "concurrency": concurrency,
        "streams_ok": len(ok),
        "wall_window_s": round(window, 3),
        "total_tokens": total_tokens,
        "aggregate_tps": round(total_tokens / window, 2) if window > 0 else None,
        "mean_per_stream_tps": round(sum(server_tps) / len(server_tps), 2) if server_tps else None,
        "min_per_stream_tps": round(min(server_tps), 2) if server_tps else None,
        "max_per_stream_tps": round(max(server_tps), 2) if server_tps else None,
        "truncated": sum(1 for r in ok if r["finish_reason"] == "length"),
    }


def main():
    ap = argparse.ArgumentParser(description="Concurrent-throughput sweep for an LLM endpoint")
    ap.add_argument("--endpoint", default="http://127.0.0.1:8080")
    ap.add_argument("--model", default="benchy")
    ap.add_argument("--label", default="model")
    ap.add_argument("--concurrencies", default="1,2,4,6,8",
                    help="comma list of concurrency levels to sweep")
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--out", default="results")
    ap.add_argument("--prompt", default=DEFAULT_PROMPT)
    a = ap.parse_args()

    levels = [int(x) for x in a.concurrencies.split(",") if x.strip()]
    probe = Client(a.endpoint, model=a.model)
    if not probe.health():
        sys.exit(f"endpoint not reachable: {a.endpoint}")
    hw = hwinfo.detect()
    print(f"\n=== concurrency sweep · {a.label} · {a.endpoint} ===")
    print(f"    hw={hw['gpu_summary']}  max_tokens={a.max_tokens}\n")
    print(f"{'conc':>4} {'agg tok/s':>10} {'per-stream':>11} {'scale':>7} "
          f"{'eff%':>6} {'window s':>9} {'trunc':>6}")
    print("-" * 62)

    results, base = [], None
    for c in levels:
        r = run_level(a.endpoint, a.model, c, a.prompt, a.max_tokens, a.timeout)
        results.append(r)
        if r.get("error"):
            print(f"{c:>4}  ERROR: {r['error']}")
            continue
        agg = r["aggregate_tps"]
        if base is None:
            base = agg
        scale = agg / base if base else 0
        eff = 100 * scale / c                     # % of ideal linear scaling
        print(f"{c:>4} {agg:>10.1f} {r['mean_per_stream_tps']:>11.1f} "
              f"{scale:>6.2f}x {eff:>5.0f}% {r['wall_window_s']:>9.2f} {r['truncated']:>6}")

    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, f"concurrency__{a.label}__{hw['host']}__{_now_iso().replace(':','')}.json")
    json.dump({"kind": "concurrency_sweep", "run_at": _now_iso(), "label": a.label,
               "endpoint": a.endpoint, "max_tokens": a.max_tokens, "hardware": hw,
               "levels": results}, open(path, "w"), indent=2)
    print(f"\nwrote {path}")
    print("\nReading the table: 'scale' = aggregate vs the C=1 baseline; 'eff%' = how close "
          "to ideal linear scaling.\nA bend toward 100%->lower marks the slot ceiling "
          "(--parallel) or a compute wall.")


if __name__ == "__main__":
    main()
