# Using Hermes-BugHunter

An end-to-end pass through the bundle in the order the work actually happens.
Every step names the skill Hermes loads and the command you can type yourself.

## 0. Prerequisites

- Hermes Agent installed, with a model configured in the active profile.
- Written authorization for every host you will touch: a program scope, a signed
  engagement, or your own lab.
- The bundle installed (`bash scripts/install.sh`) and a fresh session started.

```text
/skills
```

You should see 98 skills grouped under `hermes-bughunter`.

## 1. Scope first

Never send traffic before the scope is settled.

```text
/scope api.example.com app.example.com
```

`scope` is deterministic and deny-wins: an asset with no matching allow rule is
out of scope, and the run stops rather than widening. Write the program's scope
into the engagement's `scope.md` once, then reuse it for every check.

Skills: `scope`, `recon-scope-triage` (when handing you an ASM dump that is full
of same-named companies).

## 2. Pick the engagement mode

```text
/hunt app.example.com
```

The dispatcher asks one question — Red Team or WAPT/bug bounty — and hands off:

- **Red team:** `redteam-mindset`, `mid-engagement-ir-detection`, `hunt-dispatch`
  in redteam mode; medium findings only ship when they chain (`/chain`).
- **Bug bounty / WAPT:** full class coverage, platform-shaped reports.

If you already know the class, skip the question:
`/hunt app.example.com --vuln-class idor`.

Skills: `hunt`, `hunt-dispatch`, `bb-methodology` (when you are unsure where you
are in the process).

## 3. Recon

```text
/recon example.com
/surface example.com
```

`recon` produces `recon/<target>/` (subdomains, live hosts, URLs, classified
parameters); `surface` ranks what to look at first from the recon manifest and
hunt memory.

Skills: `web2-recon`, `offensive-osint`, `hunt-source-leak`, `hunt-spa-api`,
`recon-scope-triage`.

## 4. Hunt

Load the classes the surface actually suggests — two or three, not all 58.

```text
/skill hunt-idor
/skill hunt-ssrf
```

Each `hunt-*` skill gives: the signal that makes the class worth testing, the
payload/detection set, the confirmation bar (OOB callback, second account,
before/after diff), and the root causes behind it. `security-arsenal` holds the
shared payload library when a skill points at it.

## 5. Prove it

A signal is not a finding. `exploit-completion` covers the mechanics of getting
to proof: follow every redirect, diff the response against an expected outcome,
and change approach after repeated identical failures.

## 6. Validate

```text
/triage      # quick go/no-go
/validate    # full 7-Question Gate + 4 gates
```

One wrong answer kills the finding. This is the step that protects your validity
ratio — `triage-validation` holds the gate, the always-rejected list, and the
chain-only table.

## 7. Capture evidence

Skills: `evidence-hygiene`. Redact session cookies, bearer tokens, and other
users' PII before the screenshot — not after the report is written.

## 8. Report

```text
/report
```

Produces a platform-shaped body (HackerOne, Bugcrowd, Intigriti, Immunefi) with
CVSS 3.1, reproduction steps, impact, and remediation. `report-writing` owns the
templates and tone; `bugcrowd-reporting` adds VRT/severity-override tactics when
the platform is Bugcrowd.

## 9. Persist what you learned

```text
/remember          # note on the target or the last confirmed finding
/pickup example.com
```

`autopilot` runs the whole loop with checkpoints; `memory-gc` rotates the ledger
files when they grow.

## Red-team variant

Same skeleton, different deliverable:

1. `/skill redteam-mindset` before anything else.
2. `mid-engagement-ir-detection` while testing — the client patching a finding
   mid-engagement is itself a deliverable observation.
3. `redteam-report-template` for the client-facing format (Subject /
   Observations / Description / Impact / Recommendation / PoC), not the platform
   template.

## What "done" looks like

- Every claimed finding reproduces from a clean session with the steps in the
  report.
- Impact is demonstrated, not asserted ("could potentially" is banned by
  `report-writing`).
- Evidence is redacted and minimal.
- Out-of-scope hosts were never touched, and the scope check is in the notes.
