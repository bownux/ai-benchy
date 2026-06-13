"""OpenAI-compatible client — the ONLY thing that talks to a model server.

Works against anything that speaks /v1/chat/completions: llama.cpp (llama-server),
vLLM, ollama (/v1), LM Studio, text-generation-webui, or a hosted API. Tasks never
hardcode a URL or a port; they receive a Client and call .chat().

Throughput: we prefer the server's own `timings` block (llama.cpp reports
prompt/predicted tok/s exactly). If a server doesn't return timings (vLLM, ollama),
we fall back to wall-clock: completion_tokens / elapsed. Either way it's labeled.
"""
from __future__ import annotations
import json, time, urllib.request, urllib.error


class Response:
    __slots__ = ("content", "tool_calls", "timings", "usage", "latency_s", "raw", "finish_reason")

    def __init__(self, content, tool_calls, timings, usage, latency_s, raw, finish_reason=None):
        self.content = content or ""
        self.tool_calls = tool_calls or []
        self.timings = timings or {}
        self.usage = usage or {}
        self.latency_s = latency_s
        self.raw = raw
        self.finish_reason = finish_reason

    def gen_tps(self):
        """Generation tok/s: server timings if present, else wall-clock."""
        if self.timings.get("predicted_per_second"):
            return round(float(self.timings["predicted_per_second"]), 2)
        ct = self.usage.get("completion_tokens")
        if ct and self.latency_s > 0:
            return round(ct / self.latency_s, 2)
        return None


class Client:
    def __init__(self, base, timeout=240, api_key=None, model="benchy", no_think=False):
        self.base = base.rstrip("/")
        self.timeout = timeout
        self.model = model
        self.no_think = no_think
        self.last_finish_reason = None  # set by chat(); the runner reads it to flag truncations
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    def _post(self, path, body):
        req = urllib.request.Request(self.base + path, data=json.dumps(body).encode(),
                                     headers=self.headers, method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.load(r)

    def _get(self, path):
        req = urllib.request.Request(self.base + path, headers=self.headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.load(r)

    def chat(self, messages, max_tokens=2048, temperature=0.0, tools=None) -> Response:
        """One chat turn. `messages` may contain multimodal content parts (text +
        image_url) for vision models — they're passed through verbatim."""
        body = {"model": self.model, "messages": messages,
                "max_tokens": max_tokens, "temperature": temperature, "stream": False}
        if tools:
            body["tools"] = tools
        if self.no_think:
            # Disable a reasoning model's chain-of-thought so the token budget is spent
            # on the answer, not the `reasoning_content` channel (e.g. Qwen3 thinking).
            body["chat_template_kwargs"] = {"enable_thinking": False}
        t0 = time.time()
        j = self._post("/v1/chat/completions", body)
        dt = time.time() - t0
        choice = (j.get("choices") or [{}])[0]
        msg = choice.get("message", {}) or {}
        self.last_finish_reason = choice.get("finish_reason")
        return Response(msg.get("content"), msg.get("tool_calls"),
                        j.get("timings"), j.get("usage"), dt, j, self.last_finish_reason)

    def served_model_id(self):
        """Whatever the server says it's serving (best-effort)."""
        try:
            data = self._get("/v1/models").get("data") or []
            return data[0].get("id") if data else None
        except Exception:
            return None

    def measure_throughput(self, prompt=None, max_tokens=256):
        """A sustained generation to record prefill + gen tok/s for the result file.

        The probe must decode ENOUGH tokens that steady-state speed dominates the
        fixed per-request overhead (sampler init, the first eval after prefill).
        The old probe — a haiku capped at 64 tokens — self-terminates after ~15
        tokens, so ``predicted_per_second`` came out badly low on anything but the
        fastest servers: a VL-8B that truly sustains ~120 tok/s measured ~10. We
        now use a prompt that won't stop early and decode a few hundred tokens,
        and record ``gen_n`` (the token count the rate was measured over) so a
        reader can sanity-check it was a real generation, not a 15-token blip.
        """
        if prompt is None:
            prompt = ("Write a thorough, multi-paragraph technical explanation "
                      "(about 300 words) of how virtual memory paging works in a "
                      "modern operating system: cover page tables, the TLB, page "
                      "faults, and swapping to disk.")
        try:
            r = self.chat([{"role": "user", "content": prompt}], max_tokens=max_tokens)
            out = {"gen_tps": r.gen_tps()}
            gen_n = r.timings.get("predicted_n") or r.usage.get("completion_tokens")
            if gen_n:
                out["gen_n"] = int(gen_n)   # tokens the rate was measured over (self-audit)
            if r.timings.get("prompt_per_second"):
                out["prefill_tps"] = round(float(r.timings["prompt_per_second"]), 2)
            return out
        except Exception as e:
            return {"error": str(e)[:120]}

    def health(self):
        for path in ("/health", "/v1/models"):
            try:
                self._get(path); return True
            except Exception:
                continue
        return False
