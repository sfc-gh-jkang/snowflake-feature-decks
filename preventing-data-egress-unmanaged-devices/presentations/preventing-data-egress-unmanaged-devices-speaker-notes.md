# Speaker Notes: Preventing Data Download to Unmanaged Devices

## Presentation Context

**Audience:** customer security teams, IAM/endpoint owners, and the data-platform
team that has to implement whatever the security team decides. Also useful for SEs
walking into a "lock down Snowflake" conversation cold.

**What they should be able to do afterwards:** stop treating this as a UI problem,
and leave with an ordered list of seven changes where the first two do most of the
work and neither needs new spend.

**Status of the claims:** everything in this deck is GA and in the product
documentation, with two exceptions that must be stated out loud rather than
glossed:

1. **`AGGREGATE_ACCESS_HISTORY` is a preview feature** (Enterprise Edition or
   higher). `ACCESS_HISTORY` itself is GA. Don't let a customer build a compliance
   commitment on the preview view without flagging it.
2. **The Snowsight download claim is sourced from a Snowflake Community Knowledge
   Base article, not the product docs.** That article states Snowsight has no
   setting to cap download rows or file size, and offers `ROWS_PER_RESULTSET` as
   the workaround. This is the weakest-sourced claim in the deck. Say so. It is
   also the claim security teams care most about, so being straight about the
   sourcing buys you credibility for everything else.

There is no keyboard navigation — this is a scroll page, not a slide deck. If
someone asks for arrow keys, the honest answer is the format doesn't have them.

### SQL verification status (2026-08-03)

Every statement in this deck was run against a live Snowflake account (Enterprise,
AWS us-east-1). What was actually executed vs. compile-validated:

| Statement | Status |
|---|---|
| `CREATE NETWORK RULE` / `CREATE NETWORK POLICY` | Executed, created successfully |
| `CREATE AUTHENTICATION POLICY` | Executed, created successfully |
| `CREATE SESSION POLICY` | Executed, created successfully |
| `CREATE PROJECTION POLICY` + `ALTER TABLE … SET PROJECTION POLICY` | Executed, **behaviour verified both ways** |
| `ALTER USER … SET PREVENT_UNLOAD_TO_INLINE_URL` | Executed on a throwaway user, confirmed via `SHOW PARAMETERS` |
| `SHOW PARAMETERS LIKE 'NETWORK_POLICY' IN ACCOUNT` | Executed, returns the active policy name |
| `ALTER ACCOUNT SET NETWORK_POLICY` | **Compile-validated only** |
| `ALTER ACCOUNT SET AUTHENTICATION POLICY … FOR ALL PERSON USERS` | **Compile-validated only** |
| `ALTER ACCOUNT SET PREVENT_UNLOAD_*` / `REQUIRE_STORAGE_INTEGRATION_*` / `ENFORCE_NETWORK_RULES_*` | Compile-validated only |

The two account-wide activation statements are compile-validated rather than
executed for a specific reason worth repeating to any customer: **on a test account
that already had an activated network policy, running `ALTER ACCOUNT SET
NETWORK_POLICY` with this deck's example CIDRs would have replaced the working
policy and locked the operator out.** Never demo that line live. It is the last
step of a planned change with a verified break-glass path, not a worksheet paste.

Two bugs were found and fixed by this testing — see Slide 4 and Slide 7 notes. If
you change any SQL in this deck, re-run it before presenting.

---

## Slide 1: Hero / Overview

**Talking Points:**
- Open by naming the ask back to them: "you want to stop data landing on a
  personal phone." Then immediately reframe: the download button is the one thing
  you cannot switch off, so we're going to attack everything upstream of it.
- Walk the four stat cards. "Any device" is the Snowflake default and usually the
  first surprise. "18 h" is the Snowsight idle default and usually the second.
  "0" is the honest one — no setting disables Download Results.
- Set the arc: six layers, ordered by strength per unit of effort, then a
  deliberate slide on what Snowflake genuinely cannot do.

**Key Insight:**
A download is the last step in a four-step chain. Break any earlier step and the
download never becomes possible. Every hour spent trying to break the last step
is an hour spent on the only unwinnable fight.

**Common Questions:**
- *Q: Is any of this Business Critical only?*
  A: One thing — privatelink-only enforcement. Everything else on the recommended
  sequence works on Enterprise. Data protection policies need Enterprise or higher.
- *Q: Can we just block the mobile app?*
  A: There is no Snowflake mobile app. Mobile access is a browser hitting Snowsight,
  or a credential hitting the REST API. The second one is the part people miss.

