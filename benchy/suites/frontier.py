"""FRONTIER suite — harder, GRADED tasks to separate top-tier models.

The base suites saturate at the top (every good model ties at 1.0), so these tasks
return PARTIAL CREDIT — the fraction of hidden cases passed — and lean on the failure
modes frontier models still trip on:

- interpreter:     write a real expression evaluator (precedence/associativity/unary
                   minus/modulo), graded against 24 hidden expressions.
- longctx:         pull 12 facts (incl. multi-hop ones that chain two facts) out of a
                   long document salted with look-alike decoys.
- multi_incident:  a mocked-shell incident with TWO independent root causes; must find
                   and fix both, scored ALSO on how efficiently (fewer tool calls).

v2 raised the difficulty after v1 saturated (3 of 4 top models maxed it): more/nastier
interpreter expressions, multi-hop recall, and efficiency-scored triage.

Judge-free & deterministic like the rest: model code is executed against a reference,
recall answers are exact-matched, the agentic loop is scored by code. Every input is
built in-code (no fetching), so reruns are byte-identical.
"""
from __future__ import annotations
import json, re
from . import Suite, Task, register
from ..sandbox import extract_code, run_py
from .agentic import _agentic_loop  # reuse the mocked-shell multi-turn loop + tool schema


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


# ── interpreter: write evaluate(), run it on hidden expressions, grade the fraction ──
# Standard precedence, left-associative, unary minus, integer '/' and '%'. All division
# is exact, so Python's own eval gives the same integer reference value. Several cases
# (12%5*3, 2*3%4) only resolve correctly with '%' at the same precedence as '*' and '/'.
_EXPRS = [
    "2+3*4", "(2+3)*4", "2*3+4*5", "-3+5", "-(3+4)*2", "2*(3+(4*5))",
    "100/4/5", "2+3*4-10/2", "((1+2)*(3+4))", "-2*-3", "7-3-2", "2*3*4+1",
    "17%5", "100%7%4", "12%5*3", "2*3%4", "1000/8/5/5", "-(2*3)+(8/4)",
    "((1+2)*(3+(4*(5-1))))", "2+2*2+2*2*2+2", "(7-2)*(7-2)-1", "50/(2+3)/2",
    "-10+-20+-30", "3*(4+5*(6-2))",
]
_EXPECT = [int(eval(e)) for e in _EXPRS]  # our own constant expressions, safe to eval


def f_interpreter(client):
    listing = "\n".join(_EXPRS)
    prompt = (
        "Write a COMPLETE Python program defining evaluate(expr: str) -> int that "
        "evaluates an integer arithmetic expression. Support: + - * / % , parentheses, "
        "and unary minus. Rules: * / % bind tighter than + and -, all are "
        "left-associative, and '/' and '%' are INTEGER operations ('/' inputs always "
        "divide evenly). Do NOT use Python's eval or exec. Then, for each line below, "
        "print evaluate(<that line>) on its own line, in order:\n\n" + listing
    )
    out = run_py(extract_code(client.chat(
        [{"role": "user", "content": prompt}], max_tokens=4000).content))
    # take the last N non-empty lines (the program may print incidental lines first),
    # and read the trailing integer of each so "expr = 14" scores like a bare "14".
    lines = [x.strip() for x in out.strip().splitlines() if x.strip()][-len(_EXPRS):]
    got = 0
    for exp, line in zip(_EXPECT, lines):
        nums = re.findall(r"-?\d+", line)
        if nums and int(nums[-1]) == exp:
            got += 1
    return (got / len(_EXPRS), f"{got}/{len(_EXPRS)} exprs")


