"""CODING suite — ask for a function, then EXECUTE it and check the output.

Judge-free: the model's code is run against known inputs; pass = correct stdout.
Tiers: `code` (warm-up) and `hard` (the ones that actually separate models).
"""
from __future__ import annotations
from . import Suite, Task, register
from ..sandbox import extract_code, run_py


def _solve(client, prompt, checker, max_tokens=4000):
    r = client.chat([{"role": "user", "content": prompt}], max_tokens=max_tokens)
    out = run_py(extract_code(r.content))
    ok = checker(out)
    return (1.0 if ok else 0.0, f"out={out.strip()[:60]!r}")


def t_fib(client):
    return _solve(client,
        "Write a complete Python program that prints the 10th Fibonacci number "
        "(1,1,2,3,5,... so the 10th is 55). Print only the number.",
        lambda o: o.strip().splitlines()[-1].strip() == "55" if o.strip() else False)


def t_bugfix(client):
    buggy = "def avg(xs):\n    return sum(xs) / len(xs) - 1  # off-by-one bug\nprint(avg([2,4,6]))"
    return _solve(client,
        "This program has a bug; the average of [2,4,6] should be 4.0. Fix it and "
        f"give the full corrected program:\n\n```python\n{buggy}\n```",
        lambda o: o.strip().splitlines()[-1].strip() in ("4.0", "4") if o.strip() else False)


def h_palindrome(client):
    return _solve(client,
        "Write Python: def longest_palindrome(s) returning the longest palindromic "
        "substring of s. Then print longest_palindrome('babad') and "
        "longest_palindrome('cbbd') and longest_palindrome('a') and "
        "longest_palindrome('geeksskeeg'), one per line.",
        lambda o: [x.strip() for x in o.strip().splitlines()[-4:]] in
                  (['bab', 'bb', 'a', 'geeksskeeg'], ['aba', 'bb', 'a', 'geeksskeeg']))


def h_parens(client):
    return _solve(client,
        "Write Python: def valid(s) returns True iff brackets ()[]{} are correctly "
        "matched and nested. Then print valid('([]{})'), valid('(]'), valid('([)]'), "
        "valid('{[]}'), one per line.",
        lambda o: [x.strip() for x in o.strip().splitlines()[-4:]] == ['True','False','False','True'])


def h_dedup_order(client):
    return _solve(client,
        "Write Python: def dedup(xs) returns a list with duplicates removed but "
        "FIRST-seen order preserved, and it must work when elements are unhashable "
        "(e.g. lists). Then print dedup([3,1,2,1,3]) and dedup([[1],[2],[1],[1,2]]), "
        "one per line.",
        lambda o: [x.strip() for x in o.strip().splitlines()[-2:]] == ['[3, 1, 2]', '[[1], [2], [1, 2]]'])


def h_rate_limiter(client):
    return _solve(client,
        "Write Python: a class TokenBucket(capacity, refill_per_sec) with method "
        "allow(now) -> bool that implements a token-bucket rate limiter (starts full, "
        "refills continuously, capped at capacity). Then simulate: bucket = "
        "TokenBucket(2, 1); print([bucket.allow(t) for t in [0,0,0,1,1]]) — expected "
        "[True, True, False, True, False].",
        lambda o: "[True, True, False, True, False]" in o)


SUITE = register(Suite(
    name="coding", version="1", needs="text",
    blurb="Write-and-run Python: warm-up + 4 hard algorithmic tasks.",
    tasks=[
        Task("fib", "code", t_fib),
        Task("bugfix", "code", t_bugfix),
        Task("palindrome", "hard", h_palindrome),
        Task("parens", "hard", h_parens),
        Task("dedup_order", "hard", h_dedup_order),
        Task("rate_limiter", "hard", h_rate_limiter),
    ],
))
