"""Auto-detect the machine a run happened on, so every result is self-describing.

This is what makes cross-person comparison meaningful: a friend with 2× Blackwell
5000s, another with 1× RTX 6000, and you on 3× R9700 each get their hardware
stamped into the result file automatically — nobody has to remember to write it down.

Pure stdlib + a couple of optional CLIs (nvidia-smi / rocm-smi). Degrades to "unknown"
fields rather than failing; vendor GPUs are also read from Linux /sys as a fallback.
"""
from __future__ import annotations
import json, os, platform, re, socket, subprocess


def _run(cmd, timeout=6):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.stdout if p.returncode == 0 else ""
    except Exception:
        return ""


def _nvidia_gpus():
    out = _run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"])
    gpus = []
    for line in out.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2 and parts[0]:
            try: vram = int(float(parts[1]))
            except Exception: vram = None
            gpus.append({"name": parts[0], "vram_mb": vram, "vendor": "nvidia"})
    return gpus


def _amd_gpus():
    # Prefer rocm-smi; fall back to /sys/class/drm for amdgpu cards.
    out = _run(["rocm-smi", "--showproductname", "--showmeminfo", "vram", "--json"])
    gpus = []
    try:
        j = json.loads(out) if out.strip().startswith("{") else {}
        for k, v in j.items():
            if not k.lower().startswith("card"):
                continue
            name = v.get("Card Series") or v.get("Card model") or v.get("GPU ID") or "AMD GPU"
            vram = v.get("VRAM Total Memory (B)")
            mb = int(int(vram) / 1024 / 1024) if vram else None
            gpus.append({"name": str(name).strip(), "vram_mb": mb, "vendor": "amd"})
    except Exception:
        pass
    if gpus:
        return gpus
    # /sys fallback (Linux): amdgpu vendor id 0x1002
    try:
        import glob
        for dev in sorted(glob.glob("/sys/class/drm/card[0-9]/device")):
            try:
                if open(os.path.join(dev, "vendor")).read().strip() != "0x1002":
                    continue
                vt = os.path.join(dev, "mem_info_vram_total")
                mb = int(int(open(vt).read().strip()) / 1024 / 1024) if os.path.exists(vt) else None
                gpus.append({"name": "AMD GPU (amdgpu)", "vram_mb": mb, "vendor": "amd"})
            except Exception:
                continue
    except Exception:
        pass
    return gpus


def _cpu_name():
    try:
        for line in open("/proc/cpuinfo"):
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or platform.machine() or "unknown"


def _ram_gb():
    try:
        for line in open("/proc/meminfo"):
            if line.startswith("MemTotal"):
                return round(int(re.search(r"\d+", line).group()) / 1024 / 1024, 1)
    except Exception:
        pass
    try:
        return round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024**3, 1)
    except Exception:
        return None


def detect():
    gpus = _nvidia_gpus() + _amd_gpus()
    return {
        "host": socket.gethostname(),
        "os": platform.platform(),
        "cpu": _cpu_name(),
        "cores": os.cpu_count(),
        "ram_gb": _ram_gb(),
        "gpus": gpus,
        "gpu_summary": ", ".join(
            f"{g.get('name')}" + (f" {g['vram_mb']//1024}GB" if g.get("vram_mb") else "")
            for g in gpus) or "no GPU detected",
    }


if __name__ == "__main__":
    print(json.dumps(detect(), indent=2))
