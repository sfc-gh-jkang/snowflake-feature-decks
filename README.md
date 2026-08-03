# Snowflake Feature Decks

Self-contained HTML decks explaining Snowflake features and patterns. Each deck is
a single file with inline CSS and JS — no build step, no dependencies — served
directly from GitHub Pages.

Format and styling follow
[`sfc-gh-perickson/demos-enablement`](https://github.com/sfc-gh-perickson/demos-enablement)
so these sit alongside that library.

## Decks

| Topic | Audience | Format | Support status | Link |
|-------|----------|--------|----------------|------|
| Interactive Tables, Fed Directly by Snowpipe Streaming | SEs, Solution Architects | Presentation + speaker notes | GA; quickstart-documented | [View](interactive-tables-streaming/presentations/interactive-tables-streaming.html) |
| Dynamic Tables: Why Your Refresh Went Full | SEs, Analytics Engineers | Presentation + speaker notes | GA (ADAPTIVE GA 2026-07-30) | [View](dynamic-tables-refresh-modes/presentations/dynamic-tables-refresh-modes.html) |
| Storage Lifecycle Policies: Archive Before You Pay | SEs, Data Engineers, Compliance | Presentation + speaker notes | GA 2025-11-07 (COLD: AWS + GCP only) | [View](storage-lifecycle-policies/presentations/storage-lifecycle-policies.html) |
| Secretless CI/CD: Deploying to Snowflake from GitHub Actions | SEs, Platform Engineers | Presentation + speaker notes | GA (OIDC needs CLI 3.11+) | [View](github-actions-oidc-cicd/presentations/github-actions-oidc-cicd.html) |
| Preventing Data Download to Unmanaged Devices | SEs, Security Teams, IAM Owners | Presentation + speaker notes | GA (AGGREGATE_ACCESS_HISTORY preview; 1 claim KB-sourced) | [View](preventing-data-egress-unmanaged-devices/presentations/preventing-data-egress-unmanaged-devices.html) |

## Claim accuracy

Every factual claim carries a `docs.snowflake.com` citation. Where a pattern is
documented somewhere other than the product guide — or observed working but not
written down anywhere — the deck says so explicitly and shows the evidence
gathered: object type, code path, and live query telemetry, along with whatever
could not be verified.

This matters because a deck is a claim surface. The **Interactive Tables** deck
covers two GA features whose combination is documented in a first-party
[Snowflake quickstart](https://www.snowflake.com/en/developers/guides/interactive-tables-snowpipe-streaming-arcade-lab/)
but is absent from the interactive-tables product guide. It carries an evidence
matrix distinguishing the two rather than flattening them. Read the "Support
Status" section before presenting it.

## Reading a deck

These are scroll pages, not slide decks — there is no keyboard navigation. A fixed
sidebar tracks position; the progress bar at the top reflects scroll depth. They
print to PDF cleanly (the sidebar is dropped and fade-in blocks are forced
visible).

Each deck ships with `*-speaker-notes.md` alongside it: talking points, key
insight, anticipated questions, and doc references per section.

## Building a deck

Decks are authored with the `enablement-html-deck` Cortex Code skill, which owns
the HTML template, the component reference, and the publishing checklist. That
skill is the single source of truth — this repo deliberately does not duplicate it.

`scripts/` here is the **CI guard**, not the authoring toolchain. It runs on every
push to validate what review misses:

```bash
# structure, dangling anchors, unfilled placeholders, leaked tokens — exits 1 on failure
python3 scripts/new_deck.py --check <slug>/presentations/<slug>.html
```

Scaffolding a new deck requires the skill's templates; running `new_deck.py`
without them exits 2 with a pointer rather than a traceback.

## Owner

| | |
|---|---|
| Owner | John Kang |
| Email | john.kang@snowflake.com |
| GitHub | [@sfc-gh-jkang](https://github.com/sfc-gh-jkang) |
| Access requests | Email the owner, or open an issue |
| License | Apache-2.0 |

Corrections to factual claims are especially welcome — if something here is wrong,
or has since been documented, open an issue or email the owner directly.

## License

[Apache-2.0](LICENSE)
