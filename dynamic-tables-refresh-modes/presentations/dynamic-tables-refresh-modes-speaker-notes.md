# Speaker Notes: Dynamic Tables — Why Your Refresh Went Full

## Presentation Context

For SEs and analytics engineers who own dynamic table pipelines, or who get pulled
into "why did this get expensive" conversations. After this session someone should
be able to look at a dynamic table and say what mode it is actually running, why,
and whether that is the right choice.

Eleven slides in four arcs. Concepts (1–3) covers the four modes and ADAPTIVE.
Diagnosis (4–6) is the AUTO trap, what breaks incremental, and how to trace a
regression. Design (7–9) is the five-percent myth, pipeline shape, and cost
levers. Advanced (10–11) is custom incrementalization and the wrap.

**Support status:** everything here is documented. ADAPTIVE went GA 2026-07-30 —
recent enough that most customers have not adopted it and many SEs have not seen
it. `CUSTOM_INCREMENTAL` is Public Preview; confirm current status before
recommending it. Two recommendations come from the Snowflake engineering blog and
developer guide rather than the product docs, and the deck labels those links.

The through-line: incremental refresh is a property of your query, not a switch.
Everything else follows from that.

---

## Slide 1: Hero / Overview

**Talking Points:**
- Open with the framing sentence: incremental is a property your query has or
  loses, not a setting you turn on.
- The four stat cards preview the arc — four modes, ADAPTIVE as the new default,
  eleven documented breakers, and no automatic threshold.
- Flag that ADAPTIVE is days old as GA. If people have prior dynamic tables
  experience, their mental model is already out of date.

**Key Insight:**
Most dynamic table cost surprises trace to one of two things: a table silently
resolved to FULL at creation, or a table still configured INCREMENTAL whose change
rate outgrew the useful range. Both are invisible unless you look.

**Common Questions:**
- *Q: Is ADAPTIVE GA everywhere?*
  A: GA as of 2026-07-30. Verify in the customer's region and account before
  designing around it.

**References:**
- https://docs.snowflake.com/en/release-notes/2026/other/2026-07-30-dynamic-tables-adaptive-refresh-mode-ga
- https://docs.snowflake.com/en/user-guide/dynamic-tables/refresh-modes

---

## Slide 2: Four Modes, One Decision

**Talking Points:**
- Walk the four boxes left to right. The ordering is deliberate: ADAPTIVE first
  because it is the recommended answer, AUTO last because it is the trap.
- Emphasise that the mode is fixed at creation and `ALTER` cannot change it.
- Read both quotes verbatim — the docs saying "use ADAPTIVE as your preferred
  refresh mode for all incremental workloads" and the blog saying "never use
  `REFRESH_MODE = AUTO` in production." Direct guidance like this is rare and
  worth quoting exactly.
- AUTO never resolves to ADAPTIVE. If you want ADAPTIVE you must ask for it.

**Key Insight:**
Four modes look like a menu but there is a default answer for most workloads:
ADAPTIVE if the definition is incrementalizable, FULL if it is not. INCREMENTAL is
for when you want creation to fail loudly rather than adapt.

**Common Questions:**
- *Q: Why would I pick INCREMENTAL over ADAPTIVE?*
  A: When you want to guarantee no surprise reinitializations, or the definition is
  simple enough that ADAPTIVE would never rebuild anyway.
- *Q: Can I change the mode later?*
  A: Not with `ALTER`. `CREATE OR ALTER` or `CREATE OR REPLACE` — and the latter
  reinitializes downstream dependencies too.

**References:**
- https://docs.snowflake.com/en/user-guide/dynamic-tables/refresh-modes
- https://www.snowflake.com/en/blog/whats-new-dynamic-tables-faster-flexible/

---

## Slide 3: ADAPTIVE Refresh

