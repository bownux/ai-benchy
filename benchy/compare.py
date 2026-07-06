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


def _fmt(x):
    # show graded (fractional) scores without noise: 6.0 -> "6", 2.5 -> "2.5"
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return s or "0"


def _tier_str(scores):
    t = scores.get("tiers", {})
    return " · ".join(f"{k} {_fmt(v[0])}/{v[1]}" for k, v in t.items()) or "-"


def _rank(r):
    """Higher is better: score, then throughput, then most recent."""
    s = r.get("scores", {})
    return (s.get("total", 0), r.get("throughput", {}).get("gen_tps") or 0, r.get("run_at", ""))


def _dedup(rows):
    """Collapse repeat runs to the single best per (label, hardware) so re-running a
    model replaces its row rather than stacking another. Distinct labels (e.g. a
    `-nothink` variant) are kept separate. Returns (kept_rows, dropped_count)."""
    best = {}
    for r in rows:
        key = (r.get("label"), r.get("hardware", {}).get("gpu_summary"))
        if key not in best or _rank(r) > _rank(best[key]):
            best[key] = r
    return list(best.values()), len(rows) - len(best)


def leaderboard(paths):
    results = _load(paths)
    by_suite = {}
    for r in results:
        by_suite.setdefault(r.get("suite", "?"), []).append(r)
    lines = ["# ai-benchy leaderboard", ""]
    if not results:
        return "\n".join(lines + ["_no result files found._"])
    lines += ["<!-- generated: `python -m benchy compare results/ > LEADERBOARD.md` — do not hand-edit -->",
              "",
              "Scores are out of each suite's task count; tiers show the breakdown. `gen tok/s`"
              " is throughput on the **runner's** hardware (shown in the last column), so compare"
              " capability across rows and speed only within the same hardware.", ""]
    for suite in sorted(by_suite):
        rows, dropped = _dedup(by_suite[suite])
        # score desc, then tok/s desc, then label asc for a stable, deterministic order
        rows.sort(key=lambda r: (-r["scores"]["total"], -(r["throughput"].get("gen_tps") or 0),
                                 r.get("label", "")))
        ver = rows[0].get("suite_version", "?")
        runs = f"{len(rows)} runs" + (f", {dropped} older deduped" if dropped else "")
        lines += [f"## {suite}  (suite v{ver}, {runs})", "",
                  "| Model | Score | Tiers | gen tok/s | Backend · Quant | Hardware | Run |",
                  "|---|---|---|---|---|---|---|"]
        for r in rows:
            s = r["scores"]; m = r.get("model", {}) or {}
            backend = " · ".join(x for x in (m.get("backend"), m.get("quant")) if x) or "—"
            hw = r.get("hardware", {}).get("gpu_summary", "?")
            tp = r["throughput"].get("gen_tps")
            when = (r.get("run_at", "") or "")[:10]
            lines.append(f"| **{r.get('label','?')}** | {_fmt(s['total'])}/{s['max']} | {_tier_str(s)} "
                         f"| {tp if tp is not None else '—'} | {backend} | {hw} | {when} |")
        lines.append("")
    return "\n".join(lines)
