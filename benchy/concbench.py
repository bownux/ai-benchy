#!/usr/bin/env python3
"""concbench — a tiny concurrency load test for an OpenAI-compatible endpoint.

benchy itself is single-stream (one request at a time), so it can't tell you how a
server behaves under load. This does: it fires N prompts through a pool of `--concurrency`
workers against /v1/chat/completions (streaming, so we can time the first token), and
reports the numbers that matter when batching: aggregate output tok/s, request
throughput, TTFT (time-to-first-token), and per-request latency — at p50/p99.

Zero dependencies (stdlib only), same spirit as benchy. Point it at vLLM, llama.cpp
(start llama-server with --parallel N or it serializes!), ollama, LM Studio, etc.

    python -m benchy.concbench --endpoint http://127.0.0.1:1234 --model Qwen3.6-27B \
        --concurrency 16 --num-prompts 64 --max-tokens 256

Sweep concurrency to find where throughput plateaus and TTFT blows up:
    for c in 1 4 8 16 32; do python -m benchy.concbench ... --concurrency $c; done
"""
from __future__ import annotations
import argparse, json, os, time, urllib.request, urllib.error, random
from concurrent.futures import ThreadPoolExecutor, as_completed

CONCRESULT_SCHEMA = "ai-benchy/concresult/1"

# A few distinct prompts so a prefix cache can't inflate throughput by serving
# every request from the same cached prefix. Each request also gets a unique nonce.
PROMPTS = [
    "Explain how a hash map works, then give a short Python example.",
    "Summarize the tradeoffs between TCP and UDP for a real-time game.",
    "Write a function that returns the nth Fibonacci number, with a docstring.",
    "Describe what happens, step by step, when you type a URL and press enter.",
    "Compare quicksort and mergesort: when would you pick each, and why?",
    "Outline a plan to migrate a monolith to microservices, with risks.",
    "What is backpropagation? Explain it to a second-year CS student.",
    "Give three ways to detect and fix a memory leak in a long-running service.",
]


def percentile(values, p):
    """Linear-interpolated percentile (p in 0..100)."""
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * (p / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def one_request(base, headers, model, prompt, max_tokens, temperature, timeout, no_think):
    """Stream one chat completion.
    Returns (ttft_s, total_s, out_tokens, ok, err, used_usage), where used_usage is
    True iff out_tokens came from the server's exact usage.completion_tokens (vs the
    streamed-delta fallback, which is only an approximation)."""
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens, "temperature": temperature, "stream": True,
        "stream_options": {"include_usage": True},
    }
    if no_think:
        # Suppress chain-of-thought so output length is bounded and TTFT is meaningful
        # (otherwise the first *visible* token only arrives after all reasoning tokens).
        body["chat_template_kwargs"] = {"enable_thinking": False}
    data = json.dumps(body).encode()
    req = urllib.request.Request(base + "/v1/chat/completions", data=data,
                                 headers=headers, method="POST")
    t0 = time.time()
    ttft = None
    chunk_tokens = 0       # streamed content deltas, used if server omits usage
    usage_tokens = None    # exact completion_tokens if the server reports it
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            for raw in r:
                line = raw.decode("utf-8", "replace").strip()
                if not line or not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                try:
                    obj = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                u = obj.get("usage")
                if u and u.get("completion_tokens") is not None:
                    usage_tokens = u["completion_tokens"]
                for ch in obj.get("choices") or []:
                    delta = ch.get("delta") or {}
                    # Count both visible content and reasoning tokens — a thinking model
                    # streams the latter first, and TTFT should mark the very first token.
                    piece = delta.get("content") or delta.get("reasoning_content")
                    if piece:
                        if ttft is None:
                            ttft = time.time() - t0
                        chunk_tokens += 1
        total = time.time() - t0
        used_usage = usage_tokens is not None
        out_tokens = usage_tokens if used_usage else chunk_tokens
        return (ttft, total, out_tokens, True, None, used_usage)
    except Exception as e:
        return (None, time.time() - t0, 0, False, str(e)[:120], False)


