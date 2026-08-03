# Speaker Notes: EXTERNAL + Free: What a Private App Listing Actually Requires

## Presentation Context

For SEs and Solution Architects working with a partner or ISV who is building a
Snowflake Native App and intends to distribute it to their own customers by
private listing. Also usable directly with the partner's product and engineering
leads — there is nothing Snowflake-internal in the deck.

After this, the audience should be able to answer three questions without
checking: does a private listing need Snowflake's approval (no), what actually
triggers the security scan (the `DISTRIBUTION` property, not the listing), and
which single requirement is most likely to force an architecture change (the
Snowflake-authentication-first rule).

Everything in the deck is GA and documented in the Snowflake product docs. There
are no preview features and no field-observed-only claims. Two things need
flagging when you present:

1. Two SQL snippets in the deck differ from how the docs render their examples,
   because the docs' examples do not execute. The manifest `privileges`
   indentation and the `SET RELEASE DIRECTIVE` argument order were both corrected
   by running them. Say this plainly if asked — it is a credibility win, not a
   caveat.
2. The ongoing-monitoring / 30-business-day remediation window is documented as
   applying to apps published on the Snowflake Marketplace. Whether it attaches
   to a private-listing-only app is not stated. Do not assert either way.

This deck exists because "we need to start the Snowflake compliance and security
review process for our private listing" is a common and entirely reasonable
misreading of the documentation — and that review process does not exist. The goal
is to let you answer the question in one sitting rather than scheduling a meeting
to work it out.

---

## Slide 1: Hero / Overview

**Talking Points:**
- Open with the distinction that the whole deck hangs on: `DISTRIBUTION` controls
  whether Snowflake scans your *code*; listing type controls whether Snowflake
  reviews your *listing*. A private listing skips the second, never the first.
- Zero Snowflake approvals to schedule. This is the number that changes a partner's
  release plan, so lead with it.
- ~4 minutes was the observed scan time on a minimal app. Frame it as a floor, not
  a promise — a trivial app gives the CVE scanner nothing to do.
- Three release channels are created automatically now. This surprises people who
  learned the framework a year ago.
- The one-way door: once a private listing is published you cannot change the
  associated share.

**Key Insight:**
Partners conflate "external distribution" with "Snowflake gatekeeping." They are
separate. External distribution turns on an automated scan they run themselves;
Snowflake gatekeeping only exists on the Marketplace path.

**Common Questions:**
- *Q: Is this GA?*
  A: Yes, all of it. The Native App Framework is GA on supported cloud platforms,
  and private listings, release channels, and Cross-Cloud Auto-Fulfillment are all
  documented product features.
- *Q: So we need nothing at all from Snowflake?*
  A: For a free private listing, correct — no approval, no provider profile, no
  Stripe. You need an ACCOUNTADMIN to have accepted the Customer-Controlled Data
  Sharing Functionality Terms, and that is a click-through.

**References:**
- https://docs.snowflake.com/en/collaboration/provider-listings-creating-publishing
- https://docs.snowflake.com/en/developer-guide/native-apps/security-run-scan

---

## Slide 2: What EXTERNAL + Free Means

**Talking Points:**
- `INTERNAL` restricts you to private listings *within the same organization* and
  the scan is not performed at all. If the partner's "customers" are tenants
  inside their own org, stop here — the rest of the deck does not apply to them.
- `EXTERNAL` covers private listings outside the org, public listings, and
  Marketplace listings. One property, three destinations.
- Free is a pricing choice and is fully orthogonal to distribution. A free listing
  can be EXTERNAL; a paid listing needs an approved provider profile and Stripe,
  which is a different conversation with real lead time.
- Walk the spec rows — they are the fastest way to kill the "what do we need from
  you" question.

**Key Insight:**
Ask the org-topology question first, in every engagement. It is the single input
that determines whether this is a ten-minute conversation or a full one.