**References:**
- https://docs.snowflake.com/en/user-guide/network-policies
- https://docs.snowflake.com/en/sql-reference/sql/create-session-policy

---

## Slide 2: The Real Question

**Talking Points:**
- Walk the four-step flow out loud: reachable endpoint → successful auth → live
  session → readable data. Point at each step and name the layer that attacks it.
- The reframe is the whole point of the slide. Let it land before moving on.
- If the room pushes back ("we just want the button gone"), agree that it's a
  reasonable ask and promise a straight answer on it later — then deliver on
  slide 10. Don't argue here.

**Key Insight:**
Reframing from "prevent download" to "prevent session" turns an impossible
request into seven concrete configuration changes.

**Common Questions:**
- *Q: Isn't this just deflecting our requirement?*
  A: No — it over-delivers on it. Blocking the session also blocks screenshots,
  copy-paste, and REST API pulls, none of which a download control would touch.

**References:**
- https://docs.snowflake.com/en/user-guide/authentication-policies

---

## Slide 3: Why "Block the UI" Is the Wrong First Move

**Talking Points:**
- Read the `CLIENT_TYPES` quote verbatim. Do not paraphrase it — the words
  "best-effort", "should not be used as the sole control", and "does not restrict
  access to the Snowflake REST APIs" are Snowflake's own, and they carry more
  weight coming from the docs than from you.
- Note that Snowflake repeats this warning three separate times on one page.
  That level of repetition is deliberate.
- Walk the coverage table column by column. The `CLIENT_TYPES` row is the only one
  with a red badge, and it's the control most teams reach for first.
- If they already have a REST/SQL-API integration, this is the moment to point out
  that no authentication-policy client restriction covers it.

**Key Insight:**
`CLIENT_TYPES` is a UX control that looks like a security control. It belongs in
the design, but never as the boundary.

**Common Questions:**
- *Q: So CLIENT_TYPES is useless?*
  A: No. It's genuinely useful for scoping service accounts to `DRIVERS` so a
  leaked service credential can't be replayed into the web UI. It just isn't a
  boundary on its own.
- *Q: Does a network policy cover the REST API?*
  A: Yes. Network policies are evaluated before authentication, for all inbound
  access. That's why it's the recommended first move.

**References:**
- https://docs.snowflake.com/en/user-guide/authentication-policies

---

## Slide 4: Layer 1 — Identity: Where Device Posture Actually Lives

**Talking Points:**
- Say plainly that Snowflake has no concept of device posture. No fingerprinting,
  no jailbreak detection, no MDM awareness. This is not a gap to apologise for —
  it's correct separation of concerns, and the IdP is where that decision belongs.
- Entra ID's grant control is literally named "Require device to be marked as
  compliant", and it covers iOS and Android when the device is registered with
  Entra ID and enrolled in Intune. That is exactly the personal-phone scenario.
- Then deliver the warning box, because it's the highest-value sentence in the
  deck: **a local Snowflake password bypasses the IdP, and with it every
  Conditional Access rule.** Federating SSO while leaving passwords enabled is a
  very common half-finished state.
- Walk the SQL. Call out the break-glass admin line — the docs explicitly
  recommend keeping a non-restrictive policy on one admin to avoid lockout.
- Then the `MFA_ENROLLMENT` trap, which was verified as a hard error during
  testing. Setting `MFA_ENROLLMENT = 'REQUIRED'` while omitting `SNOWFLAKE_UI`
  from `CLIENT_TYPES` is rejected outright: *"If MFA_ENROLLMENT = 'REQUIRED',
  CLIENT_TYPES must include SNOWFLAKE_UI to allow for enrollment."* This is a
  genuinely useful thing to know in the room, because it means **you cannot both
  block the web UI and require Snowflake-native MFA enrollment.** One has to give.
  When the IdP owns MFA — which is the architecture this deck recommends —
  `MFA_ENROLLMENT = 'OPTIONAL'` is the correct choice, not a compromise.
- Close on precedence: network → authentication → password → session.

**Note on the SQL, if anyone copies it:** an earlier draft of this deck used a
property called `MFA_AUTHENTICATION_METHODS`. **That property does not exist** —
Snowflake rejects it with *"invalid property 'MFA_AUTHENTICATION_METHODS' for
'AUTHENTICATION_POLICY'"*. The real properties are `AUTHENTICATION_METHODS`,
`CLIENT_TYPES`, `CLIENT_POLICY`, `SECURITY_INTEGRATIONS`, `MFA_ENROLLMENT`,
`MFA_POLICY`, `PAT_POLICY`, `WORKLOAD_IDENTITY_POLICY` and `COMMENT`. The deck is
now correct, but if you see that property in any older copy, it will not run.

