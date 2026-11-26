---
name: bb-local-toolkit
description: "Bug bounty workflow plus local tool/wordlist paths. Covers recon, pre-hunt research, source code audit, web and API vulnerability testing (IDOR, SSRF, XSS, SQLi, OAuth), LLM security testing, bug chaining, finding validation, and reporting. For general workflow routing without local tooling, use bug-bounty. 中文触发词：漏洞赏金、安全测试、渗透测试、漏洞挖掘、信息收集、子域名枚举、XSS测试、SQL注入、SSRF、安全审计、漏洞报告"
sources: community, operator_experience
---

# Bug Bounty Master Workflow

Full pipeline: Recon -> Learn -> Hunt -> Validate -> Report. One skill for everything.

## THE ONLY QUESTION THAT MATTERS

> **"Can an attacker do this RIGHT NOW against a real user who has taken NO unusual actions -- and does it cause real harm (stolen money, leaked PII, account takeover, code execution)?"**
>
> If the answer is NO -- **STOP. Do not write. Do not explore further. Move on.**

### Theoretical Bug = Wasted Time. Kill These Immediately:

| Pattern | Kill Reason |
|---|---|
| "Could theoretically allow..." | Not exploitable = not a bug |
| "An attacker with X, Y, Z conditions could..." | Too many preconditions |
| "Wrong implementation but no practical impact" | Wrong but harmless = not a bug |
| Dead code with a bug in it | Not reachable = not a bug |
| Source maps without secrets | No impact |
| SSRF with DNS-only callback | Need data exfil or internal access |
| Open redirect alone | Need ATO or OAuth chain |
| "Could be used in a chain if..." | Build the chain first, THEN report |

**You must demonstrate actual harm. "Could" is not a bug. Prove it works or drop it.**

---

## CRITICAL RULES

1. **READ FULL SCOPE FIRST** -- verify every asset/domain is owned by the target org
2. **NO THEORETICAL BUGS** -- "Can an attacker steal funds, leak PII, takeover account, or execute code RIGHT NOW?" If no, STOP.
3. **KILL WEAK FINDINGS FAST** -- run the 7-Question Gate BEFORE writing any report
4. **Validate before writing** -- check CHANGELOG, design docs, deployment scripts FIRST
5. **One bug class at a time** -- go deep, don't spray
6. **Verify data isn't already public** -- check web UI in incognito before reporting API "leaks"
7. **5-MINUTE RULE** -- if a target shows nothing after 5 min probing (all 401/403/404), MOVE ON
8. **IMPACT-FIRST HUNTING** -- ask "what's the worst thing if auth was broken?" If nothing valuable, skip target
9. **CREDENTIAL LEAKS need exploitation proof** -- finding keys isn't enough, must PROVE what they access
10. **STOP SHALLOW RECON SPIRALS** -- don't probe 403s, don't grep for analytics keys, don't check staging domains that lead nowhere
11. **BUSINESS IMPACT over vuln class** -- severity depends on CONTEXT, not just vuln type
12. **UNDERSTAND THE TARGET DEEPLY** -- before hunting, learn the app like a real user
13. **DON'T OVER-RELY ON AUTOMATION** -- automated scans hit WAFs, trigger rate limits, find the same bugs everyone else finds
14. **HUNT LESS-SATURATED VULN CLASSES** -- XSS/SSRF/XXE have the most competition. Expand into: cache poisoning, Android/mobile vulns, business logic, race conditions, OAuth/OIDC chains, CI/CD pipeline attacks
15. **ONE-HOUR RULE** -- stuck on one target for an hour with no progress? SWITCH CONTEXT
16. **TWO-EYE APPROACH** -- combine systematic testing (checklist) with anomaly detection (watch for unexpected behavior)
17. **T-SHAPED KNOWLEDGE** -- go DEEP in one area and BROAD across everything else

