# Reuse assessment

> **Status: not yet manually reviewed.** Written by an agent; awaiting human review.

This is a newly created, standalone hotel project, built autonomously during
the submission period. No source code, datasets, or prose have been copied
from any other repository.

Working principles applied throughout:
- Explicit evidence provenance and incomplete-result reporting.
- Separation of generated output from independent validation.
- Observable acceptance criteria and small regression checks.

Further implementation reuse remains subject to file-level ownership and license
review. On 2026-09-14 the user explicitly authorized MIT licensing for original project
code and public repository release. The root LICENSE applies to original code only.

Competition rules checked 2026-09-13:
https://agentsforhumans.devpost.com/rules
The project must be newly built during the submission period; incorporated
pre-existing work must be disclosed. Submission requires a public repository
with MIT or Apache licensing. Public release and working judge access are being prepared.

## i18next

i18next 26.4.2 is vendored from the official npm tarball, verified against its SHA-512 integrity metadata. The unmodified MIT license is retained at web/vendor/i18next.LICENSE. Source: https://www.i18next.com/ and https://registry.npmjs.org/i18next/-/i18next-26.4.2.tgz. Translation catalogs are authored for this application.

## Current implementation and judge package

Authentication dependency: Werkzeug, BSD-3-Clause,
official source https://github.com/pallets/werkzeug and license
https://github.com/pallets/werkzeug/blob/main/LICENSE.txt. Use the packaged
generate_password_hash/check_password_hash APIs; no library source copying.
Original distribution notices remain under their own license.

Agent-authored changes use installed SDK interfaces; no SDK source was copied.
The locked Python dependency distributions are inventoried in
[dependency-licenses.md](dependency-licenses.md). Their original notices remain
inside the prepared ZIP; they are not covered by the project MIT license.
The source diagram, Lambda adapter, tests and packaging script were authored for
this project, autonomously and from scratch.

Installed authentication dependencies: Werkzeug 3.1.8 (BSD-3-Clause) and
MarkupSafe 3.0.3 (BSD-3-Clause), unmodified package distributions. No source
copying or relicensing; the local judge package preserves distribution notices.
