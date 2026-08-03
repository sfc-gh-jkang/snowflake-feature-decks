# Speaker Notes: Storage Lifecycle Policies — Archive Before You Pay

## Presentation Context

For SEs and data engineers looking at a storage bill, and for anyone advising on
retention or compliance. After this session someone should be able to decide
whether lifecycle policies fit a table, choose the right tier the first time, and
know which decisions cannot be undone.

Eleven slides. Slides 1–3 are the mechanics and the tier decision. Slides 4–6 are
the irreversible choice, retrieval, and locking. Slides 7–9 are replication,
exclusions, and cost. Slides 10–11 are monitoring and the wrap.

**Support status:** GA since 2025-11-07, and everything here is from the product
documentation. Cloud availability differs by tier — COLD is AWS and GCP only, and
the whole feature is unavailable in the People's Republic of China. Verify in the
customer's region before designing.

The through-line: this feature saves real money, and three of its decisions are
one-way doors. Lead with the savings, but do not let anyone attach a policy before
slide 4.

---

## Slide 1: Hero / Overview

**Talking Points:**
- Frame the value in one line: old rows move to cheap storage or get deleted, on a
  daily schedule, with no warehouse and no orchestration to maintain.
- The four stat cards preview the arc — the 4× saving, the 48-hour retrieval cost
  of that saving, the zero-ops execution model, and the irreversibility.
- Set the expectation early that this deck spends as much time on traps as on
  benefits. That is deliberate; the traps are where the money is lost.

**Key Insight:**
The savings are easy and the mistakes are permanent. That asymmetry is the reason
to spend ten minutes on it before enabling anything.

**Common Questions:**
- *Q: Do I need a warehouse?*
  A: No. Policies run daily on Snowflake-managed shared compute.
- *Q: Is it GA?*
  A: Yes, since 2025-11-07 — but check tier availability for the customer's cloud.

**References:**
- https://docs.snowflake.com/en/release-notes/2025/other/2025-11-07-storage-lifecycle-policies-ga
- https://docs.snowflake.com/en/user-guide/storage-management/storage-lifecycle-policies

---

## Slide 2: How It Works

**Talking Points:**
- Walk the four-step strip. The whole model is: write an expression, attach it,
  Snowflake runs it daily.
- Attaching triggers a first run within minutes — useful for demos, because you do
  not wait a day to show something happening.
- The chunking behaviour matters operationally: a large table's first pass may span
  several daily runs. A policy that has not finished is normal, not stuck. People
  file support tickets over this.
- Note the supported-table nuance: standard tables, dynamic tables, and interactive
  tables **that do not auto-refresh**.

**Key Insight:**
There is no scheduler to build and no warehouse to size. The operational surface is
just the expression and the tier — which is why the tier decision deserves the
attention slide 4 gives it.

**Common Questions:**
- *Q: Can I force a run?*
  A: Attaching triggers one. Otherwise it is daily.
- *Q: Does it respect masking policies?*
  A: Snowflake internally and temporarily bypasses governance policies to evaluate
  the expression. Worth knowing for an audit conversation.

**References:**
- https://docs.snowflake.com/en/user-guide/storage-management/storage-lifecycle-policies
- https://docs.snowflake.com/en/user-guide/dynamic-tables/storage-lifecycle-policies

---

## Slide 3: COOL vs COLD

**Talking Points:**
- Work down the table. The two rows that decide most conversations are retrieval
  time and cloud availability, not price.
- COLD is 4× cheaper to store but retrieval can take **48 hours**, and a restore
  is capped at 1 million files.
- The one-time archiving cost is identical for both tiers — so the decision is
  purely about ongoing storage versus retrieval characteristics.
- Land the warning: expiration works everywhere, COOL works on all three clouds,
  **COLD is AWS and GCP only**. Do not design a COLD tier for an Azure account.

**Key Insight:**
Frame the choice as a question for the data owner, not a cost optimisation for you
to make alone: if someone needs a row back, is a 48-hour wait acceptable? If the
answer is no or unknown, COOL.

**Common Questions:**
- *Q: Can I use COLD on Azure?*
  A: No. COOL and expiration only.
- *Q: What if retrieval takes longer than 48 hours?*
  A: 48 hours is the documented upper bound. Plan the process around it — this is
  not an interactive workflow.

**References:**
- https://docs.snowflake.com/en/user-guide/storage-management/storage-lifecycle-policies

---

## Slide 4: Creating a Policy

**Talking Points:**
- Two examples: expiration-only, and archive-then-expire. The difference is just
  whether `ARCHIVE_FOR_DAYS` is present.