def main():
    ap = argparse.ArgumentParser(prog="concbench", description="concurrency load test for an OpenAI endpoint")
    ap.add_argument("--endpoint", required=True, help="base URL, e.g. http://127.0.0.1:1234")
    ap.add_argument("--model", default="benchy", help="model id to send (most servers ignore it)")
    ap.add_argument("--concurrency", type=int, default=16, help="in-flight requests at once")
    ap.add_argument("--num-prompts", type=int, default=64, help="total requests to send")
    ap.add_argument("--max-tokens", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=0.7, help="non-zero so varied prompts don't all cache-hit")
    ap.add_argument("--timeout", type=float, default=240)
    ap.add_argument("--api-key", default=None)
    ap.add_argument("--no-think", action="store_true",
                    help="send chat_template_kwargs enable_thinking=false (recommended for a "
                         "clean throughput test — bounds output length and makes TTFT meaningful)")
    ap.add_argument("--label", default=None, help="short name for this run (default: --model)")
    ap.add_argument("--out", default=None,
                    help="dir to write a concresult JSON for `python -m benchy compare-conc`")
    # Config that DOMINATES concurrency throughput but can't be read back from the API —
    # record it so the leaderboard never conflates two different server setups.
    ap.add_argument("--backend", default=None, help="vllm | llama.cpp | ollama | ...")
    ap.add_argument("--quant", default=None, help="e.g. FP8, Q4_K_M")
    ap.add_argument("--max-num-seqs", type=int, default=None,
                    help="the server's --max-num-seqs (the single biggest batching knob)")
    ap.add_argument("--notes", default=None, help="freeform (other server flags, etc.)")
    a = ap.parse_args()
    if a.concurrency < 1 or a.num_prompts < 1:
        ap.error("--concurrency and --num-prompts must be >= 1")

    base = a.endpoint.rstrip("/")
    headers = {"Content-Type": "application/json"}
    if a.api_key:
        headers["Authorization"] = f"Bearer {a.api_key}"

    rng = random.Random(1234)  # deterministic prompt selection across runs
    jobs = []
    for i in range(a.num_prompts):
        p = rng.choice(PROMPTS) + f"\n\n(request #{i})"  # nonce defeats prefix cache
        jobs.append(p)

    print(f"concbench -> {base}  model={a.model}  concurrency={a.concurrency}  "
          f"prompts={a.num_prompts}  max_tokens={a.max_tokens}")

    results = []
    wall0 = time.time()
    with ThreadPoolExecutor(max_workers=a.concurrency) as ex:
        futs = [ex.submit(one_request, base, headers, a.model, p,
                          a.max_tokens, a.temperature, a.timeout, a.no_think) for p in jobs]
        done = 0
        for f in as_completed(futs):
            results.append(f.result())
            done += 1
            if done % max(1, a.num_prompts // 10) == 0:
                print(f"  {done}/{a.num_prompts} done")
    wall = max(time.time() - wall0, 1e-9)  # guard the divisor; real runs are never ~0

    ok = [r for r in results if r[3]]
    failed = [r for r in results if not r[3]]
    out_tokens = sum(r[2] for r in ok)
    ttfts = [r[0] for r in ok if r[0] is not None]
    lats = [r[1] for r in ok]
    # Counts are EXACT only if every ok request reported usage.completion_tokens. If any
    # server omitted usage we counted streamed deltas instead (not guaranteed one token
    # each), so the rate is approximate — flag it with `~` rather than claiming tok/s.
    exact = bool(ok) and all(r[5] for r in ok)
    unit = "tok/s" if exact else "tok/s~"

    def r2(x, nd=2):
        return round(x, nd) if x is not None else None

    metrics = {
        "ok": len(ok), "failed": len(failed), "wall_s": round(wall, 1),
        "req_per_s": r2(len(ok) / wall) if wall else None,
        "agg_tok_s": r2(out_tokens / wall, 1) if wall else None,
        "out_tokens": out_tokens,
        "ttft_p50_s": r2(percentile(ttfts, 50), 3), "ttft_p99_s": r2(percentile(ttfts, 99), 3),
        "lat_p50_s": r2(percentile(lats, 50)), "lat_p99_s": r2(percentile(lats, 99)),
        "per_stream_tok_s": r2(out_tokens / sum(lats), 1) if lats and sum(lats) else None,
        "token_source": "exact" if exact else "approx",  # usage vs streamed-delta fallback
    }

    print("\n=== results ===")
    print(f"  ok={metrics['ok']}/{len(results)}  failed={metrics['failed']}  wall={metrics['wall_s']}s")
    print(f"  request throughput : {metrics['req_per_s']} req/s")
    print(f"  aggregate output   : {metrics['agg_tok_s']} {unit}  ({out_tokens} tokens total)")
    if ttfts:
        print(f"  TTFT   p50/p99     : {metrics['ttft_p50_s']}s / {metrics['ttft_p99_s']}s")
    if lats:
        print(f"  latency p50/p99    : {metrics['lat_p50_s']}s / {metrics['lat_p99_s']}s")
    print(f"  per-stream rate    : {metrics['per_stream_tok_s']} {unit}  (avg single-stream)")
    if failed:
        print(f"  first error        : {failed[0][4]}")
    src = ("exact (server usage.completion_tokens)" if exact
           else "~approx — some servers omitted usage; counted streamed deltas (not 1 token each)")
    print(f"  token source       : {src}")

    if a.out:
        _write_result(a, base, metrics)


def _write_result(a, base, metrics):
    """Write a self-describing concresult JSON for `benchy compare-conc`. Reuses benchy's
    hwinfo so the run is stamped with auto-detected hardware, like a normal benchy result."""
    try:
        from benchy import hwinfo, __version__ as bver
        hw = hwinfo.detect()
    except Exception:
        import socket
        hw, bver = {"host": socket.gethostname(), "gpu_summary": "?"}, None
    label = a.label or a.model
    run_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    config = {k: v for k, v in (("backend", a.backend), ("quant", a.quant),
                                ("max_num_seqs", a.max_num_seqs), ("max_tokens", a.max_tokens),
                                ("num_prompts", a.num_prompts), ("no_think", a.no_think),
                                ("notes", a.notes)) if v is not None}
    rec = {
        "schema": CONCRESULT_SCHEMA, "benchy_version": bver,
        "label": label, "run_at": run_at, "endpoint": base,
        "concurrency": a.concurrency, "config": config,
        "hardware": hw, "metrics": metrics,
    }
    os.makedirs(a.out, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-._" else "_" for c in label)
    fn = f"conc__{safe}__{hw.get('host', 'host')}__c{a.concurrency:02d}__{run_at.replace(':', '')}.json"
    path = os.path.join(a.out, fn)
    json.dump(rec, open(path, "w"), indent=2)
    print(f"  wrote {path}")


if __name__ == "__main__":
    main()
