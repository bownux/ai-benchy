"""AGENTIC suite — does the model use tools and reach the right conclusion?

- tool_call: emits a valid OpenAI tool_call to a schema (the single biggest predictor
  of whether a model works in an agent loop at all).
- doc_follow: reads a whole fictional CLI's docs and follows the non-obvious rule
  instead of hallucinating a plausible-but-wrong command.
- disk_full / crash_loop: a real multi-turn loop against a MOCKED shell. Scores
  whether the model investigates with the right commands, finds the actual root
  cause, proposes a fix, and DOESN'T wander off (ping/curl an unrelated thing) or
  loop forever. Scenarios are generic infra incidents — no private hosts/services.
"""
from __future__ import annotations
import json, re
from . import Suite, Task, register

_SHELL_TOOL = [{"type": "function", "function": {
    "name": "run_shell",
    "description": "Run a shell command on this Linux server and return its stdout.",
    "parameters": {"type": "object",
        "properties": {"command": {"type": "string", "description": "the shell command"}},
        "required": ["command"]}}}]


# ── tool_call ────────────────────────────────────────────────────────────────
def t_toolcall(client):
    tools = [{"type": "function", "function": {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "parameters": {"type": "object", "properties": {
            "city": {"type": "string"}, "unit": {"type": "string", "enum": ["c", "f"]}},
            "required": ["city"]}}}]
    r = client.chat([{"role": "user", "content": "What's the weather in Tokyo in celsius? Use the tool."}],
                    max_tokens=300, tools=tools)
    ok, detail = False, "no tool_call"
    for tc in (r.tool_calls or []):
        if tc.get("function", {}).get("name") == "get_weather":
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
                ok = "tokyo" in str(args.get("city", "")).lower()
                detail = f"args={args}"
            except Exception:
                detail = "bad args json"
    return (1.0 if ok else 0.0, detail)


# ── doc_follow (read the WHOLE doc, don't hallucinate) ───────────────────────
_TOOL_DOC = """# orchard — internal deploy CLI (v4)
# Deploys are CHANNEL-scoped. You MUST pass --channel; there is no default and
# omitting it is rejected. Valid channels: edge, beta, stable.
#   orchard release --channel <name> --build <id>
# NOTE: `orchard deploy` was REMOVED in v3 — it now errors. Use `release`.
# Rollback:  orchard release --channel <name> --build previous
"""
def a_doc_follow(client):
    r = client.chat([
        {"role": "system", "content": "These tool docs are authoritative. Follow them exactly.\n\n" + _TOOL_DOC},
        {"role": "user", "content": "What command deploys build 1234 to the beta channel? Give only the command."}],
        max_tokens=400)
    low = r.content.lower().replace(" ", "")
    # must use `release --channel beta ... 1234` and NOT fall back to the removed `deploy`
    ok = "orchardrelease" in low and "--channelbeta" in low and "1234" in low and "orcharddeploy" not in low
    return (1.0 if ok else 0.0, f"raw={r.content.strip()[:60]!r}")


# ── multi-turn tool loop ─────────────────────────────────────────────────────
def _agentic_loop(client, system, user, tool_impl, max_turns=14):
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    calls, final, texts = 0, "", []
    for _ in range(max_turns):
        r = client.chat(msgs, max_tokens=1200, tools=_SHELL_TOOL)
        tcs = r.tool_calls or []
        if r.content.strip():
            texts.append(r.content.strip())
        am = {"role": "assistant", "content": r.content}
        if tcs:
            am["tool_calls"] = tcs
        msgs.append(am)
        if not tcs:
            final = r.content
            break
        for tc in tcs:
            calls += 1
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except Exception:
                args = {}
            msgs.append({"role": "tool", "tool_call_id": tc.get("id", ""),
                         "content": tool_impl(args.get("command", ""))})
    if not final:  # ran out of tool budget — force a plain-text conclusion (like real frameworks)
        msgs.append({"role": "user", "content":
            "You've reached the tool-call limit. Based on what you found, answer the original "
            "question now in plain text (do not call any tools)."})
        r = client.chat(msgs, max_tokens=1200)
        final = r.content or "(no answer)"
        if final.strip():
            texts.append(final.strip())
    return final, calls, "\n".join(texts)


def _wandered(low, state):
    if re.search(r"\b(ping|curl|wget|nc|netcat|telnet)\b", low):
        state["wandered"] = True
        return "(no useful output — that host/service is unrelated to this task)"
    return None


