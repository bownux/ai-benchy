"""Run model-generated Python to score coding tasks — in a separate process with a
timeout and tight resource limits.

Coding tasks ask the model for a function, then EXECUTE it against known inputs and
check the output. That means running untrusted text. We mitigate: fresh subprocess,
CPU+memory+output rlimits, short timeout, and an opt-out (`--no-exec` skips all
code-execution tasks). For maximum paranoia, run the whole benchmark in a container.
"""
from __future__ import annotations
import re, subprocess, sys, textwrap

_GUARD = textwrap.dedent("""
    try:
        import resource  # Unix-only; absent on Windows, where limits are simply skipped
        resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
        resource.setrlimit(resource.RLIMIT_AS, (1024*1024*1024, 1024*1024*1024))
        resource.setrlimit(resource.RLIMIT_FSIZE, (4*1024*1024, 4*1024*1024))
    except Exception:
        pass
""")


def extract_code(text: str) -> str:
    """Pull a python code block out of a model reply (```python … ``` or bare ```)."""
    m = re.search(r"```(?:python)?\s*\n(.*?)```", text or "", re.S)
    return (m.group(1) if m else (text or "")).strip()


def run_py(code: str, timeout: int = 8) -> str:
    """Execute `code` and return combined stdout (stderr appended on failure)."""
    try:
        p = subprocess.run([sys.executable, "-I", "-c", _GUARD + code],
                           capture_output=True, text=True, timeout=timeout)
        return (p.stdout or "") + (("" if p.returncode == 0 else "\n[stderr] " + (p.stderr or "")))
    except subprocess.TimeoutExpired:
        return "[timeout]"
    except Exception as e:
        return f"[error] {e}"
