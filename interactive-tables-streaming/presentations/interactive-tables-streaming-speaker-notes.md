# Speaker Notes: Interactive Tables, Fed Directly by Snowpipe Streaming

## Presentation Context

For SEs and solution architects evaluating sub-second serving on streaming data.
After this session someone should be able to decide whether interactive tables
fit a workload, stand up the pattern, and — critically — describe its support
status accurately to a customer.

Eleven sections in four arcs. Concepts (1–4) covers why hops hurt and what the
evidence for this pattern actually is. Implementation (5–7) is the mechanics.
Operations (8–9) is cost and limits. Production (10–11) is claim verification and
the wrap.

**Support status, state this up front every time:** interactive tables are GA
(Dec 2025) and Snowpipe Streaming HPA is GA (Sep 2025). The combination —
streaming directly into an interactive table — **is documented**, in a first-party
Snowflake quickstart with runnable code: https://www.snowflake.com/en/developers/guides/interactive-tables-snowpipe-streaming-arcade-lab/ (updated 2026-07-14, lab repo
https://github.com/Snowflake-Labs/Summit26-InteractiveLab).

What it is *not* is covered in the interactive-tables product guide, which never
mentions streaming, channels, or pipes and presents `TARGET_LAG` auto-refresh as
the population path. So the honest framing is "documented in a quickstart, not in
the product guide" — **not** "undocumented." Point people at the quickstart.

Two caveats to carry: the quickstart is explicitly marked "provided as is, and is
not maintained on an ongoing basis," and HPA ingest still cannot be confirmed from
`ACCOUNT_USAGE` because the streaming channel views are empty — an observability
gap, not a support gap.

---

## Slide 1: Hero / Overview

**Talking Points:**
- Frame it: "one table is both the streaming target and the serving layer."
- The four stat cards each map to something proven later. 196 ms (p50) and 12.3 M
  queries are live-measured from `QUERY_HISTORY` over the 30 days to 2026-07-31 on
  one X-Small interactive warehouse — not modelled, and not a published benchmark.
  If asked for the longer view: 24.6 M queries at p50 212 ms since 2026-05-13.
- Read the warning box out loud. Naming the docs split early prevents the "is this
  even supported?" question from hanging over the rest of the session.

**Key Insight:**
Freshness normally degrades at every hop between ingest and serve. Collapsing the
hops means serving freshness equals ingest latency. The price is a table that
rejects nearly all DML, which changes how you design writes.

**Common Questions:**
- *Q: Is this GA?*
  A: Both halves are GA, and the combination ships as a first-party quickstart with
  working code. It's just missing from the product guide.
- *Q: Can I arrow-key through this deck?*
  A: No — it's a scroll page. That's the format, not an oversight.

**References:**
- https://docs.snowflake.com/en/release-notes/2025/other/2025-12-11-interactive-tables-ga
- https://docs.snowflake.com/en/release-notes/2025/other/2025-09-23-snowpipe-streaming-high-performance-architecture

---

## Slide 2: The Problem

**Talking Points:**
- Walk the four cards as compounding constraints, not a list.
- The `TARGET_LAG` floor of 60 seconds is the sharpest point: for a live ops or
  trading dashboard, a one-minute floor *is* the problem.
- The interactive-warehouse wall is the one people miss — it cannot query
  standard tables at all, which forces a design decision early.

**Key Insight:**
The documented population path for interactive tables is auto-refresh from a
source table. That is correct and cheaper for most workloads. It is only wrong
when your freshness requirement is below the refresh floor.

**Common Questions:**
- *Q: Why not a dynamic table?*
  A: Same refresh-lag issue, plus an interactive table can't be a dynamic table's
  base table.

**References:**
- https://docs.snowflake.com/en/user-guide/interactive

---

## Slide 3: Architecture

**Talking Points:**
- Walk the six-stage strip once, then explain *why* it's legal: HPA routes all
  ingestion through a `PIPE`, and a pipe targets "a table." Nothing in that
  contract requires a standard table.
- Opening a channel is what causes Snowflake to auto-create the default pipe.
- The denormalization point in the highlight box is a design consequence, not a
  preference — the join restriction forces it.