**Common Questions:**
- *Q: Can we start on INTERNAL and switch later?*
  A: Yes, and that is the documented best practice — but note that flipping
  `DISTRIBUTION` on a package that already has versions immediately scans the 10
  most recent patches of every version. Expect a burst of results.
- *Q: Do we need a provider profile?*
  A: Not for private listings. You do for paid listings or anything on the
  Marketplace.

**References:**
- https://docs.snowflake.com/en/developer-guide/native-apps/security-run-scan
- https://docs.snowflake.com/en/developer-guide/native-apps/ui-provider-publishing-app-package
- https://docs.snowflake.com/en/collaboration/collaboration-listings-legal
- https://docs.snowflake.com/en/collaboration/provider-listings-pricing-model

---

## Slide 3: What Snowflake Does Not Review

**Talking Points:**
- This is the slide that saves the partner weeks. The "Submit for Approval" step
  lives on the same documentation page as the private-listing publish steps, under
  a shared heading, and it is Marketplace-only.
- Walk the comparison table row by row. The only row where private and Marketplace
  agree is the automated security scan.
- The enforced app standards page — immediate utility, standalone, data-centric,
  transparent — is verified at Marketplace submission. It is a good design target
  if the partner may go public later. It is not a gate today. Be careful not to
  overcorrect here and imply the standards are worthless.
- Shared responsibility is worth saying out loud: the provider is the seller of
  record, and Snowflake's scan is explicitly not a substitute for the consumer's
  own due diligence. The partner's customers will still run their own review.

**Key Insight:**
The absence of a Snowflake gate is not the absence of scrutiny. It moves the
scrutiny to the consumer's security team, which is often slower and less
predictable than Snowflake would have been. Partners should prepare the privilege
list and endpoint disclosure for that audience.

**Common Questions:**
- *Q: Then why did we think there was a review?*
  A: Because the create-and-publish page covers both paths. Show them the two
  distinct sections.
- *Q: Should we meet the Marketplace standards anyway?*
  A: If a public listing is plausibly in your future, yes — retrofitting is more
  expensive. If it is definitively not, treat them as advisory.

**References:**
- https://docs.snowflake.com/en/collaboration/provider-listings-creating-publishing
- https://docs.snowflake.com/en/collaboration/guidelines-reqs-for-listing-apps
- https://docs.snowflake.com/en/developer-guide/native-apps/consumer-guide-evaluate

---

## Slide 4: What Snowflake Does Scan

**Talking Points:**
- Walk the four-step flow. The trigger people miss is step 3: with release
  channels enabled, the scan starts when a version is added to ALPHA or DEFAULT.
  Adding only to QA does not start it.
- Call out the `ADD VERSION` rejection explicitly. Release channels are enabled by
  default on new packages, so a lot of older sample code fails immediately with
  "Use REGISTER/DEREGISTER instead of ADD/DROP version syntax." This wastes real
  time if they hit it cold.
- The three channel descriptions are the product telling you the scan contract in
  its own words. DEFAULT = passed review, ALPHA = may not have passed, QA = never
  reviewed. Read them aloud; they land better than a paraphrase.
- Walk the observed-status table. The INTERNAL package sat at `NOT_REVIEWED` with
  a version in DEFAULT; the EXTERNAL package moved `NOT_REVIEWED` to `IN_PROGRESS`
  to `APPROVED`. Same code, same channel, different `DISTRIBUTION`. That is the
  cleanest possible demonstration of what the trigger actually is.
- On timing: be honest. Four minutes on an app with no dependencies. A real app
  with a large dependency tree gives the CVE scanner actual work. The defensible
  claim is "self-service, minutes to hours," not "always four minutes."
- Manual Snowflake review only enters on `REJECTED`. That is the only place a
  human at Snowflake is in the critical path.

**Key Insight:**
The scan is the only real Snowflake-side gate, it is automated, and the partner
controls when it starts. Which means the correct advice is always: start it now,
on a throwaway version, before the release window.

