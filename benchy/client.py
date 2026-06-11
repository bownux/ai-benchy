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
    __slots__ = ("content", "tool_calls", "timings", "usage", "latency_s", "raw")

    def __init__(self, content, tool_calls, timings, usage, latency_s, raw):
        self.content = content or ""
        self.tool_calls = tool_calls or []
        self.timings = timings or {}
        self.usage = usage or {}
        self.latency_s = latency_s
        self.raw = raw

    def gen_tps(self):
        """Generation tok/s: server timings if present, else wall-clock."""
        if self.timings.get("predicted_per_second"):
            return round(float(self.timings["predicted_per_second"]), 2)
        ct = self.usage.get("completion_tokens")
        if ct and self.latency_s > 0:
            return round(ct / self.latency_s, 2)
        return None


class Client:
    def __init__(self, base, timeout=240, api_key=None, model="benchy"):
        self.base = base.rstrip("/")
        self.timeout = timeout
        self.model = model
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
        t0 = time.time()
        j = self._post("/v1/chat/completions", body)
        dt = time.time() - t0
        msg = (j.get("choices") or [{}])[0].get("message", {}) or {}
        return Response(msg.get("content"), msg.get("tool_calls"),
                        j.get("timings"), j.get("usage"), dt, j)

    def served_model_id(self):
        """Whatever the server says it's serving (best-effort)."""
        try:
            data = self._get("/v1/models").get("data") or []
            return data[0].get("id") if data else None
        except Exception:
            return None

    def measure_throughput(self, prompt="Write a haiku about benchmarking.", max_tokens=64):
        """A short generation to record prefill + gen tok/s for the result file."""
        try:
            r = self.chat([{"role": "user", "content": prompt}], max_tokens=max_tokens)
            out = {"gen_tps": r.gen_tps()}
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