**Key Insight:**
This isn't a special integration. It's the ordinary HPA path pointed at a table
that happens to be interactive, which is exactly why it works and exactly why
it's not written down anywhere.

**Common Questions:**
- *Q: Do I need a custom pipe?*
  A: No. The default `<TABLE>-STREAMING` pipe is created for you.
- *Q: How do I correct bad rows?*
  A: You don't update — you re-stream a snapshot and take latest-per-key at query
  time.

**References:**
- https://docs.snowflake.com/en/user-guide/snowpipe-streaming/data-load-snowpipe-streaming-overview

---

## Slide 4: Support Status

**Talking Points:**
- This is the integrity slide. Do not skip it.
- Walk the matrix row by row: five verified gates, one red (ingest telemetry), then
  the two documentation rows — quickstart yes, product guide no.
- The point is *where* it's written down, not *whether*. The quickstart is
  first-party and ships runnable code; the product guide simply doesn't cover
  streaming ingestion yet.
- The closing anecdote is why the matrix exists — a demo claimed an interactive
  serving layer while every query read a view over a standard table.

**Key Insight:**
"Documented in a quickstart, not in the product guide" is precise and useful.
"Undocumented" would be wrong, and "Snowflake fully documents this" would be
overclaiming. The precision is what makes the slide worth showing.

**Common Questions:**
- *Q: So can I recommend this?*
  A: Yes — it's a first-party quickstart with working code. Flag that the quickstart
  is marked "provided as is" and not actively maintained.
- *Q: Why couldn't you find it in the docs?*
  A: It lives under snowflake.com developer guides, not docs.snowflake.com. Searching
  the product docs for "interactive table streaming" returns nothing.
- *Q: Why are the channel views empty?*
  A: Only classic-era streaming views exist and they aren't populated for HPA here.
  Treat HPA ingest observability as a current gap.

**References:**
- https://www.snowflake.com/en/developers/guides/interactive-tables-snowpipe-streaming-arcade-lab/
- https://github.com/Snowflake-Labs/Summit26-InteractiveLab

**References:**
- https://docs.snowflake.com/en/user-guide/interactive

---

## Slide 5: Creating the Table

**Talking Points:**
- `CLUSTER BY` is required — the statement won't compile without it. Match it to
  the hottest `WHERE` clause.
- The `DROP` first is not defensive coding. You cannot `CREATE OR REPLACE` across
  table types; converting standard → interactive fails with "Object already
  exists as TABLE."
- Explicit column lists work even though the docs describe CTAS. That matters
  here because there is no source table to select from.
- Run the DDL on a standard warehouse.

**Key Insight:**
Omitting `TARGET_LAG` is the deliberate choice that makes the streaming channel
the sole writer. Adding it would reintroduce the refresh hop.

**Common Questions:**
- *Q: Can I add a column later?*
  A: No. `ALTER TABLE ADD COLUMN` is unsupported — recreate and re-stream.
- *Q: Does VARIANT work?*
  A: Yes, along with `NOT NULL`, `DEFAULT`, and `BOOLEAN`.

**References:**
- https://docs.snowflake.com/en/sql-reference/sql/create-interactive-table
- https://docs.snowflake.com/en/user-guide/tables-clustering-keys

---

## Slide 6: The Streaming Producer

**Talking Points:**
- Emphasise how unremarkable this code is. That's the point.
- `pipe_name = f"{table}-STREAMING"` is the entire integration surface.
- `wait_for_flush` is what lets you measure genuine end-to-end ingest-to-query
  latency rather than SDK-append time.
- Partition by entity key when ordering matters: order holds within a channel,
  not across channels.

**Key Insight:**
Because DML is rejected, seeding is a streaming concern. The producer emits the
baseline at startup. Anyone expecting to `INSERT` a fixture row will be stuck.

**Common Questions:**
- *Q: Channel limits?*
  A: Soft limits — 2,000 channels per pipe, 12 MBps per channel, 10 GBps per
  table. Support can raise them.
- *Q: Java or REST instead?*
  A: Both fine; same pipe contract.

**References:**
- https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-getting-started
- https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-limitations

---

## Slide 7: Warehouse Pairing

**Talking Points:**
- `ALTER WAREHOUSE ... ADD TABLES` is the step people forget. Symptom is "it
  works but it's slow" — the table never gets warmed.