_DF = ("Filesystem      Size  Used Avail Use% Mounted on\n"
       "/dev/sda1       456G  456G    0G 100% /\n"
       "tmpfs            16G  1.2M   16G   1% /run")
_DU = "48G\t/var/log/app/app.log\n2.1G\t/var/log/journal\n390M\t/var/log/syslog\n12M\t/var/log/auth.log"

def _disk_shell(cmd, state):
    low = cmd.strip().lower()
    w = _wandered(low, state)
    if w: return w
    if re.search(r"\bdf\b", low):
        state["saw_df"] = True; return _DF
    if re.search(r"\bdu\b", low):
        state["saw_du"] = True; return _DU
    if re.match(r"(ls|find|stat|tree)\b", low):
        return "app/  data/  var/"
    if re.match(r"(cat|less|head|tail|grep|awk|sed)\b", low):
        return "(text file)"
    return "(no output)"

def a_disk_full(client):
    state = {"wandered": False, "saw_df": False, "saw_du": False}
    final, calls, txt = _agentic_loop(client,
        "You are an SRE on a Linux server. Use run_shell (one command per call) to "
        "investigate. As SOON as you find the culprit, STOP calling tools and reply "
        "in plain text with the culprit AND a concrete fix.",
        "The root filesystem is 100% full. What is using the space, and how do I fix it?",
        lambda c: _disk_shell(c, state))
    low = (final + "\n" + txt).lower()
    culprit = ("app.log" in low) or ("/var/log/app" in low) or ("48g" in low)
    fix = any(w in low for w in ("truncate", "rotate", "logrotate", "delete", "rm ", ": >", "empty", "clear"))
    ok = culprit and fix and state["saw_df"] and not state["wandered"]
    return (1.0 if ok else 0.0,
            f"calls={calls} df={state['saw_df']} culprit={culprit} fix={fix} wandered={state['wandered']}")


_STATUS = """webapp.service - Web application
   Active: activating (auto-restart) (Result: exit-code)
  Process: 8120 ExecStart=/usr/bin/webapp (code=exited, status=1/FAILURE)
webapp.service: Scheduled restart job, restart counter is at 9."""
_LOG = """[INFO] webapp starting, binding 0.0.0.0:8080
[ERROR] java.net.BindException: Address already in use
[INFO] shutting down (exit 1)"""
_SS = ('tcp LISTEN 0 128 0.0.0.0:8080 0.0.0.0:* users:(("webapp",pid=4821,fd=12))'
       '   # a stale webapp instance from a prior unclean restart still holds :8080')

def _triage_shell(cmd, state):
    low = cmd.strip().lower()
    w = _wandered(low, state)
    if w: return w
    if "journalctl" in low or ("systemctl" in low and "status" in low):
        state["saw_log"] = True
        return _STATUS + "\n" + _LOG if "journalctl" in low else _STATUS
    if re.search(r"\b(ss|lsof|netstat|fuser)\b", low) or "8080" in low:
        return _SS
    if re.search(r"\b(ps|pgrep)\b", low) or "4821" in low:
        return "4821 /usr/bin/webapp   # stale process from a prior restart"
    if re.match(r"(ls|cat|find|grep|tail|head)\b", low):
        return "webapp.service  config.yaml  logs/"
    return "(no output)"

def a_crash_loop(client):
    state = {"wandered": False, "saw_log": False}
    final, calls, txt = _agentic_loop(client,
        "You are an SRE on a Linux server. Use run_shell (one command per call) to find "
        "the ROOT CAUSE. As soon as you can explain it, STOP calling tools and reply in "
        "plain text with the cause.",
        "The webapp.service keeps crash-looping. Why? Find the root cause.",
        lambda c: _triage_shell(c, state), max_turns=16)
    low = (final + "\n" + txt).lower()
    root = ("already in use" in low) or ("8080" in low and ("bind" in low or "port" in low or "stale" in low))
    ok = root and state["saw_log"] and not state["wandered"]
    return (1.0 if ok else 0.0,
            f"calls={calls} sawlog={state['saw_log']} root={root} wandered={state['wandered']}")


SUITE = register(Suite(
    name="agentic", version="1", needs="text",
    blurb="Tool-calling, doc-following, and two mocked-shell incident-response loops.",
    tasks=[
        Task("tool_call", "core", t_toolcall),
        Task("doc_follow", "core", a_doc_follow),
        Task("disk_full", "agentic", a_disk_full),
        Task("crash_loop", "agentic", a_crash_loop),
    ],
))
