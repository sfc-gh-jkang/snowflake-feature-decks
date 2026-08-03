# Security Policy

## Scope

This repository contains **documentation only** — self-contained HTML decks,
speaker notes, and the small Python tooling that generates them. It ships no
runtime service, no deployed application, and no credentials.

## Reporting a vulnerability

For anything security-relevant in this repo — a leaked credential, an internal
identifier that should not be public, or a supply-chain concern in the tooling —
email **john.kang@snowflake.com** directly rather than opening a public issue.

Snowflake product vulnerabilities are out of scope here. Report those through
Snowflake's official channel: https://www.snowflake.com/en/trust-center/

## Reporting a factual inaccuracy

Decks in this repo make technical claims about Snowflake features. If a claim is
wrong, outdated, or has since been documented differently, please open an issue.

Every deck labels its claims:

- **Documented** claims cite a `docs.snowflake.com` URL.
- **Field-observed** claims are labeled as such and carry an evidence matrix
  showing what was verified and what could not be.

A field-observed claim is not a statement of Snowflake support. Do not treat one
as a supported configuration without confirming with the relevant product team.

## No secrets

`.gitignore` excludes `.env`, `*.pem`, `*.key`, `*.p8`, `credentials.json`,
`connections.toml`, and Terraform state/tfvars. Decks use generic placeholder
object names (for example `analytics.live`) rather than real account, database,
or warehouse identifiers.