**Common Questions:**
- *Q: How long does the scan actually take?*
  A: Minutes on a trivial app. Do not quote a number for their app — tell them to
  run it and measure, which they can do today.
- *Q: What if it rejects us?*
  A: The rejection reason is readable on the application package. You fix and
  resubmit, or appeal via a severity 4 support ticket. CVE appeals need
  exploitability reasoning, a reachability analysis if available, and an update
  plan.
- *Q: Does every patch get rescanned?*
  A: Yes. On a package already set to EXTERNAL, each new version or patch is
  scanned immediately. Plan the release cadence around it.
- *Q: Is there continuous monitoring after publishing?*
  A: The documented monitoring window with a 30-business-day remediation period is
  written for apps published on the Marketplace. Whether it applies to a
  private-listing-only app is not stated. Do not guess.

**References:**
- https://docs.snowflake.com/en/developer-guide/native-apps/security-run-scan
- https://docs.snowflake.com/en/developer-guide/native-apps/release-channels
- https://docs.snowflake.com/en/developer-guide/native-apps/security-appeal

---

## Slide 5: The Scan Checklist

**Talking Points:**
- These six cards are the enforced requirements, not best practices. Worth reading
  before writing more code.
- The code requirements bite hardest on apps with bundled front-end assets:
  everything must be human-readable, and minified JavaScript needs a source map.
- Critical and high CVEs in dependencies must be updated where a fix exists. For a
  partner with a large npm or Python tree, this is the most likely rejection cause
  and the one that takes longest to fix. Push them to audit dependencies now.
- The disclosure requirement is broader than people expect: functionality, every
  Internet endpoint and URL, every external function, and any consumer data logged
  or stored. It also prohibits non-essential cookies outright.
- Then the two-package pattern. This is the highest-leverage recommendation in the
  deck for anyone with a near-term release date — dev on INTERNAL never triggers a
  scan, prod on EXTERNAL only receives reviewed versions.
- The manifest indentation trap: `manifest_version: 2` is required for app
  specifications, and the docs' `privileges` example puts `description` at the same
  indent level as the privilege name. YAML reads that as two keys in one map and
  Snowflake rejects it. Show the good form, then the rejected form.

**Key Insight:**
Most of this list is a development task, not a compliance task. The partner should
treat it as a backlog to burn down before flipping `DISTRIBUTION`, not as paperwork
to file afterwards.

**Common Questions:**
- *Q: Can we ship with a known high CVE?*
  A: Only via appeal, with documentation of why it is not exploitable and a plan
  for updating. Do not plan around this.
- *Q: Does manifest_version 2 have downsides?*
  A: It enables automated granting of privileges, which means consumers agree at
  install that the app may be granted the declared privileges during upgrades
  without additional consent. Some security teams will ask about that. Consumers
  can also constrain it with feature policies.

**References:**
- https://docs.snowflake.com/en/developer-guide/native-apps/security-app-requirements
- https://docs.snowflake.com/en/developer-guide/native-apps/manifest-overview
- https://docs.snowflake.com/en/developer-guide/native-apps/ui-consumer-feature-policies

---

## Slide 6: The Auth Requirement

**Talking Points:**
- Slow down here. This is the one item that can invalidate a design rather than
  add a task.
- All connections to the app, including web UIs and APIs, must authenticate through
  a Snowflake-provided method *first*. App-specific auth is only allowed after
  Snowflake auth succeeds. No public endpoints reachable without Snowflake auth.
- The failure mode is a partner porting an existing SaaS product who assumes their
  own login page fronts the app. It cannot. Their login can exist behind Snowflake
  auth, never in front.
- What is allowed: asking the consumer to create a service user purely to reach an
  external service, using a PAT, OAuth, or key pair, with minimum permissions.
- What is never allowed: the consumer typing their Snowflake username and password
  into the app, or generating a keypair and handing over the private key. If the
  partner's design does either, it needs to change now.

**Key Insight:**
Ask "does your app have a UI, and what fronts it" in the first technical
conversation. The answer determines whether the rest of the timeline is realistic.

