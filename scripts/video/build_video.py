"""Mux the pre-synthesized narration (scripts/video/synth_narration.py) onto
the intro + demo recordings, using each clip's real measured duration so nothing overlaps.
"""
import glob, json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from narration import INTRO_LINES as INTRO_TEXT, OUTRO_LINES as OUTRO_TEXT

ROOT = Path(__file__).resolve().parents[2]
VID = ROOT / "scripts/video"
OUT = VID / "out"
AUDIO = OUT / "audio"
DURATIONS = json.loads((AUDIO / "durations.json").read_text())

INTRO_VIDEO = sorted(glob.glob(str(OUT / "intro" / "*.webm")))[0]
DEMO_VIDEO = OUT / "demo" / "hotel-handoff-demo.webm"
DEMO_TIMELINE = json.loads((OUT / "demo/timeline.json").read_text())
OUTRO_VIDEO = sorted(glob.glob(str(OUT / "outro" / "*.webm")))[0]
OUTRO_LINES = [{"text": text, "offset_ms": 300} for text in OUTRO_TEXT]

# Fixed offsets matching the CSS scene timings in intro-animation.html:
# scene-t 0.0-2.5 (product name, silent), scene0 2.5-9.5 (narrator problem),
# scene1 9.5-15.1 (guest call), scene1b 15.1-22.8 (the confusion, 4 lines),
# scene2 22.8-38.9 (pitch/skeptic/reassure x2), scene3 38.9-41.7 (dictation),
# scene4 41.7-46.8 (narrator resolution).
INTRO_OFFSETS = [2800, 9800, 15400, 17350, 18890, 20700, 23100, 27620, 32470, 36420, 39650, 42450, 49450]
INTRO_LINES = [
    {"text": line["text"], "offset_ms": offset}
    for line, offset in zip(INTRO_TEXT, INTRO_OFFSETS)
]

FFMPEG = "/home/mari/miniconda3/bin/ffmpeg"
FFPROBE = "/home/mari/miniconda3/bin/ffprobe"


def synth_all(lines, prefix):
    for i, line in enumerate(lines):
        info = DURATIONS[line["text"]]
        line["file"] = info["file"]


def probe_duration_ms(path):
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                           "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                          capture_output=True, text=True, check=True).stdout.strip()
    return float(out) * 1000


def build_mix(lines, total_ms, out_wav):
    inputs, filters, labels = [], [], []
    for i, line in enumerate(lines):
        inputs += ["-i", line["file"]]
        delay = max(0, int(line["offset_ms"]))
        filters.append(f"[{i}:a]adelay={delay}|{delay}[a{i}]")
        labels.append(f"[a{i}]")
    filters.append(f"{''.join(labels)}amix=inputs={len(lines)}:normalize=0,apad=whole_dur={total_ms/1000}[out]")
    cmd = [FFMPEG, "-y", *inputs, "-filter_complex", ";".join(filters),
           "-map", "[out]", str(out_wav)]
    subprocess.run(cmd, check=True, capture_output=True)


def mux(video_path, audio_path, out_path):
    subprocess.run([FFMPEG, "-y", "-i", str(video_path), "-i", str(audio_path),
                     "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                     "-shortest", str(out_path)], check=True, capture_output=True)


def concat(videos, out_path):
    listfile = OUT / "concat.txt"
    listfile.write_text("".join(f"file '{v}'\n" for v in videos))
    subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
                     "-c", "copy", str(out_path)], check=True, capture_output=True)


def main():
    synth_all(INTRO_LINES, "intro")
    synth_all(DEMO_TIMELINE, "demo")
    synth_all(OUTRO_LINES, "outro")

    intro_dur = probe_duration_ms(INTRO_VIDEO)
    demo_dur = probe_duration_ms(DEMO_VIDEO)
    outro_dur = probe_duration_ms(OUTRO_VIDEO)
    print("intro_dur", intro_dur, "demo_dur", demo_dur, "outro_dur", outro_dur)

    build_mix(INTRO_LINES, intro_dur, AUDIO / "intro-mix.wav")
    build_mix(DEMO_TIMELINE, demo_dur, AUDIO / "demo-mix.wav")
    build_mix(OUTRO_LINES, outro_dur, AUDIO / "outro-mix.wav")

    mux(INTRO_VIDEO, AUDIO / "intro-mix.wav", OUT / "intro-narrated.mp4")
    mux(DEMO_VIDEO, AUDIO / "demo-mix.wav", OUT / "demo-narrated.mp4")
    mux(OUTRO_VIDEO, AUDIO / "outro-mix.wav", OUT / "outro-narrated.mp4")

    concat([OUT / "intro-narrated.mp4", OUT / "demo-narrated.mp4", OUT / "outro-narrated.mp4"],
           OUT / "hotel-handoff-lab-submission.mp4")
    print("FINAL:", OUT / "hotel-handoff-lab-submission.mp4")


main()