- The minimums are enforced at creation: COOL needs ≥ 90 days, COLD needs ≥ 180.
- Emphasise reusability — a policy is a schema-level object, so one policy can
  serve many tables and the rule changes in one place.
- The expression is arbitrary boolean logic over the bound column. Age is the
  common case, not the only one.

**Key Insight:**
The DDL is small enough that the risk is not writing it, it is attaching it before
the tier conversation has happened.

**Common Questions:**
- *Q: Can one table have several policies?*
  A: One archival policy per table, and the tier is fixed for the table's lifetime.
- *Q: Can I see what is attached?*
  A: `SHOW STORAGE LIFECYCLE POLICIES` and `DESCRIBE`.

**References:**
- https://docs.snowflake.com/en/sql-reference/sql/create-storage-lifecycle-policy
- https://docs.snowflake.com/en/user-guide/storage-management/storage-lifecycle-policies-create-manage

---

## Slide 5: The Irreversible Choice

**Talking Points:**
- Slow down here. This is the slide that prevents an expensive mistake.
- A table is permanently assigned to its archive tier **for its lifetime**. Not per
  policy — per table.
- Dropping the policy and attaching a different one does not reset it. The table
  remembers. Changing the tier requires contacting Snowflake Support to delete the
  archived data.
- The failure is usually organisational, not technical: someone doing a storage
  cleanup picks a tier in an afternoon and the account lives with it.
- Note the audit trick: `DESCRIBE` still reports `archive_tier` even after an
  archival policy is converted to expiration-only, so you can see what a table is
  already committed to.

**Key Insight:**
Treat attaching an archival policy like a schema migration, not a config tweak.
One reversible-looking command, one permanent outcome.

**Common Questions:**
- *Q: Really no way to switch?*
  A: Not without Snowflake Support deleting the archived data.
- *Q: What if I am not sure?*
  A: COOL. It is more expensive but it preserves instant retrieval, and the
  regret is financial rather than operational.

**References:**
- https://docs.snowflake.com/en/user-guide/storage-management/storage-lifecycle-policies
- https://docs.snowflake.com/en/sql-reference/sql/desc-storage-lifecycle-policy

---

## Slide 6: Retrieving Archived Data

**Talking Points:**
- The key constraint: archived rows are **not queryable in place**. There is no
  transparent read-through. You create a new table from the archive.
- Lead with `SYSTEM$GET_TABLE_ARCHIVE_METADATA` — row counts and column min/max at
  **no retrieval cost**. Confirm the data is there before paying to pull it. Most
  people do not know this exists.
- Narrow the `WHERE`. Retrieval is billed, so a precise predicate is the difference
  between a week and a decade.
- `TRANSIENT` on the restore table avoids Fail-safe cost on something you intend to
  drop.
- Removing a policy does not delete the archive. Neither does truncating the table.
  `UNDROP` within Time Travel brings the archive back too.

**Key Insight:**
Retrieval is a deliberate, billed, sometimes slow operation. Design the process
around that rather than assuming archived data is merely "slower to query."

**Common Questions:**
- *Q: Can I query the archive directly?*
  A: No. `CREATE TABLE ... FROM ARCHIVE OF` only.
- *Q: What does a restore cost?*
  A: Depends on tier and volume — see the Service Consumption Table. Check
  metadata first to size it.

**References:**
- https://docs.snowflake.com/en/user-guide/storage-management/storage-lifecycle-policies-retrieving-archived-data
- https://docs.snowflake.com/en/sql-reference/functions/system_get_table_archive_metadata

---

## Slide 7: What Gets Locked

**Talking Points:**
- During a policy run, `UPDATE`, `DELETE`, and `MERGE` are locked on that table.
  `INSERT`, `COPY`, and `SELECT` continue.
- The pipeline consequence in the highlight box is the real content: ingestion is
  fine, but anything doing merge-style upserts on the same table can block.
- Combine that with the chunking behaviour from slide 2 — on a large table the run
  may span multiple days, which widens the contention window considerably.
- If a table is both lifecycle-managed and MERGE-updated, that is a scheduling
  conversation, not a surprise to discover in production.

**Key Insight:**
"No warehouse required" does not mean "no impact." The cost moved from compute to
concurrency.

**Common Questions:**
- *Q: Can I control when it runs?*
  A: Not directly — it is a daily Snowflake-managed run.
- *Q: Will my dbt merge fail?*
  A: It can block. Design for retry, or avoid overlapping heavy MERGE windows.

**References:**
- https://docs.snowflake.com/en/user-guide/storage-management/storage-lifecycle-policies

---