**Talking Points:**
- The problem ADAPTIVE solves: a pipeline that is append-heavy all day but gets
  one nightly `INSERT OVERWRITE`. Before ADAPTIVE you chose between incremental
  (cheap all day, terrible at night) and full (predictable, wasteful all day).
- Walk the trigger table. Note the two "usually not" rows are not arbitrary —
  where the definition calls expensive per-row operators, rebuilding costs more
  than the incremental path, so the heuristic declines.
- The heuristic compares two estimated costs. It is not a row-count rule.
- Reinitializations are observable via `REFRESH_ACTION = 'REINITIALIZE'` and
  `REINIT_REASON`. Show the query — an unexplained cost spike is otherwise very
  hard to attribute.

**Key Insight:**
ADAPTIVE does not remove the need to understand incrementalization. The definition
still has to be incrementalizable or creation fails. It removes the need to
*choose* between two bad modes when change volume is bimodal.

**Common Questions:**
- *Q: How often will it reinitialize?*
  A: Workload-dependent. Measure with `DYNAMIC_TABLE_REFRESH_HISTORY` rather than
  predicting.
- *Q: Can I stop it reinitializing?*
  A: Reduce the blast radius instead — a frozen region, or a larger
  `INITIALIZATION_WAREHOUSE` so the rebuild is fast.

**References:**
- https://docs.snowflake.com/en/user-guide/dynamic-tables/refresh-modes
- https://docs.snowflake.com/en/sql-reference/functions/dynamic_table_refresh_history
- https://docs.snowflake.com/en/user-guide/dynamic-tables/frozen-regions

---

## Slide 4: The AUTO Trap

**Talking Points:**
- Two distinct failure modes, and people usually only know about one.
- Silent resolution: with AUTO an unsupported construct produces no error. You get
  a FULL table and a bill. With INCREMENTAL the same definition fails at create.
- Resolves once: AUTO evaluates at creation and locks in. If an upstream view later
  changes so incremental is impossible, refreshes **fail** — it does not quietly
  fall back.
- Show the error text. Failing at create is the outcome you want in a pipeline.

**Key Insight:**
AUTO optimises for getting a table created. Production wants the opposite — fail
early, make cost explicit in the DDL, and let code review see the trade-off.

**Common Questions:**
- *Q: What if I inherited a codebase full of AUTO?*
  A: Slide 6 has the audit query. Sweep for `refresh_mode <> 'INCREMENTAL'` and
  triage by `refresh_mode_reason`.

**References:**
- https://docs.snowflake.com/en/user-guide/dynamic-tables/refresh-modes
- https://docs.snowflake.com/en/user-guide/dynamic-tables/supported-queries

---

## Slide 5: What Breaks Incremental

**Talking Points:**
- Do not read all eleven rows aloud. Point at the four categories and let people
  scan — definition shape, function type, pipeline shape, configuration.
- The ones that bite most often: `LIMIT`, subqueries outside FROM
  (`WHERE EXISTS`, `WHERE IN (SELECT ...)`), and change tracking not enabled.
- Spend real time on the `CURRENT_TIMESTAMP()` nuance in the info box. The rule is
  positional: timestamp functions are fine in `WHERE`/`HAVING`/`QUALIFY` and break
  incremental only in the `SELECT` list. A rolling filter is fine; stamping a
  processed-at column silently costs you incremental refresh.
- Close on the context box: some computations genuinely cannot be incrementalized.
  An exact median re-sorts everything when one row lands.

**Key Insight:**
This is not a list of implementation gaps. Most entries are cases where computing
the answer requires seeing all rows, so there is no incremental shortcut to find.

**Common Questions:**
- *Q: Can I work around EXCEPT?*
  A: Rewrite as an anti-join where possible, or use custom incrementalization.
- *Q: Does a UDF always break it?*
  A: Only SQL UDFs containing subqueries, and external functions. Plain scalar UDFs
  are fine.

**References:**
- https://docs.snowflake.com/en/user-guide/dynamic-tables/supported-queries
- https://docs.snowflake.com/en/user-guide/dynamic-tables/custom-incrementalization

