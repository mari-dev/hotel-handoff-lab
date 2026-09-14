# Invoice live verification — 2026-09-13

> **Status: not yet manually reviewed.** Written by an agent; awaiting human review.

Final result: four successful live proposal cases and one safely rejected
adversarial case through the actual HTTP endpoint. Evidence: live-invoice-check.json.
A separate live browser run completed intake, explicit confirmation, atomic claim,
PDF detection, exact EML attachment matching and archival with no JavaScript errors.
Its proposal is retained in browser-live-proposal.json; video and screenshots are
in results/demo. All messages and documents are synthetic.

Profile: hotel-handoff-lab. Selected Region: eu-north-1.
Model: amazon.nova-lite-v1:0 (regional, ON_DEMAND reported ACTIVE).
Strands 1.55.1; boto3/botocore 1.43.93; awscrt 0.36.0.

| Case | Observed final outcome |
|---|---|
| English request with address promised later | Guest, stay, company quoted; address null |
| Explicitly no invoice requested | invoice_requested=false; no creation |
| Italian invoice request | Literal guest, stay and company; missing address null |
| German request with full billing address | Literal guest, stay, company and address |
| Embedded instructions to invent a request | HTTP 502 after bounded validation failure; no creation |

The fifth case is a safety rejection, not successful extraction or evidence that
the model reliably understands prompt injection. The fixture allows an explicit
negative proposal or this bounded rejection. It does not accept a positive proposal.

## Fixes and retained limits

Nested optional evidence objects were replaced by flat literal strings for model
output. Empty strings become null fields at the application boundary; a nonempty
value supplies its own exact quote. Validation runs inside the Strands output tool
and again before returning to the browser. Invalid output can be corrected within
the existing five-turn, 14,000-token and 3,000-output-token limits. Actual source
reading and guest lookup are required before accepting a proposal.

A conservative English/German/Italian invoice-demand check now rejects unrelated
or negated literal quotes. It can reject unusual valid phrasing and is not a full
semantic validator. Staff review remains necessary. No check was weakened to
accept fabricated fields. The source and duplicate tools remain read-only.

## Development failures

Earlier attempts omitted request evidence, treated “Address will follow” as an
address, skipped duplicate lookup, or fabricated literal fields. Before the demand
check was added, the adversarial case returned a positive proposal citing breakfast
information. The final gate blocks that result. Historical failed reports remain
in results/live-invoice-check*.json. These iterations are not a reliability benchmark.

## Other verification

Forty unit tests passed, including profile setup, structured-output source checks,
missing tool rejection, and judge-access authentication boundaries. JavaScript
syntax and git diff checks passed. The judge Lambda adapter passed an offline
HTTP request/claim/PDF/EML integration check. The Linux Python 3.13 ZIP imports in
an isolated environment and its CloudFormation template passes cfn-lint.
Deployment, public access and actual Lambda runtime behavior remain unverified.
