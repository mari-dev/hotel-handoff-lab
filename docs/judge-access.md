# Judge access — deployed 2026-09-14

Implementation: `judge_lambda.py`, `infra/judge-demo.yaml`.
Deployed in eu-north-1. Demo: https://whaottbycymae2xz24quiol5l40rogle.lambda-url.eu-north-1.on.aws

The deployed stack contains a Lambda function and HTTPS Function URL, a narrowly
scoped execution role, a generated Secrets Manager password, and a log group with
seven-day retention. An encrypted private S3 bucket stores the ZIP artifact.
No always-on compute, NAT gateway, AgentCore runtime or cross-region inference.

The URL is publicly reachable at the infrastructure layer; invoice data routes require an authenticated session. The public login page
accepts the generated password and username `judge`. Provide the password
only through Devpost's private testing instructions, never in a public repository
or video. AWS credentials stay in the Lambda execution role. Browser sessions use Secure,
HttpOnly, SameSite=Strict cookies; no HTTP Basic popup remains.

The sandbox uses synthetic, temporary SQLite/file data. State can reset when
Lambda replaces its environment; it is not durable production storage. One
reserved concurrent invocation serializes access. Model usage remains bounded
per analysis; the twenty-attempt local daily limit can reset with the environment
and is not a financial cap. AWS charges remain the entrant's responsibility.

Remote checks passed anonymous API rejection, Secure/HttpOnly session login,
actual Strands intake without automatic creation, human creation and ownership,
synthetic PDF detection, exact EML attachment matching and logout revocation.
A deployed Chromium check also passed page loading, login, verified operator
identity and polling without JS errors or failed requests. Static assets are
included in HTML and browser API calls are serialized for this single-instance demo.
Private login instructions are held outside the repository.
Keep it available through October 9, 2026 at 02:00 CEST. Clean up after judging
with the user's approval; do not shut it down before then.

The user's USD 20 monthly project spend limit remains in force. This package
does not claim an exact cost estimate or guarantee availability if that limit
pauses the project. These checks demonstrate the synthetic smoke workflow, not production reliability.

The Dictate (speech-to-text) button shown in the demo video is also live here:
the deployed package was rebuilt and redeployed on 2026-09-14 (`aws lambda
update-function-code`) after the feature was added, and a remote Chromium
check confirmed the button renders and toggles with no JavaScript errors.
