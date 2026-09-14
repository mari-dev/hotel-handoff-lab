# Hotel Handoff Lab

> **Status: not yet manually reviewed.** Written by an agent; awaiting human review.

A local prototype for invoice requests that get lost between hotel shifts.

## Run

```sh
uv sync
.venv/bin/python run_local.py
```

Open http://localhost:8765/login and sign in. To enable Strands with the configured AWS login:

```sh
AWS_PROFILE=hotel-handoff-lab AWS_REGION=eu-north-1 HANDOFF_MODEL_ID=amazon.nova-lite-v1:0 .venv/bin/python run_local.py --require-ai
```

If the login has expired, run `aws login --profile hotel-handoff-lab` first.
An exported `AWS_BEARER_TOKEN_BEDROCK` is also supported. Never share credentials.
The regional model avoids cross-region inference. Configuration availability
does not prove model access; the live check below does.
Startup makes no model call. AI analysis uses paid Bedrock inference; the local
20-attempt daily limit is not a monetary spending guarantee.

## Workflow

Enter a guest name or ask Strands to extract an invoice request from a message.
Every extracted field must quote the input; a person confirms creation.
Prepare claims the request atomically and opens Lexware in a browser tab.
The monitor reads actual PDFs from results/inbox/pdfs and exported sent EML
files from results/inbox/sent. Exact guest and stay matches mark a PDF prepared;
the identical attachment in a sent-folder EML marks it sent. Uncertain matches
remain visible for review. Lab buttons create synthetic files, never send email.

Matching is deliberately narrow: supported text PDFs must contain full guest
and stay fields on separate lines. This is not arbitrary invoice recognition.
The sent folder is a trusted import convention, not proof of delivery.
There is no direct Thunderbird, Booking, or Lexware API integration.
Operator identity comes from the signed-in local account, never client-supplied labels. Synthetic data only.

## Validation

```sh
.venv/bin/python -m unittest discover -s tests -v
node --check web/app.js
```

The separate paid live check exercises the actual HTTP intake endpoint against
five synthetic messages in a disposable database:

```sh
AWS_PROFILE=hotel-handoff-lab AWS_REGION=eu-north-1 HANDOFF_MODEL_ID=amazon.nova-lite-v1:0 .venv/bin/python live_invoice_check.py
```

Results, tool execution names, and token usage are written to
`results/live-invoice-check.json`. The check stops at the first failure and verifies
that extraction never modifies requests before human confirmation.

The final invoice intake check covers four successful live cases and one safely
rejected adversarial message. A separate browser run completed live intake,
confirmation, ownership, PDF detection, EML matching and archival. These are
synthetic smoke checks, not a reliability evaluation. See
[verification evidence](docs/live-invoice-status.md),
[architecture](docs/architecture.svg), and
[Devpost draft](docs/submission-draft.md).

The model emits literal strings; missing fields become null. An independent,
conservative English/German/Italian demand check can reject unusual valid wording.
Literal quotes do not establish semantic correctness; staff review is required.

A password-protected [judge demo](https://whaottbycymae2xz24quiol5l40rogle.lambda-url.eu-north-1.on.aws) is deployed in eu-north-1.
Judge credentials are provided privately in the submission testing instructions.
Remote HTTPS checks passed login, live Strands extraction, human confirmation,
ownership and synthetic PDF/EML matching on 2026-09-14. Its synthetic data is
temporary; see [judge access](docs/judge-access.md).

Original application code is licensed under MIT; third-party components retain
their own licenses. See LICENSE and docs/dependency-licenses.md.
This prototype is not a completed contest entry.

## Interface languages

Choose English, Deutsch, or Italiano from the Language selector, also available inside the request dialog. English is the default; the browser remembers your choice. i18next and all translation catalogs are bundled locally. Switching languages makes no model or remote translation calls. Guest names, notes, stay text, and source quotations keep their original content.

The focused browser check is `python tests/browser_languages.py` in an environment with Playwright and Chromium installed.


## Sign-in and accounts

The local interface and data APIs require authentication. For the first account:

```sh
.venv/bin/python manage_users.py reception --name Reception --bootstrap
```

This works only when no accounts exist. It writes a generated password to
`results/local-login.txt` with owner-only permissions; never commit or share it.
To add an account or change a password from a trusted terminal:

```sh
.venv/bin/python manage_users.py reception --name Reception
```

The command prompts privately; changing a password revokes existing sessions.
Werkzeug stores scrypt password hashes. Opaque session cookies are HttpOnly,
SameSite=Strict and expire after eight hours; logout revokes the session.
HTTPS judge hosting also marks cookies Secure. Local HTTP is loopback-only.
Five failed sign-ins per username in ten minutes trigger a temporary limit.
Public endpoints are limited to the login assets, login/logout and minimal health;
invoice data, evidence and AI calls require a session. Account management is
terminal-only: no self-registration, password-recovery email or MFA is implemented.

The sign-in page is available in English, German and Italian. The current
demo recording includes login followed by the live invoice workflow.