---

## Slide 6: Diagnosing a Full-Refresh Regression

**Talking Points:**
- The first move is always `SHOW DYNAMIC TABLES`, not reading the DDL. What was
  asked for and what is running can differ.
- Query 2 is the audit sweep — run it per schema to find every table not running
  incrementally.
- Query 3 is the trend check. Rising average duration is the only signal you get
  that a still-INCREMENTAL table has outgrown its change budget.
- Walk the `refresh_mode_reason` values. `NULL` is the good case.
- Land the warning hard: `UPSTREAM_USES_FULL_REFRESH` means the table in front of
  you is fine and its parent is the cause. People burn hours rewriting the wrong
  definition.

**Key Insight:**
Three of the four reason values point at a different fix location — the definition,
the DDL, or upstream. Reading the reason first tells you where to work.

**Common Questions:**
- *Q: Where does this data live?*
  A: `SHOW DYNAMIC TABLES` for current state; the
  `DYNAMIC_TABLE_REFRESH_HISTORY` table function for history.
- *Q: Can I alert on it?*
  A: Yes — schedule the audit sweep and alert when a table's mode or average
  duration changes.

**References:**
- https://docs.snowflake.com/en/user-guide/dynamic-tables/troubleshoot-refreshes
- https://docs.snowflake.com/en/sql-reference/functions/dynamic_table_refresh_history

---

## Slide 7: The Five Percent Myth

**Talking Points:**
- Ask the room what happens when more than five percent of a base table changes.
  Most people say Snowflake switches to full refresh. It does not.
- Five percent is a performance guideline for when incremental works well. The
  configured mode never changes based on change volume.
- The operational consequence in the highlight box is the real content: nothing
  alerts you. The table keeps running incrementally, more expensively than full
  would, indefinitely.
- Walk the four remediation cards — they map change *pattern* to mode. Consistently
  high churn is different from occasional bulk loads, and they get different answers.

**Key Insight:**
The absence of an automatic switch is a design choice for predictability, not an
omission. It does mean the cost regression is entirely yours to detect.

**Common Questions:**
- *Q: So how do I know when to switch?*
  A: Compare average refresh duration between modes using
  `DYNAMIC_TABLE_REFRESH_HISTORY`. That comparison is the only signal.
- *Q: Is five percent measured per refresh or per day?*
  A: Between refreshes. Tightening target lag reduces the per-refresh change
  fraction.

**References:**
- https://docs.snowflake.com/en/user-guide/dynamic-tables/refresh-modes
- https://docs.snowflake.com/en/user-guide/dynamic-tables/refresh-optimization

---

## Slide 8: Pipeline Shape

**Talking Points:**
- Refresh mode is per-table. An upstream FULL table does not force downstream
  tables to FULL — with one exception.
- The exception: an INCREMENTAL or ADAPTIVE table can sit downstream of a FULL
  table only if that upstream table has a system-derived unique key or a frozen
  region.
- The non-obvious half is the second card: in that scenario you must set
  `REFRESH_MODE = INCREMENTAL` **explicitly**. AUTO will not resolve to incremental
  there, so the default silently costs you full refreshes down the chain.
- Mention replication and cloning both reinitialize — relevant for DR planning.

**Key Insight:**
Pipeline topology is part of the refresh-mode decision. Diagnosing a single table
in isolation can leave you rewriting a definition that was never the problem.

**Common Questions:**
- *Q: What is a system-derived unique key?*
  A: Snowflake deriving a key from the definition, letting it compute row-level
  changes across full refreshes. See the input-data-optimization page.
- *Q: Does a frozen region help elsewhere?*
  A: Yes — it also reduces reinitialization cost under ADAPTIVE.

**References:**
- https://docs.snowflake.com/en/user-guide/dynamic-tables/input-data-optimization
- https://docs.snowflake.com/en/user-guide/dynamic-tables/frozen-regions