# ── longctx: 12 facts (incl. multi-hop) hidden in a long doc full of look-alike decoys ─
# Three regions share an attribute schema (window / on-call / failover) so a multi-hop
# question must chain one attribute to another. Each value is unique and appears once.
_PLANTED = [
    "The Helios PRODUCTION API key is HELIOS-PROD-7741.",
    "The Helios STAGING API key is HELIOS-STG-1100.",
    "The rollback build number is 5293.",
    "The previous build number was 5290.",
    "The incident bridge code is BRIDGE-8820.",
    "The status-page code is PAGE-2200.",
    "Region eu-west: maintenance window 02:00 UTC, primary on-call Priya Nair, "
    "database failover replica db-r3.",
    "Region us-east: maintenance window 14:00 UTC, primary on-call Sam Lee, "
    "database failover replica db-r9.",
    "Region ap-south: maintenance window 19:30 UTC, primary on-call Mara Ito, "
    "database failover replica db-r5.",
]
# (key, question shown to the model, verbatim expected value). The mh_* keys are
# multi-hop: the model must resolve one attribute to find the region, then read another.
_QUESTIONS = [
    ("prod_api_key",     "the Helios PRODUCTION API key",                         "HELIOS-PROD-7741"),
    ("staging_api_key",  "the Helios STAGING API key",                            "HELIOS-STG-1100"),
    ("rollback_build",   "the rollback build number",                            "5293"),
    ("previous_build",   "the previous build number",                            "5290"),
    ("bridge_code",      "the incident bridge code",                             "BRIDGE-8820"),
    ("statuspage_code",  "the status-page code",                                 "PAGE-2200"),
    ("apsouth_oncall",   "the primary on-call for region ap-south",              "Mara Ito"),
    ("euwest_failover",  "the database failover replica for region eu-west",     "db-r3"),
    ("useast_failover",  "the database failover replica for region us-east",     "db-r9"),
    ("mh_window_oncall", "the primary on-call for the region whose maintenance "
                         "window is 02:00 UTC",                                  "Priya Nair"),
    ("mh_oncall_failover", "the database failover replica for the region whose "
                           "primary on-call is Mara Ito",                        "db-r5"),
    ("mh_failover_window", "the maintenance window in UTC for the region whose "
                           "database failover replica is db-r3",                 "02:00"),
]
_WORDS = ("the system service config cluster node region metric latency request buffer "
          "cache index queue worker token window replica build deploy log alert policy "
          "budget owner vendor freeze cutover staging primary backup gateway").split()


def _filler(n_sentences, seed):
    # deterministic pseudo-random sentences (a fixed LCG) so the doc is byte-identical
    s = seed & 0xFFFFFFFF
    out = []
    for _ in range(n_sentences):
        words = []
        for _ in range(9):
            s = (1103515245 * s + 12345) & 0x7FFFFFFF
            words.append(_WORDS[s % len(_WORDS)])
        out.append(" ".join(words).capitalize() + ".")
    return out


def _build_doc():
    blocks = []
    for i, line in enumerate(_PLANTED):
        blocks.extend(_filler(16, 7 + i))  # ~2x the v1 filler, planted lines spread out
        blocks.append(line)
    blocks.extend(_filler(16, 999))
    return "\n".join(blocks)


_DOC = _build_doc()


def f_longctx(client):
    qlist = "\n".join(f'  "{k}": <{q}>' for k, q, _ in _QUESTIONS)
    r = client.chat([
        {"role": "system", "content":
            "Answer ONLY from the document below. It contains similar-looking decoys; read "
            "carefully and return the exact value asked for, not a near-match. Some questions "
            "require chaining two facts about the same region.\n\n" + _DOC},
        {"role": "user", "content":
            "Return ONLY compact JSON (no prose, no code fence) with exactly these keys, "
            "each value taken verbatim from the document:\n" + qlist}],
        max_tokens=1000)  # headroom so a verbose model isn't scored on a truncated answer
    raw = r.content.strip()
    m = re.search(r"\{.*\}", raw, re.S)
    got = 0
    if m:
        try:
            d = json.loads(m.group())
            for k, _, val in _QUESTIONS:
                if _norm(val) and _norm(val) in _norm(str(d.get(k, ""))):
                    got += 1
        except Exception:
            pass
    return (got / len(_QUESTIONS), f"{got}/{len(_QUESTIONS)} needles")


# ── multi_incident: TWO independent root causes; find/fix both, scored on efficiency ──
_INC_MAX_TURNS = 18
_INC_FAST = 6   # calls at/under this earn no efficiency penalty
_INC_FLOOR = 0.7  # a correct-but-slow solve still scores this fraction (completeness wins)

_INC_DF = ("Filesystem      Size  Used Avail Use% Mounted on\n"
           "/dev/sda1       456G  456G    0G 100% /\n"
           "tmpfs            16G  1.2M   16G   1% /run")