> **For the full hunting methodology** — 5-phase non-linear workflow, developer psychology framework, session discipline, tool routing by phase, and Wide/Deep route selection — see **`skills/bb-methodology/SKILL.md`**.

---

## A->B BUG SIGNAL METHOD (Cluster Hunting)

**When you find bug A, systematically hunt for B and C nearby.** This is one of the most powerful methodologies in bug bounty. Single bugs pay. Chains pay 3-10x more.

### Known A->B->C Chains

| Bug A (Signal) | Hunt for Bug B | Escalate to C |
|----------------|---------------|---------------|
| IDOR (read) | PUT/DELETE on same endpoint | Full account data manipulation |
| SSRF (any) | Cloud metadata 169.254.169.254 | IAM credential exfil -> RCE |
| XSS (stored) | Check if HttpOnly is set on session cookie | Session hijack -> ATO |
| Open redirect | OAuth redirect_uri accepts your domain | Auth code theft -> ATO |
| S3 bucket listing | Enumerate JS bundles | Grep for OAuth client_secret -> OAuth chain |
| Rate limit bypass | OTP brute force | Account takeover |
| GraphQL introspection | Missing field-level auth | Mass PII exfil |
| Debug endpoint | Leaked environment variables | Cloud credential -> infrastructure access |
| CORS reflects origin | Test with credentials: include | Credentialed data theft |
| Host header injection | Password reset poisoning | ATO via reset link |

### Cluster Hunt Protocol (6 Steps)

```
1. CONFIRM A     Verify bug A is real with an HTTP request
2. MAP SIBLINGS  Find all endpoints in the same controller/module/API group
3. TEST SIBLINGS Apply the same bug pattern to every sibling
4. CHAIN         If sibling has different bug class, try combining A + B
5. QUANTIFY      "Affects N users" / "exposes $X value" / "N records"
6. REPORT        One report per chain (not per bug). Chains pay more.
```

### Real Examples

**Coinbase S3->Bundle->Secret->OAuth chain:**
```
A: S3 bucket publicly listable (Low alone)
B: JS bundles contain OAuth client credentials
C: OAuth flow missing PKCE enforcement
Result: Full auth code interception chain
```

**Vienna Chatbot chain:**
```
A: Debug parameter active in production (Info alone)
B: Chatbot renders HTML in response (dangerouslySetInnerHTML)
C: Stored XSS via bot response visible to other users
Result: P2 finding with real impact
```

---

## Where the detail lives

This skill is the router. Its long chapters live in reference files so loading it stays
cheap — open only the one you need with
`skill_view("bb-local-toolkit", "references/<file>")`.

| File | Covers |
|---|---|
| `references/01-top-1-hacker-mindset.md` | TOP 1% HACKER MINDSET (63 lines) |
| `references/02-tools.md` | TOOLS (97 lines) |
| `references/03-phase-1-recon.md` | PHASE 1: RECON (134 lines) |
| `references/04-phase-2-learn-pre-hunt-intelligence.md` | PHASE 2: LEARN (Pre-Hunt Intelligence) (41 lines) |
| `references/05-phase-3-hunt.md` | PHASE 3: HUNT (54 lines) |
| `references/06-vulnerability-hunting-checklists-1.md` | VULNERABILITY HUNTING CHECKLISTS, part 1 (629 lines) |
| `references/06-vulnerability-hunting-checklists-2.md` | VULNERABILITY HUNTING CHECKLISTS, part 2 (159 lines) |
| `references/07-phase-4-validate.md` | PHASE 4: VALIDATE (88 lines) |
| `references/08-always-rejected-never-submit-these.md` | ALWAYS REJECTED — NEVER SUBMIT THESE (24 lines) |
| `references/09-phase-5-report.md` | PHASE 5: REPORT (120 lines) |
| `references/10-resources.md` | RESOURCES (26 lines) |
| `references/11-installation-hermes-agent-skill.md` | INSTALLATION (Hermes Agent Skill) (22 lines) |