---

## Slide 9: Cost Controls

**Talking Points:**
- The dual-warehouse pattern is the highest-leverage change on this slide.
  Reinitialization is a full scan; routine incremental refresh is not. One
  warehouse sized for both over-provisions the common case.
- Target lag is a cost dial, not just a freshness setting. Halving it roughly
  doubles refresh count. Ask what the consumer actually needs.
- Mode changes are not free: `CREATE OR REPLACE` reinitializes the table **and
  every downstream dependency**. Prefer `CREATE OR ALTER`.
- Splitting stacked blocking operators (GROUP BY + DISTINCT + window) into chained
  simpler tables often restores incremental efficiency.

**Key Insight:**
Most dynamic table cost problems are configuration, not query optimisation. Warehouse
split, target lag, and refresh mode account for the majority.

**Common Questions:**
- *Q: How much bigger should the init warehouse be?*
  A: Size it against a real reinitialization measured from refresh history, not a
  guess.
- *Q: Does `TARGET_LAG = DOWNSTREAM` help?*
  A: It defers to consumers' needs and can avoid refreshing more often than
  anything reads.

**References:**
- https://docs.snowflake.com/en/user-guide/dynamic-tables/refresh-optimization
- https://docs.snowflake.com/en/sql-reference/sql/create-dynamic-table
- https://www.snowflake.com/en/blog/whats-new-dynamic-tables-faster-flexible/

---

## Slide 10: Custom Incrementalization

**Talking Points:**
- Frame as the escape hatch, reached for only after the supported shapes are
  exhausted. Public Preview — say so.
- What it gives you: define refresh logic as MERGE or INSERT inside `REFRESH USING`.
  Snowflake keeps scheduling, retries, and transactional guarantees.
- What it costs you, and this is the warning box: it bypasses standard query
  analysis, so Snowflake no longer verifies your logic matches what re-running the
  definition would produce. Correctness becomes yours.
- Point at the developer guide's worked `CHANGES(INFORMATION => APPEND_ONLY)`
  example before anyone writes their own.

**Key Insight:**
This converts a platform guarantee into an engineering responsibility. Worth it for
a genuinely valuable transformation that cannot be expressed otherwise; a bad
default.

**Common Questions:**
- *Q: Production-ready?*
  A: Public Preview as of 2026-05-26. Check current status.
- *Q: What if my logic is wrong?*
  A: You get a silently incorrect table. Nothing cross-checks it against the
  definition. Test against a FULL-refresh equivalent.

**References:**
- https://docs.snowflake.com/en/user-guide/dynamic-tables/custom-incrementalization
- https://docs.snowflake.com/en/release-notes/2026/other/2026-05-26-dynamic-tables-custom-incremental
- https://www.snowflake.com/en/developers/guides/comprehensive-guide-to-dynamic-tables/

---

## Slide 11: Takeaways

**Talking Points:**
- Four-step strip is the checklist: set the mode explicitly, prefer ADAPTIVE,
  verify with `SHOW`, watch refresh duration over time.
- If only one thing lands, make it "never ship AUTO."
- Close on the audit: most rooms have dynamic tables in production nobody has
  checked the resolved mode on. Send them to slide 6's sweep query.

**Key Insight:**
Dynamic tables are declarative about *what* but not about *cost*. The mode, the
warehouse split, and the target lag are where cost is decided, and all three are
invisible unless someone looks.

**Common Questions:**
- *Q: Where do I start Monday?*
  A: Run the slide 6 sweep across production schemas. Anything with a non-NULL
  `refresh_mode_reason` is a candidate.

**References:**
- https://docs.snowflake.com/en/user-guide/dynamic-tables/refresh-modes
- https://docs.snowflake.com/en/user-guide/dynamic-tables/decision-guide
- https://docs.snowflake.com/en/user-guide/dynamic-tables/overview
