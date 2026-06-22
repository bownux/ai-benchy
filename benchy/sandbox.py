"""Run model-generated Python to score coding tasks — in a separate process with a
timeout and tight resource limits.

Coding tasks ask the model for a function, then EXECUTE it against known inputs and
check the output. That means running untrusted text. We mitigate: fresh subprocess,
CPU+memory+output rlimits, short timeout, and an opt-out (`--no-exec` skips all
code-execution tasks). For maximum paranoia, run the whole benchmark in a container.
"""
from __future__ import annotations
import os, re, subprocess, sys


def _apply_limits():
    """Set CPU/memory/file-size rlimits in the child before exec (POSIX only).

    Done via preexec_fn rather than prepended source so that model programs which
    begin with `from __future__ import ...` still parse — a __future__ import must be
    the first statement, and injecting guard code ahead of it is a SyntaxError.
    On Windows rlimits don't exist and this never runs, so isolation is weaker there.
    """
    try:
        import resource  # Unix-only
        resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
        resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_FSIZE, (4 * 1024 * 1024, 4 * 1024 * 1024))
    except Exception:
        pass


def extract_code(text: str) -> str:
    """Pull the python program out of a model reply.

    Models often emit more than one fenced block (a grammar/BNF or sample output
    before the actual ```python). Naively taking the first fence then runs the wrong
    thing, so prefer a python-tagged block, then any block that looks like Python, and
    among those the longest (the real program rather than a snippet).
    """
    text = text or ""
    blocks = re.findall(r"```([\w+.-]*)[^\n]*\n(.*?)```", text, re.S)
    if not blocks:
        return text.strip()

    def looks_py(b):
        return ("def " in b) or ("print(" in b) or ("import " in b) or ("class " in b)

    tagged = [b for tag, b in blocks if tag.lower() in ("python", "py")]
    pool = tagged or [b for _, b in blocks]
    real = [b for b in pool if looks_py(b)] or pool
    return max(real, key=len).strip()


def run_py(code: str, timeout: int = 8) -> str:
    """Execute `code` and return combined stdout (stderr appended on failure)."""
    preexec = _apply_limits if os.name == "posix" else None
    try:
        p = subprocess.run([sys.executable, "-I", "-c", code],
                           capture_output=True, text=True, timeout=timeout,
                           preexec_fn=preexec)
        return (p.stdout or "") + (("" if p.returncode == 0 else "\n[stderr] " + (p.stderr or "")))
    except subprocess.TimeoutExpired:
        return "[timeout]"
    except Exception as e:
        return f"[error] {e}"
