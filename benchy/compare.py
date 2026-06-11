"""Merge result files into a Markdown leaderboard — the whole point of the project.

Drop everyone's result JSONs into results/ (or a shared folder) and run
`benchy compare results/` to get one comparable table per suite, sorted by score,
showing model, quant/backend, hardware, throughput, and per-tier breakdown.
"""
from __future__ import annotations
import glob, json, os


def _load(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            out += _load(sorted(glob.glob(os.path.join(p, "*.json"))))
        else:
            try:
                out.append(json.load(open(p)))
            except Exception:
                pass
    return out


def _tier_str(scores):
    t = scores.get("tiers", {})
    return " · ".join(f"{k} {v[0]:.0f}/{v[1]}" for k, v in t.items()) or "-"


def leaderboard(paths):
    results = _load(paths)
    by_suite = {}
    for r in results:
        by_suite.setdefault(r.get("suite", "?"), []).append(r)
    lines = ["# ai-benchy leaderboard", ""]
    for suite in sorted(by_suite):
        rows = by_suite[suite]
        rows.sort(key=lambda r: (r["scores"]["total"], r["throughput"].get("gen_tps") or 0), reverse=True)
        ver = rows[0].get("suite_version", "?")
        lines += [f"## {suite}  (suite v{ver}, {len(rows)} runs)", "",
                  "| Model | Score | Tiers | gen tok/s | Backend · Quant | Hardware | Run |",
                  "|---|---|---|---|---|---|---|"]
        for r in rows:
            s = r["scores"]; m = r.get("model", {}) or {}
            backend = " · ".join(x for x in (m.get("backend"), m.get("quant")) if x) or "—"
            hw = r.get("hardware", {}).get("gpu_summary", "?")
            tp = r["throughput"].get("gen_tps")
            when = (r.get("run_at", "") or "")[:10]
            lines.append(f"| **{r.get('label','?')}** | {s['total']:.0f}/{s['max']} | {_tier_str(s)} "
                         f"| {tp if tp is not None else '—'} | {backend} | {hw} | {when} |")
        lines.append("")
    if len(results) == 0:
        lines.append("_no result files found._")
    return "\n".join(lines)