- The wall is one-way: interactive warehouses read only interactive tables, but a
  standard warehouse *can* read an interactive table. That asymmetry is what
  makes an A/B latency comparison possible on the same object.
- Configure a fallback warehouse. Queries past 5 seconds get re-run there.

**Key Insight:**
The fallback isn't a failure path, it's workload isolation — it keeps one slow
query from occupying the low-latency pool.

**Common Questions:**
- *Q: Smallest size?*
  A: XSMALL. Don't confuse this with Snowpark-optimized, which starts at MEDIUM.
- *Q: How many tables can I warm?*
  A: Ten today. You can query more; only ten are pre-warmed.

**References:**
- https://docs.snowflake.com/en/sql-reference/sql/create-interactive-warehouse

---

## Slide 8: Cost Traps

**Talking Points:**
- Lead with the 24-hour minimum auto-suspend. It is the most surprising fact in
  the feature and the one that turns into an unexpected bill.
- Contrast directly with a standard warehouse idling down in 60 seconds.
- Manual suspend/resume still bills a 1-hour minimum, and resuming gives your
  first users the day's worst latency while the cache re-warms.

**Key Insight:**
This is an always-on serving tier with a daily cost floor. If the workload isn't
continuous, recommend something else — that's a feature-fit judgement, not a
tuning problem.

**Common Questions:**
- *Q: Can I suspend overnight to save money?*
  A: You'll pay an hour minimum and hand your morning users cold-cache latency.
  Usually a false economy.

**References:**
- https://docs.snowflake.com/en/user-guide/interactive

---

## Slide 9: Limits

**Talking Points:**
- Everything on this slide is documented — say so, it contrasts deliberately with
  slide 4.
- The load-bearing three: `INSERT OVERWRITE` is the only DML, no streams, and no
  dynamic table can use an interactive table as a base.
- No fail-safe, but Time Travel works and inherits retention from the schema.

**Key Insight:**
Most of these are consequences of one design fact: the table is optimised for
being read, not changed. Reason from that and the list becomes predictable.

**Common Questions:**
- *Q: CDC downstream?*
  A: Not via streams on this table. Source it elsewhere in the pipeline.
- *Q: Materialized views?*
  A: Only with the `INTERACTIVE` keyword.

**References:**
- https://docs.snowflake.com/en/user-guide/interactive

---

## Slide 10: Verifying Your Own Claims

**Talking Points:**
- Provisioning an object proves nothing about whether anything reads it.
- Three gates: right type, real code path, live reads on the claimed warehouse.
- The negative control is the clever bit — proving no `INSERT`/`COPY INTO` exists
  is what establishes rows arrived by streaming.
- The CI guard stops regression. Naming an object after a feature is not using it.

**Key Insight:**
The claim lives in Markdown; reality lives in code. Without something diffing
them, they drift silently and a reviewer finds it before you do.

**Common Questions:**
- *Q: Isn't a test for a README excessive?*
  A: It caught a real shipped defect. One test is cheaper than the credibility hit.

**References:**
- https://docs.snowflake.com/en/user-guide/interactive

---

## Slide 11: Takeaways

**Talking Points:**
- Four-step strip is the implementation checklist: cluster, stream to the
  auto-pipe, pair the warehouse, budget for 24 hours.
- Close on fit: continuous high-concurrency serving, append-only thinking,
  denormalized model.
- Repeat the support framing. Last thing they hear should be accurate: GA, quickstart
  documented, product guide silent.

**Key Insight:**
One object, one truth — and you pay for it with append-only design and always-on
economics. Both are acceptable for a live serving tier and disqualifying for
anything bursty.

**Common Questions:**
- *Q: Where do I start?*
  A: Run the quickstart — it provisions everything in a GitHub Codespace and streams
  synthetic data end to end: https://www.snowflake.com/en/developers/guides/interactive-tables-snowpipe-streaming-arcade-lab/. If your freshness requirement is above the
  60-second `TARGET_LAG` floor, the simpler auto-refresh path may be enough.

**References:**
- https://docs.snowflake.com/en/user-guide/interactive
- https://docs.snowflake.com/en/sql-reference/sql/create-interactive-table
- https://docs.snowflake.com/en/sql-reference/sql/create-interactive-warehouse
