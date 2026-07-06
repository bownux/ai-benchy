"""Run a suite against an endpoint and write a self-describing result file.

The result JSON is the unit of sharing: it carries the scores, the per-task detail,
the measured throughput, the model metadata you pass in, AND the auto-detected
hardware — so anyone can drop it next to theirs and `benchy compare` them fairly.
"""
from __future__ import annotations
import json, os, time
from . import __version__, RESULT_SCHEMA
from . import hwinfo
from .client import Client
from .suites import get


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _fmt(x):
    # show graded (fractional) scores without noise: 6.0 -> "6", 2.5 -> "2.5"
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return s or "0"


def run_suite(suite_name, endpoint, label, model_meta=None, out_dir="results",
              skip_exec=False, api_key=None, model_name="benchy", quiet=False, no_think=False):
    suite = get(suite_name)
    client = Client(endpoint, api_key=api_key, model=model_name, no_think=no_think)
    if not client.health():
        raise SystemExit(f"endpoint not reachable: {endpoint}")
    hw = hwinfo.detect()
    served = client.served_model_id()
    if not quiet:
        print(f"\n=== {suite.name} v{suite.version} · {label} · {endpoint} ===")
        print(f"    served={served}  hw={hw['gpu_summary']}")

    tputs = []
    tier_tot, tier_max = {}, {}
    tasks_out, total = [], 0.0
    for task in suite.tasks:
        if skip_exec and task.tier == "code":
            continue
        t0 = time.time()
        client.last_finish_reason = None
        try:
            score, detail = task.run(client)
        except Exception as e:
            score, detail = 0.0, "EXC:" + str(e)[:100]
        dt = round(time.time() - t0, 1)
        fr = client.last_finish_reason
        # `length` means the model hit max_tokens before finishing — an empty/wrong
        # answer here is a truncation, not (necessarily) a capability failure. Flag it
        # so a reasoning model's overflowed budget doesn't read as a plain miss.
        if fr == "length":
            detail = (detail + " [trunc:length]") if detail else "[trunc:length]"
        total += score
        tier_tot[task.tier] = tier_tot.get(task.tier, 0.0) + score
        tier_max[task.tier] = tier_max.get(task.tier, 0) + 1
        tasks_out.append({"id": task.id, "tier": task.tier, "score": score,
                          "latency_s": dt, "finish_reason": fr, "detail": detail})
        if not quiet:
            print(f"  [{task.tier:<7}] {task.id:<16} {_fmt(score):<4} {detail[:56]}  {dt}s")

    n = len(tasks_out)
    tput = client.measure_throughput()
    result = {
        "schema": RESULT_SCHEMA, "benchy_version": __version__,
        "suite": suite.name, "suite_version": suite.version,
        "label": label, "run_at": _now_iso(),
        "endpoint": endpoint, "served_model_id": served,
        "model": model_meta or {},
        "options": {"no_think": no_think},
        "hardware": hw,
        "scores": {"total": round(total, 2), "max": n,
                   "tiers": {t: [round(tier_tot[t], 2), tier_max[t]] for t in tier_tot}},
        "throughput": tput,
        "tasks": tasks_out,
    }
    os.makedirs(out_dir, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-._" else "_" for c in label)
    path = os.path.join(out_dir, f"{suite.name}__{safe}__{hw['host']}__{result['run_at'].replace(':','')}.json")
    json.dump(result, open(path, "w"), indent=2)
    if not quiet:
        tiers = "  ".join(f"{t} {_fmt(tier_tot[t])}/{tier_max[t]}" for t in sorted(tier_tot))
        print(f"SCORE: {_fmt(total)}/{n}   {tiers}   |   gen ~{tput.get('gen_tps')} tok/s")
        print(f"wrote {path}")
    return result, path
