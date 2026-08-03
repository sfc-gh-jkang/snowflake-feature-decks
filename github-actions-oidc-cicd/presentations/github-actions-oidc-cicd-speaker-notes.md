# Speaker Notes: Secretless CI/CD — Deploying to Snowflake from GitHub Actions

## Presentation Context

For SEs and platform engineers helping customers automate Snowflake deploys, and
for anyone who has a pipeline authenticating with a stored private key. After this
session someone should be able to stand up an OIDC pipeline and know why the first
attempt fails.

Fifteen slides in four arcs. Concepts (1–4) is the case for secretless and the
token exchange. Setup (5–8) is the service user, the subject, the workflow, and
pinning. Operating (9–12) is the network policy wall, named connections, what you
can deploy, and the fallback. Limits (13–15) is gotchas, other providers, and the
wrap.

**Support status:** everything on the setup slides is from the product docs. The
recommended action is `snowflakedb/snowflake-actions@v3` with `use-oidc: true`,
requiring Snowflake CLI 3.11 or later. Two links go to the action repo and a
Snowflake developer guide rather than the product docs, and are labeled purple.
Slide 9's operational advice draws on field experience and is marked inline.

The single most useful thing you can tell an audience: the auth is a dozen lines,
and the network policy is what actually blocks the first run. Lead people there
before they burn an afternoon on subject strings.

---

## Slide 1: Hero / Overview

**Talking Points:**
- Frame it: OIDC replaces a stored private key with a token GitHub mints per run.
- Point at the fourth stat card — `250001` — and say plainly that this is the error
  most people hit first, and it is not an auth problem.
- Set the arc: concepts, setup, operating, limits.

**Key Insight:**
Secretless auth removes an entire maintenance category — there is no key to rotate
and nothing to leak. The cost is one-time configuration, most of which is network
policy rather than authentication.

**Common Questions:**
- *Q: Is key pair deprecated?*
  A: No. Fully supported, and still the right answer in some environments (slide 12).

**References:**
- https://docs.snowflake.com/en/developer-guide/snowflake-cli/cicd/github-action
- https://docs.snowflake.com/en/user-guide/workload-identity-federation

---

## Slide 2: Why Secretless

**Talking Points:**
- Four compounding problems with a stored key: manual rotation, permanent blast
  radius, coarse scope, weaker audit trail.
- The scope point is the strongest: a key authenticates whoever holds it, while an
  OIDC subject binds trust to a repository *and* a ref.
- The audit point lands well with security teams — subject-bound auth tells you
  which repo and branch deployed, not just that a user connected.

**Key Insight:**
You trade a secret you control for a trust relationship you configure once. Setup
is slightly harder; ongoing maintenance approaches zero.

**Common Questions:**
- *Q: We rotate keys quarterly already.*
  A: Then you have the process cost without the scope benefit. OIDC gives per-run
  expiry and repo/ref binding for free.

**References:**
- https://docs.snowflake.com/en/user-guide/workload-identity-federation

---

## Slide 3: How the Exchange Works

**Talking Points:**
- Walk the five steps. Emphasise that nothing is stored anywhere.
- Show the four exported environment variables — useful for debugging, because if a
  later step fails you can check whether these are actually set.
- The context box matters for adoption: the action installs Python 3.11 and `uv`
  and puts the CLI in an isolated environment. There is no Python version for the
  team to manage, which removes a common objection.

**Key Insight:**
Snowflake validates the GitHub-signed token directly. There is no broker, no
secret store, and no shared credential in the middle.

**Common Questions:**
- *Q: How long is the token valid?*
  A: Short-lived and per-run. That is the point — a leaked token is useless quickly.
- *Q: Does it install its own Python?*
  A: Yes, in an isolated environment. It does not disturb the runner's Python.

**References:**
- https://docs.snowflake.com/en/developer-guide/snowflake-cli/cicd/github-action

---

## Slide 4: Three Ways to Authenticate

**Talking Points:**
- Walk the table. OIDC is recommended; key pair is supported; password is legacy.
- Call out the honest caveat in the first card: even with OIDC you still store
  `SNOWFLAKE_ACCOUNT` as a secret. It is an identifier, not a credential — it
  cannot authenticate anything by itself. Saying this preempts a sceptical question.
- The second card matters — do not oversell OIDC. There are real cases where key
  pair is correct.

**Key Insight:**
"Secretless" means no long-lived *credential*, not zero configuration values. Be
precise about that distinction or someone will call it out.

**Common Questions:**
- *Q: Minimum CLI version?*
  A: 3.11 for OIDC. Key pair and password work on any version.

**References:**
- https://docs.snowflake.com/en/developer-guide/snowflake-cli/cicd/github-action

---

## Slide 5: The Service User

**Talking Points:**
- `TYPE = SERVICE` means no password and no interactive login. That is a security
  property worth naming.
- The issuer string is identical for every GitHub repository. Only the subject varies.
- Least privilege matters more here than usual, because the pipeline runs unattended
  and its role is what an attacker would inherit if a subject were ever spoofed.
- Flag the one-user-one-subject constraint now; slide 6 develops it.