**Common Questions:**
- *Q: We already have our own identity provider. Can we use it?*
  A: Yes, but layered after Snowflake authentication, not instead of it.
- *Q: What about our public marketing site or docs?*
  A: Out of scope — the requirement governs connections to the app itself.

**References:**
- https://docs.snowflake.com/en/developer-guide/native-apps/security-app-requirements
- https://docs.snowflake.com/en/collaboration/guidelines-reqs-for-listing-apps

---

## Slide 7: External Access and OAuth

**Talking Points:**
- Walk the four-step flow: declare the privilege in the manifest, the setup script
  creates the network rule / EAI / specification, the consumer approves the host
  ports, and only then can the app call out.
- The setup script runs in the *consumer's* account. That framing helps people
  understand why approval is per-consumer.
- The critical design point is partial approval. The app may request several
  endpoints and the consumer might allow only one. The EAI exists but is not usable
  until approved, and the app must confirm approval before making calls. An app
  that assumes all-or-nothing breaks at the first customer who approves three of
  four hosts.
- `HOST_PORTS` in the specification must match the network rule's `VALUE_LIST`. A
  mismatch is silent until a call fails.
- One specification applies to all EAIs the app creates. Split into multiple
  specifications when you want endpoint groups that can be approved independently
  — which is exactly what you want if some endpoints are optional.

**Key Insight:**
External access is a negotiation with each consumer, not a static configuration.
The app's error handling is part of the feature.

**Common Questions:**
- *Q: Can we require all endpoints be approved?*
  A: You can document them as required, but you cannot force approval. Design for
  graceful degradation.
- *Q: Do the endpoints need to be in the listing too?*
  A: Yes — the security requirements mandate disclosing every Internet endpoint
  and URL in the listing. Keep the spec list and the disclosure in sync.

**References:**
- https://docs.snowflake.com/en/developer-guide/native-apps/requesting-app-specs-eai
- https://docs.snowflake.com/en/developer-guide/native-apps/requesting-example-oauth
- https://docs.snowflake.com/en/developer-guide/native-apps/ui-consumer-app-spec
- https://docs.snowflake.com/en/developer-guide/native-apps/requesting-auto-privs

---

## Slide 8: Release Directives

**Talking Points:**
- Lead with the blocker: no release directive, no publish. Teams discover this at
  the moment they try to ship.
- The default release directive controls what every consumer installs. A custom
  directive overrides it for named accounts and always takes precedence.
- Argument order matters and is not interchangeable. For `SET RELEASE DIRECTIVE`,
  `ACCOUNTS` precedes `VERSION` and `PATCH`; the reverse fails with a syntax error.
  Some channel-oriented examples show the other order — the reference syntax page
  wins.
- The piloting pattern is worth selling: custom directive at two friendly accounts,
  default left on the previous version, promote after confirmation. That is a
  staged rollout without any extra infrastructure.
- `UPGRADE_IN_MAINTENANCE_WINDOW = TRUE` defers upgrades to the consumer's window
  and requires `UPGRADE_DEADLINE`. It cannot be combined with `UPGRADE_AFTER`.
  Enterprise customers will ask for this.

**Key Insight:**
Release directives are the partner's rollout safety mechanism, not a bookkeeping
step. A partner shipping to named customers should be using custom directives from
day one.

**Common Questions:**
- *Q: Can we hold some customers on an old version indefinitely?*
  A: Yes, with a custom release directive pinned to that version.
- *Q: What happens if we do nothing about upgrades?*
  A: Consumers move to whatever the applicable directive points at. Use
  `UPGRADE_AFTER` or the maintenance-window parameters if you need control.

**References:**
- https://docs.snowflake.com/en/sql-reference/sql/alter-application-package-release-directive
- https://docs.snowflake.com/en/developer-guide/native-apps/release-channels
- https://docs.snowflake.com/en/developer-guide/native-apps/consumer-maintenance-policies-provider

