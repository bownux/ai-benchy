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
import argparse, json, time, urllib.request, urllib.error, random
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    """Stream one chat completion. Returns (ttft_s, total_s, out_tokens, ok, err)."""
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
        out_tokens = usage_tokens if usage_tokens is not None else chunk_tokens
        return (ttft, total, out_tokens, True, None)
    except Exception as e:
        return (None, time.time() - t0, 0, False, str(e)[:120])


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
    a = ap.parse_args()

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
    wall = time.time() - wall0

    ok = [r for r in results if r[3]]
    failed = [r for r in results if not r[3]]
    out_tokens = sum(r[2] for r in ok)
    ttfts = [r[0] for r in ok if r[0] is not None]
    lats = [r[1] for r in ok]

    print("\n=== results ===")
    print(f"  ok={len(ok)}/{len(results)}  failed={len(failed)}  wall={wall:.1f}s")
    print(f"  request throughput : {len(ok) / wall:.2f} req/s")
    print(f"  aggregate output   : {out_tokens / wall:.1f} tok/s  ({out_tokens} tokens total)")
    if ttfts:
        print(f"  TTFT   p50/p99     : {percentile(ttfts, 50):.3f}s / {percentile(ttfts, 99):.3f}s")
    if lats:
        print(f"  latency p50/p99    : {percentile(lats, 50):.2f}s / {percentile(lats, 99):.2f}s")
    per_req = out_tokens / sum(lats) if lats and sum(lats) else 0
    print(f"  per-stream tok/s   : {per_req:.1f} tok/s  (avg single-stream gen rate)")
    if failed:
        print(f"  first error        : {failed[0][4]}")
    note = "exact (usage)" if any(r[2] for r in ok) else "n/a"
    print(f"  token count source : {note}; set a non-zero --concurrency sweep to find the plateau.")


if __name__ == "__main__":
    main()
