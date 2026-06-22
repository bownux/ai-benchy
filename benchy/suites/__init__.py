"""Suite/Task framework + registry.

A Task scores ONE capability and returns (score 0..1, detail). A Suite groups tasks,
declares whether it needs a `text` or `vision` model, and is versioned so results
stay comparable (bump the version when you change scoring, and old results keep their
old version label). To add a task: write `def my_task(client) -> (float, str)` and
append `Task("my_task", "tier", my_task)`. To add a suite: new module + register().

See CONTRIBUTING.md for the full how-to.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable


@dataclass
class Task:
    id: str
    tier: str                       # grouping label, e.g. core/hard or code/reasoning/agentic
    run: Callable                   # run(client) -> (score: float in [0,1], detail: str)


@dataclass
class Suite:
    name: str
    version: str
    needs: str                      # "text" or "vision"
    tasks: list
    blurb: str = ""


_REGISTRY: dict = {}


def register(suite: Suite):
    _REGISTRY[suite.name] = suite
    return suite


def get(name: str) -> Suite:
    _load_all()
    if name not in _REGISTRY:
        raise KeyError(f"unknown suite {name!r}; have: {', '.join(sorted(_REGISTRY))}")
    return _REGISTRY[name]


def names():
    _load_all()
    return sorted(_REGISTRY)


def all_suites():
    _load_all()
    return [_REGISTRY[n] for n in names()]


_loaded = False
def _load_all():
    global _loaded
    if _loaded:
        return
    from . import coding, reasoning, agentic, vision, frontier  # noqa: F401  (each calls register())
    _loaded = True
