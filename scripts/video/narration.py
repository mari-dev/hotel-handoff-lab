"""Single source of truth for narration text + voice, shared by synth + record scripts."""

VOICES = {
    "guest": "en-US-ChristopherNeural",
    "receptionist": "en-GB-SoniaNeural",
    "colleague": "en-US-EmmaNeural",
    "narrator": "en-US-JennyNeural",
}

# Each intro line is spoken in-character (diegetic dialogue), except the last,
# which is narrator commentary. offset_ms is filled in after measuring real
# durations (see scripts/video/plan_intro_timing.py) and used by build_video.py.
INTRO_LINES = [
    {"text": "Small hotel teams struggle to coordinate. And even a simple fix meets resistance.", "voice": VOICES["narrator"]},
    {"text": "When are you sending my invoice? I've asked three times!", "voice": VOICES["guest"]},
    {"text": "Did you take care of that?", "voice": VOICES["receptionist"], "rate": "+12%"},
    {"text": "Wait, I thought you did.", "voice": VOICES["colleague"], "rate": "+12%"},
    {"text": "Didn't you write it down?", "voice": VOICES["receptionist"], "rate": "+12%"},
    {"text": "Where would I even write it?", "voice": VOICES["colleague"], "rate": "+12%"},
    {"text": "I found an app for this. We log every request right here now.", "voice": VOICES["colleague"]},
    {"text": "Ugh, what a hassle. I don't want to enter data by hand.", "voice": VOICES["receptionist"]},
    {"text": "No, it's easy. You just say it, and the app sorts it out.", "voice": VOICES["colleague"]},
    {"text": "Trust me. It takes a second.", "voice": VOICES["colleague"]},
    {"text": "Keller, invoice.", "voice": VOICES["receptionist"]},
    {"text": "Speak it, type it, or paste it from an email you already have — on your phone or your computer.", "voice": VOICES["narrator"]},
    {"text": "Whoever is free picks it up, and knows exactly who it's for.", "voice": VOICES["narrator"]},
]

OUTRO_LINES = [
    "Thank you for watching.",
]

DEMO_LINES = [
    "Hotel Handoff Lab. Invoice requests arrive across messages and staff shifts.",
    "This message can be dictated too, with the browser's own speech recognition.",
    "Synthetic guest message. Strands extracts literal details; staff review before saving.",
    "Every field is shown with its source text. Missing details stay empty, not guessed.",
    "Only explicit confirmation creates the request. Preparing it assigns one operator atomically.",
    "Lexware opens as a browser link. This prototype does not create accounting invoices.",
    "A real synthetic PDF is matched by an independent guest and stay monitor.",
    "The exported sent email contains the identical PDF attachment. No email is sent by this app.",
    "A local synthetic prototype. Human review stays required at every step.",
]
