# Security Policy

Afterword is an experiment maintained by one person. It handles a DEV API key and, on your own machine, other people's comments, so security and privacy problems are taken seriously, even though the project is small.

## Reporting a problem

**Please do not open a public issue for a security or privacy problem.**

Report it privately through GitHub's private vulnerability reporting: on the repository page, open the **Security** tab and choose **Report a vulnerability**. Only the maintainer can see the report.

Please include:

- what you found, and why it is a problem
- the steps to reproduce it, or a minimal example
- the version or commit you tested
- whether real data (an API key, comment text, a commenter's identity) could be exposed, and how

Please do not include real API keys, real comment text, or anyone's personal data in the report. A description or a synthetic example is enough.

## What to expect

- An acknowledgment within about a week. This is a solo, best-effort project with no service-level commitment.
- Fixes are made on `main`. There are no maintained release branches; the latest commit is the supported version.
- Once a fix is available, the problem may be described publicly, with credit to the reporter if they want it.
- There is no bug bounty.

## In scope

Problems in this repository, including:

- **Credential handling:** the DEV API key being printed, logged, saved, committed, or sent anywhere other than DEV.
- **Data leaving the machine:** comment text or commenter identities being sent somewhere without the user's knowledge, including to a model provider whose path is not signed off.
- **Committed real data:** real comment text, names, or handles reaching a committed file, or a way to get past the identity scan.
- **Deletion and retention:** deleted comments or reduced runs keeping text that the documented purge and retention rules say should be gone.
- **The local labeling server:** anything that lets another site, process, or user on the network reach the label UI, which should listen on 127.0.0.1 only and require its per-launch token.
- **Priority manipulation:** comment text that causes the system to place a comment in a *lower* tier than its policy allows. Injection attempts that end up surfaced are the designed behavior; injections that get a comment collapsed are in scope.

## Out of scope

- Problems in DEV or Forem themselves. Please report those to DEV.
- Problems in Ollama, uv, Python, or other dependencies. Please report those upstream; a note here is still welcome if Afterword's use of them makes things worse.
- Misclassification in general. Model mistakes are an expected part of the experiment and are measured, not hidden. Report them as ordinary issues, unless they fall under priority manipulation above.

## Design references

How the project handles credentials, data, and privacy is described in:

- `docs/USING-AFTERWORD-ON-YOUR-ACCOUNT.md`: what is collected, stored, and sent, and how to delete it
- `docs/PRIVACY-AND-BOUNDARIES.md`: the project's privacy rules
- `docs/adr/`: the decisions behind them, including credentials (ADR-006), untrusted comment content (ADR-008), and deletion (ADR-009)