**Key Insight:**
Snowflake enforces *how* you authenticate; the IdP enforces *what device* may
authenticate. That division only holds if password auth is closed off, otherwise
users route around the IdP entirely.

**Common Questions:**
- *Q: How do we find users who still have a password?*
  A: Trust Center's secure-authentication readiness surfaces exactly this, and
  flags human users who aren't MFA-enforced.
- *Q: What about service accounts?*
  A: Different problem. Service accounts should use key-pair or OAuth with a
  dedicated network policy, and `CLIENT_TYPES = ('DRIVERS')`. They aren't
  device-bound and shouldn't be in a Conditional Access scope.
- *Q: We use Okta, not Entra.*
  A: Same architecture. Okta exposes device trust via Okta Verify with a managed-
  device signal. The Snowflake side is unchanged.

**References:**
- https://docs.snowflake.com/en/user-guide/authentication-policies
- https://learn.microsoft.com/en-us/entra/identity/conditional-access/policy-all-users-device-compliance
- https://learn.microsoft.com/en-us/entra/identity/conditional-access/concept-conditional-access-grant

---

## Slide 5: Layer 2 — Network

**Talking Points:**
- Quote the default: "Snowflake allows users to connect to the service and
  internal stage from any computer or device." Most people assume there's an
  implicit restriction. There isn't.
- Walk the SQL, then land hard on the warning box. **"A network policy doesn't
  restrict network traffic until it is activated."** Creating the object does
  nothing. This is the single most common misconfiguration in this whole area —
  teams build the policy, see it listed, and believe they're protected.
- Give them the verification one-liner: `SHOW PARAMETERS LIKE 'NETWORK_POLICY' IN
  ACCOUNT`. Blank value means inert. Have them run it live if the room allows.
- The "enumerate the full egress range" card matters practically: SASE and proxy
  vendors publish many egress IPs per data centre, and a policy with one or two
  addresses will break users the moment traffic shifts nodes. Point them at their
  vendor's published range list rather than observed IPs.
- Privatelink-only is the strongest form but it's Business Critical, and it will
  break any SaaS tool that can't use private connectivity. Frame it as a later
  step contingent on an integration inventory, not a quick win.

**Key Insight:**
This is the cheapest broad control available and it's frequently 90% built and 0%
activated. Check activation before designing anything else.

**Common Questions:**
- *Q: Won't this break remote workers?*
  A: Only if they bypass VPN/SASE. That's the point — it converts "any network"
  into "our managed egress", which is usually the actual policy intent.
- *Q: Can we exempt specific service accounts?*
  A: Yes, activate at user scope with a different policy. User-level overrides
  account-level.
- *Q: Rules or IP lists?*
  A: Rules for anything new. `ALLOWED_IP_LIST` still works but Snowflake advises
  against using both mechanisms in one policy.

**References:**
- https://docs.snowflake.com/en/user-guide/network-policies
- https://docs.snowflake.com/en/user-guide/security-disable-public-access-privatelink

---

## Slide 6: Layer 3 — Session

**Talking Points:**
- The number that gets a reaction: Snowsight idle default is 1080 minutes, which
  is 18 hours. A tab opened at 9am is still live at 3am.
- Clients and programmatic sessions default to 240 minutes — a different value,
  set by a different parameter. People routinely set one and assume both.
- Both accept 5 to 1440 minutes.
- Max-lifespan is the more interesting control for this use case: it forces a real
  re-authentication regardless of activity, which re-runs the IdP device check.
  Idle timeout alone can be defeated by a page that polls.
- Don't over-tighten in one step. 30 minutes UI idle is defensible; 5 minutes will
  generate helpdesk tickets and get rolled back.

**Key Insight:**
Idle timeout limits abandoned sessions; max lifespan is what forces device
re-evaluation. For a device-posture goal, max lifespan is the one that matters.

**Common Questions:**
- *Q: Does this log people out mid-query?*
  A: No, these are idle and lifespan limits on the session, not query timeouts.
- *Q: Can we set different timeouts per group?*
  A: Yes — apply the session policy at user level for tighter groups; account
  level is the baseline.

**References:**
- https://docs.snowflake.com/en/sql-reference/sql/create-session-policy