**Key Insight:**
Think per-pipeline, not per-team. A user bound to `main` in one repo cannot be
replayed from anywhere else, and that narrowness is most of the value.

**Common Questions:**
- *Q: Can one user cover several repos?*
  A: Not with a plain subject. You would need a broader custom claim on the GitHub
  side.

**References:**
- https://docs.snowflake.com/en/user-guide/workload-identity-federation
- https://docs.snowflake.com/en/developer-guide/snowflake-cli/cicd/github-action

---

## Slide 6: Choosing a Subject

**Talking Points:**
- Three documented formats: branch ref, pull request, named environment.
- Then the rule that overrides them, and this is the slide's whole point: **when a
  job sets `environment:`, GitHub emits the environment subject form regardless of
  the trigger.**
- Give the concrete failure: a working pipeline breaks the day someone adds
  `environment: production` for approval gating, because the emitted subject changed
  and the service user was never updated.
- Broader claims like `repository_owner` are configured on the GitHub side.

**Key Insight:**
The subject is a contract between two systems, and only one of them is in your
Snowflake DDL. Any workflow change that alters the claim needs a matching change to
the user.

**Common Questions:**
- *Q: How do I see the actual claim?*
  A: The GitHub OIDC reference documents the token claims; inspect them when
  debugging a mismatch.
- *Q: Failure mode?*
  A: Fails closed — safe, but opaque. Test on a throwaway branch.

**References:**
- https://docs.snowflake.com/en/developer-guide/snowflake-cli/cicd/github-action
- https://docs.github.com/en/actions/reference/security/oidc

---

## Slide 7: The Workflow

**Talking Points:**
- Two lines make it work: `id-token: write` and `use-oidc: true`. Missing the
  permission is the most common first failure after the network policy.
- `id-token: write` is a *job permission*, not an action input. People look for it
  in the wrong place.
- `persist-credentials: false` on checkout is free hygiene.
- `-x` on `snow` commands makes failures fail the job. Without it a broken deploy
  can pass green, which is worse than failing.

**Key Insight:**
The workflow is unremarkable, which is the goal. All the Snowflake-specific
complexity lives in the service user and the network policy.

**Common Questions:**
- *Q: Why did it work locally but not in CI?*
  A: Check `id-token: write` first, then the network policy, then the subject.

**References:**
- https://docs.snowflake.com/en/developer-guide/snowflake-cli/cicd/github-action

---

## Slide 8: Version Pinning

**Talking Points:**
- Two independent things to pin: the action and the CLI it installs. People
  routinely pin one and forget the other.
- Commit SHA is the supply-chain-safe option for the action.
- Omitting `cli-version` installs latest, meaning the pipeline can change without a
  commit — a genuine reproducibility problem.
- `cli-version` and `custom-github-ref` are mutually exclusive; setting both errors.

**Key Insight:**
An unpinned pipeline is not reproducible. If a deploy worked last week and fails
today with no commits, unpinned versions are the first suspect.

**Common Questions:**
- *Q: `@v3` or a SHA?*
  A: SHA for production. `@v3` is convenient and moves under you.

**References:**
- https://docs.snowflake.com/en/developer-guide/snowflake-cli/cicd/github-action

---

## Slide 9: The Network Policy Wall

**Talking Points:**
- Spend real time here. This is the slide that saves someone a day.
- Symptom: OIDC succeeds, then `250001` — IP not allowed. GitHub-hosted runners
  have ephemeral IPs from very large ranges, so any network-policy'd account blocks
  them by default.
- Emphasise it is **not** an auth problem. People respond by rewriting subject
  strings, which cannot help.
- Fix: a **user-level** network policy on the service user, using the Snowflake
  managed rule for GitHub Actions ranges. User-level overrides the account policy
  for that user only, so humans stay restricted.
- The managed rule matters because Snowflake maintains the CIDR list as GitHub
  changes it. Hand-maintaining thousands of CIDRs is not viable.
- The field note is marked as such: where the account policy is org-managed and
  cannot be overridden per user, this path is closed — use a self-hosted runner on
  an allowlisted IP.

**Key Insight:**
Authentication and network authorisation are separate gates. Passing the first
tells you nothing about the second, and the error message does not make that
obvious.

**Common Questions:**
- *Q: Can I just allow all IPs?*
  A: Technically, but that defeats the network policy. The managed rule is scoped
  and maintained.
- *Q: What if I cannot change the account policy?*
  A: Self-hosted runner on an allowlisted IP, with key pair auth.

**References:**
- https://docs.snowflake.com/en/user-guide/network-policies

---

## Slide 10: Named Connections

**Talking Points:**
- Some commands want a named connection rather than environment variables. That
  changes where the token must land.
- The naming rule is exact: `SNOWFLAKE_CONNECTIONS_<NAME>_TOKEN`, uppercased
  connection name. Get it wrong and the token is exported somewhere the CLI does
  not look.
- The committed `config.toml` holds an empty connection block — a name and nothing
  else. No secret is committed.
- Platform note for security review: `0600` on Linux/macOS, permissions untouched
  on Windows.

