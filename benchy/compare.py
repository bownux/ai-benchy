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
            lines.append(f"| **{r.get('label','?')}** | {s['total']:.0f}/{s['max']} | {_tier_str(s)} "
                         f"| {tp if tp is not None else '—'} | {backend} | {hw} | {when} |")
        lines.append("")
    return "\n".join(lines)


# ── concurrency leaderboard (from `benchy.concbench --out` files) ────────────
CONCRESULT_SCHEMA = "ai-benchy/concresult/1"


def _conc_sig(r):
    """Group key: throughput under load is bound to BOTH hardware and server config,
    so a different backend/quant/max_num_seqs is a different row — never conflated."""
    c = r.get("config", {})
    return (r.get("label", "?"), r.get("hardware", {}).get("gpu_summary", "?"),
            c.get("backend"), c.get("quant"), c.get("max_num_seqs"), c.get("no_think"))


def _agg(r):
    return r.get("metrics", {}).get("agg_tok_s") or 0


def conc_leaderboard(paths):
    rows = [r for r in _load(paths) if r.get("schema") == CONCRESULT_SCHEMA]
    lines = ["# ai-benchy concurrency leaderboard", ""]
    if not rows:
        return "\n".join(lines + ["_no concurrency results found — generate with "
                                  "`python -m benchy.concbench --out results/ ...`._"])
    # group by config, then keep the best run per concurrency level within each group
    groups, levels = {}, set()
    for r in rows:
        g = groups.setdefault(_conc_sig(r), {})
        c = r.get("concurrency")
        levels.add(c)
        if c not in g or _agg(r) > _agg(g[c]):
            g[c] = r
    levels = sorted(x for x in levels if x is not None)

    lines += ["<!-- generated: `python -m benchy compare-conc results/ > CONC_LEADERBOARD.md` -->", "",
              "Aggregate output tok/s under concurrent load — higher means the server batches "
              "better. This is bound to **hardware AND server config**, so rows are grouped by "
              "backend, quant, and `max_num_seqs`; compare within a config, not across hardware.", ""]
    head = ["Model", "Backend · Quant", "max_seqs", "Hardware"] + \
           [f"c={c}" for c in levels] + ["peak tok/s @ c"]
    lines += ["| " + " | ".join(head) + " |", "|" + "|".join(["---"] * len(head)) + "|"]

    def peak(g):
        best = max(g.values(), key=_agg)
        return _agg(best), best.get("concurrency")

    for sig in sorted(groups, key=lambda s: -peak(groups[s])[0]):
        g = groups[sig]
        label, hw, backend, quant, mseq, _ = sig
        bq = " · ".join(x for x in (backend, quant) if x) or "—"
        cells = [f"{_agg(g[c]):.0f}" if c in g else "—" for c in levels]
        pk_v, pk_c = peak(g)
        row = [f"**{label}**", bq, str(mseq) if mseq is not None else "—", hw] + \
              cells + [f"{pk_v:.0f} @ {pk_c}"]
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    return "\n".join(lines)