## Slide 8: Replication and Cloning

**Talking Points:**
- Replication: policies and their associations replicate. **Archived data does
  not.** After failover, source-account archived data is unavailable in the target.
- Snowflake never automatically runs secondary policies on secondary tables, even
  after failover. Execution pauses in the original primary and resumes on failback.
- Cloning: policies are not auto-applied to clones, and archiving from one table in
  a clone group creates copies in both standard and archive tiers — **you pay for
  both**. A clone can quietly cancel the saving.
- Land the warning as a DR statement: if a compliance obligation is satisfied by
  archived rows, that obligation is **not** met in the failover account.

**Key Insight:**
This belongs in the DR plan explicitly. It is the kind of gap that is invisible
until an auditor or an actual failover finds it.

**Common Questions:**
- *Q: How do I get archived data into the DR account?*
  A: It does not replicate. Plan retention with that constraint in mind.
- *Q: Does cloning a table double my archive cost?*
  A: You pay for standard and archive copies as described — model it before cloning
  large lifecycle-managed tables.

**References:**
- https://docs.snowflake.com/en/user-guide/storage-management/storage-lifecycle-policies
- https://docs.snowflake.com/en/user-guide/storage-management/storage-lifecycle-policies-billing

---

## Slide 9: Where It Does Not Apply

**Talking Points:**
- Run this list **before** promising a customer that lifecycle policies will fix
  their storage bill. It is a short slide with high save-value.
- The ones that most often disqualify a use case: shared tables (both provider and
  consumer sides), Native Apps, and auto-refreshing interactive tables.
- Python, Java, and Scala UDFs, external functions, and UDFs with external access
  cannot appear in the expression.
- The encryption pair in the info box is for security reviews: TSS can protect
  archived data, but Snowflake **does not rekey** it. The documented remedy for
  suspected key compromise is retrieve to a new table, re-archive, drop the old
  archive.

**Key Insight:**
Most disqualifications are structural rather than fixable. Check the list early so
the conversation does not have to be walked back later.

**Common Questions:**
- *Q: Can I archive a table I am sharing?*
  A: No — not on either side of the share.
- *Q: What about a dynamic table?*
  A: Supported, with its own documentation page.

**References:**
- https://docs.snowflake.com/en/user-guide/storage-management/storage-lifecycle-policies
- https://docs.snowflake.com/en/user-guide/dynamic-tables/storage-lifecycle-policies

---

## Slide 10: Monitoring and Cost

**Talking Points:**
- Five cost components. Four are intuitive; the fifth is not.
- The penalty-bytes trap: data deleted before `ARCHIVE_FOR_DAYS` elapses is still
  billed for the remainder of the period. Setting six years and cleaning up after
  six months does not save five and a half years.
- Therefore `ARCHIVE_FOR_DAYS` is a commitment, not a ceiling. Choose it against
  the real retention requirement.
- Sizing advice: apply the tier discount to the share of the table that is actually
  older than the threshold, not to the whole table. This is where optimistic
  savings estimates come from.

**Key Insight:**
The savings estimate is only as good as the age distribution of the data. Measure
what fraction actually qualifies before quoting a number to an AE or a customer.

**Common Questions:**
- *Q: Where are the rates?*
  A: Tables 3(e) and 4(f) of the Snowflake Service Consumption Table.
- *Q: How do I know it is working?*
  A: Monitor policy runs — confirm rows are moving and that large operations are
  progressing across daily runs.

**References:**
- https://docs.snowflake.com/en/user-guide/storage-management/storage-lifecycle-policies-billing
- https://docs.snowflake.com/en/user-guide/storage-management/storage-lifecycle-policies-monitoring

---

## Slide 11: Takeaways

**Talking Points:**
- Four-step strip is the pre-flight checklist: check cloud and tier availability,
  agree the tier with the data owner, set the period deliberately, confirm DR
  coverage.
- If only one thing lands, make it the irreversibility of the tier.
- Close on the sizing point — quantify the qualifying share before promising a
  saving.

**Key Insight:**
This is one of the few Snowflake features where the technical work is trivial and
essentially all the value is in the decisions made before you run the DDL.

**Common Questions:**
- *Q: Where do I start?*
  A: Find the largest tables, measure what share of rows is older than the
  candidate threshold, and take that number to the data owner with the tier
  question.

**References:**
- https://docs.snowflake.com/en/user-guide/storage-management/storage-lifecycle-policies
- https://docs.snowflake.com/en/user-guide/storage-management/storage-lifecycle-policies-create-manage
- https://www.snowflake.com/en/blog/storage-lifecycle-policies-ga/