_INC_DU = "47G\t/var/log/app/app.log\n1.9G\t/var/log/journal\n410M\t/var/log/syslog"
_INC_STATUS = ("webapp.service - Web application\n"
               "   Active: activating (auto-restart) (Result: exit-code)\n"
               "  Process: 8120 ExecStart=/usr/bin/webapp (code=exited, status=1/FAILURE)\n"
               "webapp.service: restart counter is at 11.")
# The log shows BOTH faults at once — a full disk AND a port already held.
_INC_LOG = ("[ERROR] java.io.IOException: No space left on device (writing /var/log/app/app.log)\n"
            "[ERROR] java.net.BindException: Address already in use (bind 0.0.0.0:8080)\n"
            "[INFO] shutting down (exit 1)")
_INC_SS = ('tcp LISTEN 0 128 0.0.0.0:8080 0.0.0.0:* users:(("webapp",pid=4821,fd=12))'
           '   # a stale webapp from a prior unclean restart still holds :8080')


def _incident_shell(cmd, state):
    low = cmd.strip().lower()
    if re.search(r"\b(ping|curl|wget|nc|netcat|telnet)\b", low):
        state["wandered"] = True
        return "(no useful output - that host/service is unrelated to this task)"
    if re.search(r"\bdf\b", low):
        state["saw_df"] = True
        return _INC_DF
    if re.search(r"\bdu\b", low):
        return _INC_DU
    if "journalctl" in low or ("systemctl" in low and "status" in low):
        state["saw_log"] = True
        return _INC_STATUS + "\n" + _INC_LOG if "journalctl" in low else _INC_STATUS
    if re.search(r"\b(ss|lsof|netstat|fuser)\b", low) or "8080" in low:
        state["saw_port"] = True
        return _INC_SS
    if re.search(r"\b(ps|pgrep)\b", low) or "4821" in low:
        state["saw_port"] = True
        return "4821 /usr/bin/webapp   # stale process from a prior restart"
    if re.match(r"(ls|cat|find|grep|tail|head|stat|tree)\b", low):
        return "app/  config.yaml  logs/"
    return "(no output)"


def f_multi_incident(client):
    state = {"wandered": False, "saw_df": False, "saw_log": False, "saw_port": False}
    final, calls, txt = _agentic_loop(client,
        "You are an SRE on a Linux server. Use run_shell (one command per call) to "
        "investigate efficiently. This incident may have MORE THAN ONE root cause - find "
        "ALL of them with as few commands as possible. When done, STOP calling tools and "
        "reply in plain text listing every root cause AND a concrete fix for each.",
        "webapp.service keeps crash-looping and will not start. Find every root cause "
        "and how to fix it.",
        lambda c: _incident_shell(c, state), max_turns=_INC_MAX_TURNS)
    low = (final + "\n" + txt).lower()
    disk = (("space" in low or "disk" in low or "full" in low or "app.log" in low)
            and any(w in low for w in ("truncate", "rotate", "logrotate", "delete",
                                       "rm ", ": >", "clear", "free up")))
    port = (("already in use" in low or "8080" in low or "stale" in low or "4821" in low)
            and any(w in low for w in ("kill", "pkill", "fuser", "stop", "terminate")))
    base = 0.5 * (1 if (disk and state["saw_df"]) else 0) \
        + 0.5 * (1 if (port and state["saw_port"]) else 0)
    if state["wandered"]:
        base *= 0.5  # penalize chasing unrelated hosts/services
    # efficiency: full credit at/under _INC_FAST calls, decaying to _INC_FLOOR at the budget
    if calls <= _INC_FAST:
        eff = 1.0
    else:
        span = _INC_MAX_TURNS - _INC_FAST
        eff = max(_INC_FLOOR, 1.0 - (calls - _INC_FAST) / span * (1.0 - _INC_FLOOR))
    score = base * eff
    return (score, f"calls={calls} eff={eff:.2f} disk={disk} port={port} "
                   f"df={state['saw_df']} portseen={state['saw_port']} "
                   f"wandered={state['wandered']}")


SUITE = register(Suite(
    name="frontier", version="2", needs="text",
    blurb="Graded high-end tasks: real evaluator (24 exprs), long-context recall with "
          "multi-hop + decoys, efficiency-scored two-root-cause triage.",
    tasks=[
        Task("interpreter", "code", f_interpreter),     # executes model code (--no-exec skips)
        Task("longctx", "recall", f_longctx),
        Task("multi_incident", "agentic", f_multi_incident),
    ],
))