---

## Slide 9: Cross-Region and Cost

**Talking Points:**
- The reframe: "free" describes what the consumer pays. If consumers sit in other
  regions or clouds, the provider pays for Cross-Cloud Auto-Fulfillment — compute,
  storage, and egress.
- Cost is demand-driven. Private listings are auto-fulfilled after the specified
  consumers get the listing, so you are not pre-staging every region.
- The attribution surprise: costs land on a Snowflake-managed secure share area per
  region, not under normal warehouse attribution. Point them at
  `LISTING_AUTO_FULFILLMENT_USAGE_HISTORY` in `ORGANIZATION_USAGE` so the first
  bill is not a mystery.
- Recommend Egress Cost Optimization before scaling to many consumer regions.
- Then the silent-drift bug, which is the most operationally dangerous item on the
  slide: an application package does not automatically propagate new versions to
  remote regions. Without `LISTING_AUTO_REFRESH` or an explicit
  `SYSTEM$TRIGGER_LISTING_REFRESH`, remote consumers stay on an old version while
  the home region looks correct. Track with `LISTING_REFRESH_HISTORY`.
- Close on the one-way door: after publishing a private listing you cannot change
  the associated share.

**Key Insight:**
Cross-region is where a private listing acquires ongoing cost and an ongoing
operational obligation. Both belong to the provider, and both are invisible until
something is wrong.

**Common Questions:**
- *Q: How much will auto-fulfillment cost us?*
  A: It depends on database size, rate of change, refresh frequency, and which
  regions. Point at the pricing guide rather than estimating; then have them
  measure with the usage view.
- *Q: Can we avoid it entirely?*
  A: Only by having all consumers in your region and cloud, or by replicating
  manually — which is more work, not less.
- *Q: Why is our customer on an old version?*
  A: Check `LISTING_AUTO_REFRESH` first. This is the most common cause.

**References:**
- https://docs.snowflake.com/en/collaboration/provider-listings-auto-fulfillment
- https://docs.snowflake.com/en/collaboration/provider-understand-cost-auto-fulfillment
- https://docs.snowflake.com/en/collaboration/provider-listings-auto-fulfillment-eco
- https://docs.snowflake.com/en/sql-reference/functions/system_trigger_listing_refresh
- https://docs.snowflake.com/en/collaboration/provider-listings-creating-publishing

---

## Slide 10: Pre-Flight Checklist

**Talking Points:**
- Use this as the actual agenda for a working session with a partner. Walk it top
  to bottom and mark what is settled.
- The first two rows are the ones to answer before anything else. Org topology
  decides whether the scan applies at all; regions decide whether fulfillment and
  cost apply.
- Push hard on "scan run early on a throwaway version." It is the cheapest
  risk reduction available and it can be done the same day.
- Close on the net statement: no Snowflake approval to wait on, a self-service scan
  to start now, an auth model to validate before writing more code, and a
  cross-region cost decision that is theirs.
- The verification note at the bottom is deliberate. If someone asks whether the
  SQL works, the answer is that it was executed, and two snippets were corrected
  because of it. Offer that rather than hiding it.

**Key Insight:**
The partner's real risk was never Snowflake's review queue. It is their own auth
architecture and their dependency tree. Redirect the urgency there.

**Common Questions:**
- *Q: What is the fastest path to a September release?*
  A: Split into two packages today, flip the prod package to EXTERNAL on a
  throwaway version this week, and validate the Snowflake-auth-first requirement
  against your UI design before writing more front-end code.
- *Q: What do you need from us?*
  A: Consumer account identifiers in ORG.ACCOUNT form with their regions, the
  manifest, the app specification list, and confirmation of free versus paid.

**References:**
- https://docs.snowflake.com/en/developer-guide/native-apps/security-app-requirements
- https://docs.snowflake.com/en/developer-guide/native-apps/security-run-scan
- https://docs.snowflake.com/en/collaboration/provider-listings-creating-publishing