**Key Insight:**
The default `SNOWFLAKE_TOKEN` only serves the default temporary connection. The
moment you use `-c <name>`, you must redirect the token with `oidc-token-name`.

**Common Questions:**
- *Q: Why use a named connection at all?*
  A: Some commands require one. If environment variables work for your commands,
  keep it simple.

**References:**
- https://docs.snowflake.com/en/developer-guide/snowflake-cli/connecting/configure-connections
- https://docs.snowflake.com/en/developer-guide/snowflake-cli/cicd/github-action

---

## Slide 11: What You Can Deploy

**Talking Points:**
- Once `snow` is authenticated the pipeline is ordinary CLI usage: DCM, dbt,
  Streamlit, Native Apps, plain SQL.
- The highlight box is the design recommendation: PR-scoped user against dev,
  main-scoped user against prod. Two subjects, two users, one workflow file.
- Land the reframe — one-subject-per-user stops being an annoyance and becomes the
  safety property that keeps a PR from deploying to production.

**Key Insight:**
The constraint that looks like a limitation is what gives you environment
separation without extra machinery.

**Common Questions:**
- *Q: One workflow or two?*
  A: One file with two jobs is fine, as long as each job's trigger matches the
  subject of the user it authenticates as.

**References:**
- https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects-on-snowflake-ci-cd
- https://docs.snowflake.com/en/developer-guide/builders/devops-with-snowflake

---

## Slide 12: When You Cannot Use OIDC

**Talking Points:**
- Be even-handed. Key pair is fully supported and sometimes correct.
- The three legitimate reasons: org-managed account network policy, self-hosted
  runner already allowlisted, provider without OIDC trust configured.
- Password is legacy — supported for existing workflows, explicitly not recommended
  for production.
- Mention the one-line migration from `snowflake-cli-action@v2` to
  `snowflake-actions@v3`, inputs identical. Useful for anyone with existing pipelines.

**Key Insight:**
Recommend OIDC, but do not treat key pair as a mistake. Constraints in the customer's
environment often decide this, not preference.

**Common Questions:**
- *Q: Do we have to migrate off v2?*
  A: The old path keeps working. New workflows should use v3.

**References:**
- https://docs.snowflake.com/en/developer-guide/snowflake-cli/cicd/github-action
- https://github.com/snowflakedb/snowflake-actions

---

## Slide 13: Limits and Gotchas

**Talking Points:**
- Six items. The two that change architecture decisions:
- `snow auth oidc` is documented as currently limited to GitHub Actions as the
  provider — so do not promise OIDC parity on GitLab or Azure DevOps without
  checking.
- No reusable bearer token. If something in the pipeline needs a static
  `Snowflake Token="..."` header, that still needs a PAT — scope it to those steps
  only rather than abandoning OIDC for the whole workflow.
- Repeat the `environment:` override; it is worth hearing twice.

**Key Insight:**
OIDC covers CLI authentication well. It is not a general-purpose credential for
arbitrary HTTP calls, and conflating the two leads to a wrong design.

**Common Questions:**
- *Q: Can I get a token for my own API calls?*
  A: Not a reusable static bearer. Use a PAT for that, narrowly scoped.

**References:**
- https://docs.snowflake.com/en/developer-guide/snowflake-cli/command-reference/auth-commands/overview
- https://docs.snowflake.com/en/developer-guide/snowflake-cli/cicd/github-action

---

## Slide 14: Beyond GitHub

**Talking Points:**
- Snowflake ships first-party integrations for GitLab and Azure DevOps as well.
- The split in the two cards is the useful takeaway: the Snowflake side is portable
  (service user, least-privilege role, network policy), the trust configuration and
  claim format are provider-specific.
- Do not assume OIDC parity — the CLI's OIDC commands are documented as GitHub-only
  for now.

**Key Insight:**
Most of the work transfers between providers. The part that does not is exactly the
part people assume will.

**Common Questions:**
- *Q: Which is most mature?*
  A: GitHub Actions today, and the only one with documented OIDC support.

**References:**
- https://docs.snowflake.com/en/developer-guide/snowflake-cli/cicd/integrate-ci-cd
- https://docs.snowflake.com/en/developer-guide/snowflake-cli/cicd/gitlab-component

---

## Slide 15: Takeaways

**Talking Points:**
- Four-step strip is the setup order, and the order matters: service user, network
  policy, workflow permissions, then test on a throwaway branch.
- If one thing lands, make it the network policy. It is the difference between a
  30-minute setup and a lost afternoon.
- Close on pinning — an unpinned pipeline is not reproducible.

**Key Insight:**
The interesting engineering is not the authentication. It is realising that
authentication and network authorisation are separate gates, and that the subject is
a contract with a system outside your DDL.

**Common Questions:**
- *Q: Where do I start?*
  A: Throwaway repo, throwaway branch, one service user, `snow connection test -x`.
  Get that green before wiring a real deploy.

**References:**
- https://docs.snowflake.com/en/developer-guide/snowflake-cli/cicd/github-action
- https://docs.snowflake.com/en/user-guide/workload-identity-federation
- https://www.snowflake.com/en/developers/guides/configure-cicd-integrations-with-snowflake
