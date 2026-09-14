# Demo script — under five minutes

> **Status: not yet manually reviewed.** Written by an agent; awaiting human review.

1. Explain the real problem: several people prepare invoices, but requests arrive
   on paper, by voice, and through messages. Forgotten requests cost staff time.
2. Show a synthetic message: “Anna Keller requests an invoice for 12–14 September.
   Company: Example GmbH. Address will follow.” The live check has passed for this case. Run actual Strands intake. Show quotes and missing address; confirm the request.
3. Click Prepare. Show ownership in another tab and Lexware opening. Explain
   that this is a browser link, not automatic invoice creation.
4. Create a synthetic PDF in the lab. Wait for the independent monitor to mark
   it prepared. Create the synthetic sent EML; show automatic archival.
5. Show an ambiguous or unmatched document remaining in review. Explain why
   the system avoids guessing when guest names alone are ambiguous.
6. Close with boundaries: local prototype, synthetic files, no real email sent;
   real hotel exports and usability need further testing.

Record in English. Do not show keys, personal data, or claim a simulated AI run
is live. The agent extracts supported fields and checks existing requests;
deterministic evidence matching handles completion.


## Recorded material

A 59.60-second silent screen recording with English captions is available at
`results/demo/hotel-handoff-live-demo.webm`. It contains a real paid Strands run
and actual synthetic PDF/EML file monitoring. Lexware navigation was intercepted
in the browser test and is explicitly described as a link, not accounting work.
The video is a review draft and has not been uploaded or published.

Suggested short voiceover if rerecording: “Hotel staff receive invoice requests
across messages, paper notes and shifts. Hotel Handoff Lab turns a message into a
source-backed proposal. Strands reads the message and checks existing requests.
Staff confirm before anything is saved. Preparing the invoice assigns an owner.
The independent monitor then matches a PDF and the same attachment in an exported
sent email. That keeps progress visible without extra status clicks. This is a
synthetic prototype; it does not send email or integrate directly with accounting.”

The current recording includes the login page and a successful authenticated
live invoice flow, recorded on 2026-09-14. The visible test username is a
disposable synthetic fixture, not the deployed judge credential.
