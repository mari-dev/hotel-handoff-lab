"""Pre-synthesize narration once, with the real audio durations, so the
recordings can wait exactly as long as each line takes to speak (no overlaps).
"""
import asyncio, json, subprocess, sys
from pathlib import Path
import edge_tts
sys.path.insert(0, str(Path(__file__).parent))
from narration import INTRO_LINES, DEMO_LINES

VID = Path(__file__).parent
AUDIO = VID / "out" / "audio"
AUDIO.mkdir(parents=True, exist_ok=True)
FFPROBE = "/home/mari/miniconda3/bin/ffprobe"
VOICE = "en-US-JennyNeural"


def duration_ms(path):
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                           "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                          capture_output=True, text=True, check=True).stdout.strip()
    return float(out) * 1000


async def synth_set(lines, prefix, registry):
    for i, text in enumerate(lines):
        path = AUDIO / f"{prefix}-{i:02d}.mp3"
        await edge_tts.Communicate(text, VOICE).save(str(path))
        registry[text] = {"file": str(path), "duration_ms": duration_ms(path)}


async def main():
    registry = {}
    await synth_set(INTRO_LINES, "intro", registry)
    await synth_set(DEMO_LINES, "demo", registry)
    (AUDIO / "durations.json").write_text(json.dumps(registry, indent=2))
    for text, info in registry.items():
        print(f"{info['duration_ms']:6.0f} ms  {text}")


asyncio.run(main())