---

## Slide 7: Layer 4 — Limit What Is Downloadable at All

**Talking Points:**
- Frame it: everything so far assumed you want to block the session. This layer
  assumes the session is legitimate and asks what should be *in* the result.
- Walk all five policy types quickly, then slow down on **projection policy** —
  it's the least-known and the most directly on-point. A column can be used in a
  `WHERE` clause but cannot be projected into output. That is precisely
  "filterable but not exportable".
- Aggregation policy is the right answer for analyst populations that need
  cohort-level numbers but must not isolate individuals.
- Push the tag-based application pattern. Attaching policies to a governance tag
  means new sensitive columns inherit protection instead of relying on someone
  remembering.
- All five require Enterprise Edition or higher.
- **Deliver the `SELECT *` caveat — this was verified live and it will come up in
  implementation.** A projection policy does not silently drop the column. Both
  `SELECT ssn` and bare `SELECT *` fail with *"The following columns are restricted
  by a Projection Policy."* Verified behaviour on a two-row test table: `SELECT id,
  name WHERE ssn = '111-22-3333'` returned the row correctly, while `SELECT *`
  errored. So the "filterable but not projectable" claim is exactly true — and the
  cost is that every `SELECT *` against that table breaks. Tell them to inventory
  `SELECT *` usage in views and BI extracts before applying it.
- One more operational detail found in testing: you cannot drop a schema containing
  a network rule that is still referenced by a network policy — Snowflake blocks it
  with *"Cannot drop schema … as it includes network rule - policy associations."*
  Drop or alter the policy first. Relevant if they build these in a sandbox schema
  and then try to clean up.

**Key Insight:**
This is the only layer that still helps when access is fully authorised. A managed
laptop on the corporate network downloading a masked column is a non-event, and
that's the end state you want.

**Common Questions:**
- *Q: Does masking slow queries down?*
  A: Policies are evaluated at query time. Keep the policy body simple —
  expensive lookups inside a policy are the usual cause of complaints.
- *Q: Can a user with a high privilege see through a mask?*
  A: Only if the policy body grants it. These are independent of role grants —
  that's the design intent. `SELECT` privilege does not imply visibility.
- *Q: Difference between projection and masking?*
  A: Masking returns an altered value. Projection refuses to return the column at
  all while still allowing it as a predicate.

**References:**
- https://docs.snowflake.com/en/user-guide/data-protection-policies-snowsight
- https://docs.snowflake.com/en/user-guide/projection-policies

---

## Slide 8: Layer 5 — Close the Bulk Export Paths

**Talking Points:**
- Reframe the scale: the download button moves a result grid, `COPY INTO
  <location>` moves a table. If the concern is volume, this is the bigger hole.
- Walk the path explicitly: `COPY INTO` to an internal stage, then `GET` to local
  disk. Or straight to an external bucket.
- All of these parameters are off by default. That's the headline.
- Walk the table. Flag that `PREVENT_UNLOAD_TO_INTERNAL_STAGES` became settable at
  both account and user level in the 2025_01 behaviour change bundle, and the
  **user-level value wins** — so an account-level `TRUE` can be silently overridden
  per user. Tell them to audit for user-level overrides before declaring victory.
- Both `PREVENT_UNLOAD_*` parameters are ACCOUNTADMIN-only to set.
- `ENFORCE_NETWORK_RULES_FOR_INTERNAL_STAGES` is the one that closes the gap where
  stage traffic ignores the network policy you set in Layer 2.
- The integration inventory point in the context box deserves 30 seconds: BI tools,
  automation platforms and AI assistants connected over OAuth each read data on
  their own infrastructure, reachable from a phone, and no browser or driver
  control touches that path. Enumerate them, least-privilege each one, and scope
  their service users to `DRIVERS`.

**Key Insight:**
Result-grid downloads are the visible path; bulk unload is the high-volume one.
Closing unload is a handful of `ALTER ACCOUNT` statements and is usually the
fastest large win after the network policy.

**Common Questions:**
- *Q: Will this break our ETL?*
  A: Possibly, if it unloads to internal stages. Inventory first. Legitimate
  pipelines should use storage integrations, which is what the
  `REQUIRE_STORAGE_INTEGRATION_*` parameters force anyway.
- *Q: How do we find who's unloading today?*
  A: Query history for `COPY INTO` against stage locations, plus ACCESS_HISTORY
  for what was read.

**References:**
- https://docs.snowflake.com/en/sql-reference/sql/copy-into-location
- https://docs.snowflake.com/en/release-notes/bcr-bundles/2025_01/bcr-1841
- https://docs.snowflake.com/en/sql-reference/sql/alter-account

---

## Slide 9: Layer 6 — Prove It, Then Watch It

**Talking Points:**
- Preventive controls decay. Somebody adds a user-level override, or a new service
  account arrives with a password. This layer is about evidence and drift.
- Trust Center is the fastest path to "which human users can still use a
  password" — it ships a secure-authentication readiness view and an MFA
  enforcement scanner. No build required.
- `ACCESS_HISTORY` answers the question auditors actually ask: not "was a query
  run" but "was regulated data read, by whom, in which column".
- `AGGREGATE_ACCESS_HISTORY` covers short transactional queries that
  `ACCESS_HISTORY` omits, aggregated into one-minute intervals. **State that it is
  a preview feature** and Enterprise or higher.
- The four-numbers box is the practical takeaway. Each is one query. In most
  accounts at least one comes back wrong. Offer to run them together.

**Key Insight:**
The four questions in the highlight box are a complete posture check for this
threat model, and they take about five minutes.

**Common Questions:**
- *Q: How far back does ACCESS_HISTORY go?*
  A: It's an Account Usage view with the standard retention for that schema —
  check the current documented retention rather than quoting a number from memory.
- *Q: Can Trust Center alert us?*
  A: Yes, it supports proactive notifications for findings.

**References:**
- https://docs.snowflake.com/en/user-guide/trust-center/overview
- https://docs.snowflake.com/en/sql-reference/account-usage/aggregate_access_history

---

## Slide 10: What Snowflake Cannot Do

**Talking Points:**
- This is the trust-building slide. Deliver it without hedging. Security teams
  discount vendors who won't name limitations, and they will find these during
  implementation anyway.
- No setting disables Download Results. Say it flatly.
- `ROWS_PER_RESULTSET` is the workaround, and be honest about its side effect: it
  limits **every** query the user runs, not just exports. It is a blunt instrument
  and it will surprise analysts.
- No device fingerprinting. No screenshot or copy-paste prevention — that's MDM
  and endpoint DLP, and no database does it.
- Then the sourcing note. The download-limit claim comes from a Community
  Knowledge Base article, not the product docs. Say that out loud and recommend
  they re-verify before writing it into a compliance narrative. This is the single
  most credibility-positive sentence you will say in the meeting.

**Key Insight:**
Naming the five things Snowflake can't do is what makes the other six layers
believable.

**Common Questions:**
- *Q: Is a download-disable feature on the roadmap?*
  A: Don't speculate. Take it as a feature request and route it properly.
- *Q: Then how do we satisfy our policy as written?*
  A: Usually by amending the control statement from "prevent download" to
  "restrict access to managed devices on approved networks, and limit exposed
  data" — which is both achievable and stronger. Offer to help word it.

**References:**
- https://community.snowflake.com/s/article/How-to-limit-the-number-of-rows-or-file-size-that-can-be-downloaded-via-SnowSight

---

## Slide 11: Recommended Sequence

**Talking Points:**
- Emphasise the ordering rationale: strength per unit of effort. Steps 1 and 2
  deliver most of the outcome, need no edition change and no new spend.
- Step 1 is often a five-minute change because the policy already exists and was
  never activated.
- Step 2 is the one with change-management weight — you're taking passwords away
  from humans. Pair it with the break-glass admin exception.
- Step 3 moves to the IdP team, so it's a different owner and a different change
  window. Name that explicitly so it doesn't stall.
- Steps 4–7 are incremental hardening and can run in parallel.
- Close on the one-sentence version and then stop talking. Let them react.
- Suggested exit action: agree to run the four verification queries together and
  put dates against steps 1–3.

**Key Insight:**
Sequence matters more than completeness. Doing step 5 before step 2 hardens the
export path while leaving the identity bypass wide open.

**Common Questions:**
- *Q: What can we do today?*
  A: Check whether a network policy is activated, and count human users who can
  still authenticate with a password. Both are single queries.
- *Q: Who owns this?*
  A: Split ownership: platform team owns 1, 4, 5, 6, 7; IAM team owns 2 and 3.
  Say this out loud — unassigned steps are why these programmes stall.

**References:**
- https://docs.snowflake.com/en/user-guide/network-policies
- https://docs.snowflake.com/en/user-guide/authentication-policies
- https://docs.snowflake.com/en/user-guide/trust-center/overview
