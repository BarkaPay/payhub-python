# Security Policy

## Reporting a vulnerability

Please **do not** open a public issue for security vulnerabilities.

- Preferred: use GitHub's [private vulnerability reporting](https://github.com/BarkaPay/payhub-python/security/advisories/new).
- Or email **security@payhub.africa** with details and reproduction steps.

We aim to acknowledge reports within 72 hours.

## Handling secrets

- Never commit your `sk_live_…` API keys or `whsec_…` webhook secrets.
- The SDK never logs credentials.
- Always verify webhook signatures against the **raw** request body
  (`payhub.webhook.verify` / `parse`) before trusting the payload.

## Supported versions

The latest released minor version receives security fixes.
