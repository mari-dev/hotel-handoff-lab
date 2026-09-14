# Devpost entry — Hotel Handoff Lab

> Ready-to-paste draft. Public video URL and final Devpost review remain outstanding.

## Project name
Hotel Handoff Lab

## Elevator pitch
Turn scattered hotel invoice requests into source-backed proposals, staff-owned work, and document-verified progress across shifts.

## Track
Professional Agents

## Inspiration
This comes from lived experience, not a hypothetical: having worked in a front-of-house, guest-facing role at a small, independently-run hospitality business, where staff turnover is high and formal onboarding is minimal, so coordination between shifts is inconsistent by default, not by anyone's fault. Unlike larger hotels, there is no dedicated general-manager role to catch what falls through the cracks between shifts: ownership handles the business side personally, on top of everything else running the property, so coordination has to work through the team itself. Ownership there also has very limited comfort with software.

Hotel invoice requests arrive through guest conversations, paper notes, calls and messages. Several people may prepare invoices, but the next shift needs to know who asked, which stay the request concerns, who is handling it, and whether the document was actually prepared or sent. We built a small coordination tool around those questions.

## Persona and real-world use cases
**Persona:** front-of-house staff at a small, independently-run hospitality business, working alongside colleagues who rotate frequently; ownership oversees invoicing personally but has very limited comfort with software.

- **The request arrives sideways.** A guest asks in person, at breakfast or at the desk, or calls on the phone, never through a formal channel. Each staff member jots it on whatever scrap of paper is at hand, in their own words, with no shared place to look; the note can end up in a pocket, a drawer or the bin. The staff member who hears it may be off shift by the time it can be acted on, and with onboarding this thin, the next person on duty often has no way of knowing the request was ever made.
- **Coordination has to fit in two taps on a phone.** Nobody on a shift like this has time, or patience, for a system that needs training. Logging a request, or claiming one and opening it in Lexware, is a single tap from a phone; seeing what is outstanding is a glance at a shared list, not a report to run. If it takes more than that, staff will go back to paper.
- **Duplicate or dropped work.** With high turnover and minimal handover process, two different staff members can each start preparing the same guest's invoice without knowing about the other, or a request can quietly fall through because no one is clearly its owner. Checking existing requests by guest name before creating a new one directly targets this.
- **"Done" needs proof, not a verbal claim.** The owner-manager wants a yes/no glance, not a dashboard to learn. Distinguishing "prepared" from "sent" only when a matching PDF and an exported Sent-folder EML actually exist replaces "I think I sent it" with something checkable, without asking a non-technical owner to verify anything themselves.
- **The accounting tool is not a reminder system.** Guests ask for invoices ("Rechnungen") in German, English or Italian, but the request itself lives nowhere: Lexware is where an invoice gets produced once someone remembers to open it, not a place that tracks who still needs one. Requests get lost between the moment a guest asks and the moment someone happens to check. That gap, not Lexware's invoicing itself, is what the shared queue and per-request ownership are built to close.

The consequence lands on the guest: invoices that never arrive, arrive late, or arrive with the wrong stay or billing details, followed by a guest having to ask again or complain. We are not claiming a measured reduction in complaints; the point is that today's failure mode is a lost paper note, and a shared, source-backed queue removes that specific failure mode without asking already-stretched staff to change how they work.

## What it does
A Strands agent reads a synthetic guest message, extracts an explicit invoice request and its literal details, and checks existing requests by guest name. Every extracted field is shown with source text. Missing details stay empty. Staff review the proposal and explicitly confirm creation. The message can be typed, pasted, or dictated: an optional Dictate button uses the browser's own speech recognition to transcribe speech directly into the message field, live, with no server call and no extra cost.

The request enters a shared local queue. Preparing it atomically assigns an operator and opens Lexware through a browser link. A separate monitor reads text PDFs from a local folder and links a document only when the guest and stay match uniquely. It marks the request prepared. An exported Sent EML containing the identical PDF attachment supplies the evidence for the sent state. Ambiguous matches remain unresolved.

The interface supports English, German and Italian with local translation catalogs. Guest messages and source evidence are never translated automatically.

## How we built it
Python, Strands Agents SDK, regional Amazon Bedrock Nova Lite, Pydantic, SQLite, pypdf, and a browser interface with locally bundled i18next. The agent has two read-only tools: read_request_message and find_existing_requests. Structured-output validation runs inside the agent loop, so errors can be corrected within bounded model turns. The same evidence checks run again before returning a proposal. Model extraction, deterministic document checks and staff actions remain separate.

## Challenges
Nova Lite did not consistently handle nested optional evidence objects. We simplified its output to literal strings and represent absent fields as empty strings, then convert them to nullable source-backed fields for the interface. We also require actual tool execution and reject invoice-demand quotes that fail a conservative English/German/Italian request check. This deliberately narrow gate can reject valid unusual phrasing; it is not a general semantic proof.

## What we verified
Live HTTP checks covered missing billing details, an explicit absence of an invoice request, Italian intake and a full German billing address. A separate adversarial check evaluates rejection of embedded model instructions; a rejected analysis is not counted as a successful extraction. A real browser run completed live intake, human confirmation, ownership, PDF detection, exact EML attachment matching and archival, with no JavaScript errors. All inputs and files were synthetic. These are small development checks, not a reliability benchmark or production validation.

## Limitations and next steps
The local app now uses password-protected accounts, expiring server-side sessions and verified operator identities. It has no direct Lexware, Thunderbird or booking-system API integration. The PDF matcher supports a narrow text layout; exported Sent folders are a trusted convention, not proof of email delivery. The application does not send email or create legal accounting invoices. Next steps are user-reviewed workflow evaluation, durable shared storage and managed account recovery and broader extraction testing.

## Built with
Python; Strands Agents SDK; Amazon Bedrock; Amazon Nova Lite; Pydantic; SQLite; pypdf; JavaScript; i18next.

More about me: [mari-dev.github.io](https://mari-dev.github.io/)

## Development and reuse disclosure
AI coding assistance was used, directed throughout by the entrant's own prompts and decisions: the problem framing, the persona, the use cases and every acceptance criterion came from the entrant's lived front-of-house/reception experience, not from the model. The AI wrote code under that direction and did not originate the problem being solved. This is a standalone, autonomous project, built entirely during the submission period; no external source code or datasets were copied. Third-party packages and vendored i18next retain their own licenses; see docs/reuse.md and docs/dependency-licenses.md. No unsupported time-saving or originality claims are made.

## Attachments to complete before submitting
- Public MIT repository: https://github.com/mari-dev/hotel-handoff-lab
- Portfolio: https://mari-dev.github.io/
- Public YouTube/Vimeo video URL, no more than five minutes.
- Architecture diagram: docs/architecture.svg.
- Working judge demo: https://whaottbycymae2xz24quiol5l40rogle.lambda-url.eu-north-1.on.aws
- AWS Builder ID: enter your ID in the Devpost field.
- Private judge testing instructions: copy results/judge-login.txt only into the private testing field.
