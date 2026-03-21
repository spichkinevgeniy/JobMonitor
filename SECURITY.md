# Security Policy

## Supported Versions

Security fixes are currently applied to the `main` branch and the latest tagged release.

## Reporting a Vulnerability

Please do not report security issues in public GitHub issues.

Instead, contact the maintainer privately and include:

- a short description of the issue;
- steps to reproduce;
- impact assessment;
- affected configuration or version;
- any suggested mitigation if available.

Security contact: `evgeniyspichkin.work@gmail.com`

## What to avoid publishing publicly

- `.env` contents
- Telegram session files
- bot tokens
- Telegram API credentials
- production database credentials
- private infrastructure endpoints

## Response expectations

- initial acknowledgment target: within 7 days;
- status update target: within 14 days;
- remediation timeline depends on severity and reproducibility.

## Hardening recommendations for contributors

- use `.env.sample` as the starting point for local setup;
- rotate secrets immediately if they were exposed;
- avoid sharing logs with tokens or personal data;
- review dependency updates and deployment changes carefully.
