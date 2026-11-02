import torch

LOW_VRAM_THRESHOLD_GB = 2.0
DEFAULT_TRACKER = "botsort.yaml"
FALLBACK_TRACKER = "bytetrack.yaml"

def get_tracker() -> str:
    """Select tracker algorithm based on available VRAM."""
    if not torch.cuda.is_available():
        return DEFAULT_TRACKER

    free_vram, _ = torch.cuda.mem_get_info()
    free_vram_gb = free_vram / (1024 ** 3)

    if free_vram_gb < LOW_VRAM_THRESHOLD_GB:
        print(f"Low VRAM ({free_vram_gb:.1f}GB free). Switching to ByteTrack.")
        return FALLBACK_TRACKER

    print(f"VRAM OK ({free_vram_gb:.1f}GB free). Using BoT-SORT.")
    return DEFAULT_TRACKER
