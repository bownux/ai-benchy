"""REASONING suite — strict-output, exact-match tasks (no code execution).

Tests instruction-following (output ONLY what's asked), basic logic, SQL synthesis,
and needle-in-context recall. All scored by normalized match.
"""
from __future__ import annotations
import json, re
from . import Suite, Task, register


def _norm(s): return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def t_json_only(client):
    r = client.chat([{"role": "user", "content":
        "Output ONLY this as compact JSON, nothing else (no prose, no code fence): "
        "a person named alice aged 30."}], max_tokens=200)
    raw = r.content.strip()
    m = re.search(r"\{.*\}", raw, re.S)
    ok = False
    if m:
        try:
            d = json.loads(m.group())
            ok = str(d.get("name", "")).lower() == "alice" and int(d.get("age", 0)) == 30
        except Exception:
            ok = False
    return (1.0 if ok else 0.0, f"raw={raw[:50]!r}")


def t_reasoning(client):
    r = client.chat([{"role": "user", "content":
        "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. "
        "How much does the ball cost in cents? Reply with only the number of cents."}],
        max_tokens=2000)
    nums = [int(x) for x in re.findall(r"\d+", r.content or "")]
    return (1.0 if (5 in nums and 55 not in nums) else 0.0, f"raw={r.content.strip()[:50]!r}")


def t_sql(client):
    r = client.chat([{"role": "user", "content":
        "Tables: orders(id, customer_id, total), customers(id, name). Write ONE SQL "
        "query returning each customer's name and their total spend, highest first. "
        "Reply with only the SQL."}], max_tokens=500)
    low = r.content.lower()
    ok = "join" in low and "sum(" in low and "group by" in low and "order by" in low
    return (1.0 if ok else 0.0, f"clauses={ok}")


def t_recall(client):
    doc = ("Project Zephyr kickoff notes. Owner: Priya. Budget code: ZEPHYR-7741. "
           "The staging URL is https://stg.example.invalid and the cutover date is "
           "the second Tuesday of March. Risks: vendor lead time, holiday freeze.")
    r = client.chat([
        {"role": "system", "content": "Answer only from the notes.\n\n" + doc},
        {"role": "user", "content": "What is the budget code? Reply with only the code."}],
        max_tokens=200)
    return (1.0 if "zephyr7741" in _norm(r.content) else 0.0, f"raw={r.content.strip()[:40]!r}")


SUITE = register(Suite(
    name="reasoning", version="1", needs="text",
    blurb="Strict-output JSON, a logic trap, SQL synthesis, context recall.",
    tasks=[
        Task("json_only", "core", t_json_only),
        Task("reasoning", "core", t_reasoning),
        Task("sql", "core", t_sql),
        Task("recall", "core", t_recall),
    ],
))
