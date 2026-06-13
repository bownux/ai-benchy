"""ai-benchy CLI.

    python -m benchy run <suite> --endpoint URL --label NAME [model metadata]
    python -m benchy run text   --endpoint URL --label NAME      # coding+reasoning+agentic
    python -m benchy compare [results/ or files...]              # markdown leaderboard
    python -m benchy list                                        # suites + tasks
    python -m benchy selftest                                    # render vision images, no model

`text` is an alias that runs every text suite; `all` runs text + vision.
"""
from __future__ import annotations
import argparse, sys
from . import __version__
from .suites import names, get, all_suites

TEXT_SUITES = ["coding", "reasoning", "agentic"]


def _model_meta(a):
    m = {k: v for k, v in (("name", a.model_name_meta), ("backend", a.backend),
                            ("quant", a.quant), ("ctx", a.ctx), ("params_b", a.params_b),
                            ("notes", a.notes)) if v is not None}
    return m


def cmd_run(a):
    from .runner import run_suite
    if a.suite in ("text", "all"):
        suites = TEXT_SUITES + (["vision"] if a.suite == "all" else [])
    else:
        suites = [a.suite]
    for s in suites:
        try:
            run_suite(s, a.endpoint, a.label, model_meta=_model_meta(a), out_dir=a.out,
                      skip_exec=a.no_exec, api_key=a.api_key, model_name=a.model,
                      no_think=a.no_think)
        except SystemExit as e:
            print(f"!! {s}: {e}", file=sys.stderr)


def cmd_compare(a):
    from .compare import leaderboard
    print(leaderboard(a.paths or ["results"]))


def cmd_list(a):
    for s in all_suites():
        print(f"\n{s.name}  (v{s.version}, needs {s.needs}) — {s.blurb}")
        for t in s.tasks:
            print(f"    [{t.tier:<7}] {t.id}")


def cmd_selftest(a):
    import os
    os.environ.setdefault("VL_SAVE_IMAGES", a.dir)
    # re-import vision so it picks up VL_SAVE_IMAGES, then render every image
    from .suites import vision
    if not vision._HAVE_PIL:
        sys.exit("Pillow not installed — `pip install pillow` to render vision images.")
    vision.SAVE = a.dir
    for tid, tier, b, p, s in vision._SPEC:
        import base64
        os.makedirs(a.dir, exist_ok=True)
        open(os.path.join(a.dir, f"{tid}.png"), "wb").write(base64.b64decode(b()))
    print(f"rendered {len(vision._SPEC)} vision images to {a.dir} — open them to verify ground truth.")


def main():
    ap = argparse.ArgumentParser(prog="benchy", description=f"ai-benchy {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="run a suite against an endpoint")
    r.add_argument("suite", help="one of: " + ", ".join(names()) + ", text, all")
    r.add_argument("--endpoint", required=True, help="OpenAI-compatible base URL, e.g. http://127.0.0.1:8080")
    r.add_argument("--label", required=True, help="short name for this model, e.g. qwen3-vl-8b")
    r.add_argument("--out", default="results", help="output dir for the result JSON")
    r.add_argument("--model", default="benchy", help="model id to send in the request (most servers ignore it)")
    r.add_argument("--api-key", default=None, help="bearer token if your endpoint needs one")
    r.add_argument("--no-exec", action="store_true", help="skip code-execution tasks (don't run model output)")
    r.add_argument("--no-think", action="store_true",
                   help="disable a reasoning model's chain-of-thought (sends chat_template_kwargs "
                        "enable_thinking=false) so the token budget goes to the answer")
    # optional metadata stamped into the result for fair comparison
    r.add_argument("--backend", default=None, help="llama.cpp | vllm | ollama | lmstudio | ...")
    r.add_argument("--quant", default=None, help="e.g. Q4_K_M, MXFP4, fp16")
    r.add_argument("--ctx", type=int, default=None, help="context length the server is running")
    r.add_argument("--params-b", type=float, default=None, help="param count in billions, e.g. 8")
    r.add_argument("--model-name-meta", default=None, help="full model name, e.g. Qwen3-VL-8B-Instruct")
    r.add_argument("--notes", default=None, help="freeform notes")
    r.set_defaults(fn=cmd_run)

    c = sub.add_parser("compare", help="merge result files into a leaderboard")
    c.add_argument("paths", nargs="*", help="result files or dirs (default: results/)")
    c.set_defaults(fn=cmd_compare)

    l = sub.add_parser("list", help="list suites and tasks")
    l.set_defaults(fn=cmd_list)

    st = sub.add_parser("selftest", help="render the vision images locally (no model needed)")
    st.add_argument("--dir", default="/tmp/benchy-images")
    st.set_defaults(fn=cmd_selftest)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
