# Hotel Handoff Lab — Story

## Inspiration

This comes from lived experience, not a hypothetical. I worked front-of-house at a small, independently-run hospitality business with high staff turnover and no dedicated manager to catch what falls between shifts. Guests ask for invoices in person, by phone, or in passing — whoever hears it scribbles a note, and the next shift often has no idea it happened. The demo video's opening exchange ("Did you take care of that?" / "Wait, I thought you did.") is a composite of that exact situation. The accounting software doesn't help either: it produces invoices, it doesn't track who still needs one. That gap is where requests get lost, and the guest is the one who pays for it.

## What it does

A Strands agent reads a guest message — typed, dictated, or pasted from an email — and extracts the invoice request with literal, source-quoted details. It checks for existing requests first, so nobody duplicates work. Nothing is created without explicit staff confirmation. Once confirmed, preparing a request atomically assigns one owner and opens Lexware. A separate, deterministic file monitor (not AI) verifies a matching PDF and, later, a sent-email with the same attachment, before marking anything as sent — so "done" is checkable, not just claimed. Works in English, German and Italian, on phone or computer.

## How I built it

Python, Strands Agents SDK, Amazon Bedrock (Nova Lite), Pydantic, SQLite, pypdf, Werkzeug for auth, i18next for translations. The agent has two read-only tools and can't write anything itself — only a person confirms creation. Structured-output validation runs in the agent loop, and the same checks run again server-side before anything reaches the UI. The submission video is a real screen recording of the live app (genuine Bedrock calls), narrated with free neural TTS voices, timed against each clip's measured audio duration so nothing overlaps.

## Challenges

Nova Lite struggled with nested optional fields, so I flattened its output to literal strings and validated afterward. The agent must prove it actually read the message and checked for duplicates — no tool call, no result. A conservative request-detection gate can reject unusual phrasing; I chose that trade-off deliberately, since a false rejection is safer than fabricating a request nobody made. The bigger challenge was restraint: no Lexware/Thunderbird/booking-system integration, no email sending, no claim beyond what's actually verified.

## What I learned

The small, literal constraints — exact source quotes, forced tool use, evidence checks kept separate from the model — are the actual product design, not limitations bolted on after. For a low-trust, high-turnover team, the real design problem is the two-tap, no-training constraint; what the agent is allowed to touch comes second.

## What's next

Durable shared storage, managed account recovery, broader extraction testing — and eventually a direct integration with Thunderbird and Booking.com guest messages, so a "Rechnung" request creates itself automatically, with the same source citation and human confirmation step already in place.
