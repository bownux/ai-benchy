"""ai-benchy — a small, hardware-agnostic LLM/VLM benchmark you can repeat and compare.

Every task is scored PROGRAMMATICALLY (run-the-code / exact-match / valid-JSON /
tool-call-made) against fixed or synthetic inputs — no second model grades the
output, so a run on your box and a run on someone else's are directly comparable.
Point it at any OpenAI-compatible endpoint (llama.cpp, vLLM, ollama, LM Studio, …).
"""
__version__ = "0.1.0"
RESULT_SCHEMA = "ai-benchy/result/1"
