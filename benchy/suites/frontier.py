"""FRONTIER suite — harder, GRADED tasks to separate top-tier models.

The base suites saturate at the top (every good model scores 1.0 and ties), so these
tasks return PARTIAL CREDIT — the fraction of hidden cases passed — instead of binary
pass/fail, and they lean on the failure modes frontier models still trip on:

- interpreter:     write a real expression evaluator (precedence/associativity/unary
                   minus), scored against 12 hidden expressions.
- longctx:         pull 6 specific facts out of a long document salted with look-alike
                   decoys (tests careful long-context recall, not just "find a needle").
- multi_incident:  a mocked-shell incident with TWO independent root causes; must find
                   and propose a fix for BOTH, without wandering.

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
# Standard precedence, left-associative, unary minus, integer division. All division
# here is exact, so Python's own eval gives the same integer reference value.
_EXPRS = [
    "2+3*4", "(2+3)*4", "2*3+4*5", "-3+5", "-(3+4)*2", "2*(3+(4*5))",
    "100/4/5", "2+3*4-10/2", "((1+2)*(3+4))", "-2*-3", "7-3-2", "2*3*4+1",
]
_EXPECT = [int(eval(e)) for e in _EXPRS]  # our own constant expressions, safe to eval


def f_interpreter(client):
    listing = "\n".join(_EXPRS)
    prompt = (
        "Write a COMPLETE Python program defining evaluate(expr: str) -> int that "
        "evaluates an integer arithmetic expression. Support: + - * / , parentheses, "
        "and unary minus. Rules: standard precedence (* and / bind tighter than + and "
        "-), left-associative, and '/' is INTEGER division (inputs always divide "
        "evenly). Do NOT use Python's eval or exec. Then, for each line below, print "
        "evaluate(<that line>) on its own line, in order:\n\n" + listing
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


# ── longctx: 6 real facts hidden in a long doc full of look-alike decoys ─────────────
# (key, human-readable label, the verbatim value the model must return)
_FACTS = [
    ("prod_api_key",     "Helios PRODUCTION API key",            "HELIOS-PROD-7741"),
    ("eu_west_oncall",   "on-call engineer for region eu-west",  "Priya Nair"),
    ("maint_window_utc", "maintenance window start time in UTC", "02:00"),
    ("rollback_build",   "rollback build number",                "5293"),
    ("bridge_code",      "incident bridge code",                 "BRIDGE-8820"),
    ("failover_target",  "database failover target replica",     "db-r3"),
]
# Each decoy is a near-miss for one of the facts above — same shape, different value.
_DECOYS = [
    "The Helios STAGING API key is HELIOS-STG-1100.",
    "The on-call engineer for region us-east is Sam Lee.",
    "The deploy window starts at 14:00 UTC on weekdays.",
    "The previous build number was 5290.",
    "The status-page incident code is PAGE-2200.",
    "The database read replica for analytics is db-r9.",
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
    facts = [f"The {label} is {val}." for _, label, val in _FACTS]
    payload = facts + _DECOYS              # 12 planted lines, fact/decoy interleaved
    blocks = []
    for i, line in enumerate(payload):
        blocks.extend(_filler(12, 7 + i))  # ~12 filler sentences before each planted line
        blocks.append(line)
    blocks.extend(_filler(12, 999))
    return "\n".join(blocks)


_DOC = _build_doc()


def f_longctx(client):
    qlist = "\n".join(f'  "{k}": <{label}>' for k, label, _ in _FACTS)
    r = client.chat([
        {"role": "system", "content":
            "Answer ONLY from the document below. It contains similar-looking decoys; read "
            "carefully and return the exact value asked for, not a near-match.\n\n" + _DOC},
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
            for k, _, val in _FACTS:
                if _norm(val) and _norm(val) in _norm(str(d.get(k, ""))):
                    got += 1
        except Exception:
            pass
    return (got / len(_FACTS), f"{got}/{len(_FACTS)} needles")


# ── multi_incident: TWO independent root causes, must find and fix both ──────────────
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
        "investigate. This incident may have MORE THAN ONE root cause - find ALL of "
        "them. When done, STOP calling tools and reply in plain text listing every root "
        "cause AND a concrete fix for each.",
        "webapp.service keeps crash-looping and will not start. Find every root cause "
        "and how to fix it.",
        lambda c: _incident_shell(c, state), max_turns=18)
    low = (final + "\n" + txt).lower()
    disk = (("space" in low or "disk" in low or "full" in low or "app.log" in low)
            and any(w in low for w in ("truncate", "rotate", "logrotate", "delete",
                                       "rm ", ": >", "clear", "free up")))
    port = (("already in use" in low or "8080" in low or "stale" in low or "4821" in low)
            and any(w in low for w in ("kill", "pkill", "fuser", "stop", "terminate")))
    score = 0.5 * (1 if (disk and state["saw_df"]) else 0) \
        + 0.5 * (1 if (port and state["saw_port"]) else 0)
    if state["wandered"]:
        score *= 0.5  # penalize chasing unrelated hosts/services
    return (score, f"calls={calls} disk={disk} port={port} "
                   f"df={state['saw_df']} portseen={state['saw_port']} "
                   f"wandered={state['wandered']}")


SUITE = register(Suite(
    name="frontier", version="1", needs="text",
    blurb="Graded high-end tasks: real evaluator, long-context recall under decoys, "
          "two-root-cause triage.",
    tasks=[
        Task("interpreter", "code", f_interpreter),     # executes model code (--no-exec skips)
        Task("longctx", "recall", f_longctx),
        Task("multi_incident", "agentic", f_multi_incident),
    ],
))
