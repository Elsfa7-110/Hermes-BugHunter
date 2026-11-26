---
name: web3-audit
description: "Solidity DeFi audit: 10 bug classes, Foundry PoC. Use for any Solidity/Rust contract audit or when deciding whether a DeFi target is worth hunting."
sources: public_research, community
---

# WEB3 SMART CONTRACT AUDIT

10 bug classes. Pre-dive kill signals. Foundry PoC template. Real paid examples.

---

## PRE-DIVE KILL SIGNALS (check BEFORE any code review)

> ZKsync lesson: $322M TVL + OZ audit + 750K LOC + 5 sessions = 0 findings. Large well-audited bridges are extremely hard.

1. **TVL < $500K** → max payout capped too low for effort
2. **2+ top-tier audits** (Halborn, ToB, Cyfrin, OpenZeppelin) on simple protocol → bugs already found
3. **Protocol < 500 lines, single A→B→C flow** → minimal attack surface
4. **Formula**: `max_realistic_payout = min(10% × TVL, program_cap)` — if < $10K, skip

**Soft kill:** OZ/ToB/Cyfrin audit on current version + codebase > 500K LOC → expect 40+ hours for maybe 1 finding. Only proceed if bounty floor > $50K AND you have protocol-specific expertise.

**Target scoring (go if >= 6/10):**
- TVL > $10M: +2
- Immunefi program with Critical >= $50K: +2
- No top-tier audit on current version: +2
- < 30 days since deploy: +1
- Protocol you've hunted before: +1
- Source code + natspec comments: +1
- Upgradeable proxies: +1

---

## THE ONE RULE

> "Read ALL sibling functions. If `vote()` has a modifier, check `poke()`, `reset()`, `harvest()`. The missing modifier on the sibling IS the bug."

This single rule explains 19% of all Critical findings.

---

## FOUNDRY POC TEMPLATE

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "../src/VulnerableContract.sol";

contract ExploitTest is Test {
    VulnerableContract target;
    address attacker = makeAddr("attacker");
    address victim = makeAddr("victim");

    function setUp() public {
        // Fork mainnet at specific block
        vm.createSelectFork("mainnet", BLOCK_NUMBER);

        // Deploy or load target
        target = VulnerableContract(TARGET_ADDRESS);

        // Fund accounts
        deal(address(token), attacker, INITIAL_BALANCE);
        deal(address(token), victim, VICTIM_BALANCE);
    }

    function test_exploit() public {
        console.log("Attacker balance before:", token.balanceOf(attacker));

        vm.startPrank(attacker);

        // Step 1: Setup conditions
        // Step 2: Execute exploit
        // Step 3: Verify impact

        vm.stopPrank();

        console.log("Attacker balance after:", token.balanceOf(attacker));
        assertGt(token.balanceOf(attacker), INITIAL_BALANCE, "Exploit failed");
    }
}
```

### Key Foundry Cheatcodes
```solidity
vm.prank(address)           // next call from address
vm.startPrank(address)      // all calls from address until stopPrank()
vm.deal(address, amount)    // set ETH balance
deal(token, address, amount) // set ERC20 balance
vm.warp(timestamp)          // set block.timestamp
vm.roll(blockNumber)        // set block.number
vm.createSelectFork("mainnet", blockNumber)  // fork mainnet
vm.expectRevert(bytes)      // next call should revert
vm.label(address, "name")   // label for trace output
vm.assume(condition)        // fuzz: discard inputs where false
```

### Running Tests
```bash
# Run specific test
forge test --match-test test_exploit -vvvv

# Run with fork
forge test --match-test test_exploit -vvvv --fork-url $MAINNET_RPC

# Gas report
forge test --gas-report

# Coverage
forge coverage --report summary
```

---

## Related Skills & Chains

- **`meme-coin-audit`** — When the target is a meme coin / SPL token rather than a DeFi protocol. Workflow primitive: pre-dive kill signals diverge — this skill's "TVL < $500K skip" doesn't apply to meme coins where the rug check (mint authority, freeze authority, LP lock) is the entire audit; route to `meme-coin-audit` instead.
- **`triage-validation`** — When a contract finding is ready to be filed on Immunefi. Workflow primitive: Immunefi has its own report format, but the impact-validated, chain-end-to-end discipline of `triage-validation` still applies; run the 7Q gate against the Foundry PoC before submitting.
- **`report-writing`** — When writing the Immunefi report body. Workflow primitive: `report-writing`'s Immunefi template (with Foundry PoC, root cause code snippet, quantified economic impact) is the body skeleton this skill's findings feed into.
- **`offensive-osint`** — When auditing a protocol's off-chain attack surface (frontend, admin API, RPC gateways). Workflow primitive: on-chain audit is this skill's job; any web2 component of the protocol (web-frontend, admin panel, indexer API) routes to `offensive-osint` for recon.
- **`bb-methodology`** — When deciding whether to dive at all. Workflow primitive: PART 0 of `bb-methodology` confirms engagement (web3 bug bounty / private audit / smart-contract review); this skill's pre-dive kill signals replace the standard scoring rubric for that engagement type.

---

## Hermes workflow shortcut: /web3-audit

# /web3-audit

Smart contract security audit using the 10-bug-class methodology.

## Usage

```
/web3-audit VulnerableContract.sol
/web3-audit https://github.com/protocol/contracts
/web3-audit [paste contract code]
```

## Step 0: Pre-Dive Kill Signals

ALWAYS check these BEFORE reading any code:

```
1. TVL < $500K → max payout too low for effort → SKIP
2. 2+ top-tier audits (Halborn, ToB, Cyfrin, OZ) on simple protocol → SKIP
3. Protocol < 500 lines, single A→B→C flow → minimal attack surface → SKIP
4. max_payout = min(10% × TVL, program_cap) → if < $10K → SKIP

Formula: Is [TVL * 10%] > [hours I'll spend * hourly rate]? If not, skip.
```

Only proceed if score >= 6/10:
- TVL > $10M: +2
- Immunefi Critical >= $50K: +2
- No top-tier audit on current version: +2
- < 30 days since deploy: +1
- Protocol you've hunted before: +1
- Upgradeable proxies present: +1

## Step 1: Accounting State Desynchronization (28% of Criticals)

```bash
# Find accounting variables
grep -rn "totalSupply\|totalShares\|totalAssets\|totalDebt\|cumulativeReward" contracts/

# Find ALL early returns in critical functions
grep -rn "\breturn\b" contracts/ -B3 | grep -B3 "if\b"
```

Check: For each early return in claim/redeem/withdraw functions:
- Which state variables are updated in the normal path?
- Are ALL of them also updated in the early return path?
- If A updated but B isn't → potential desync bug

## Step 2: Access Control (19% of Criticals)

```bash
# Sibling function families — do ALL have same modifier set?
grep -rn "function vote\|function poke\|function reset\|function update\|function claim\|function harvest" contracts/ -A2

# Ownership check: existence vs ownership
grep -rn "_requireOwned\|ownerOf\|_isApprovedOrOwner" contracts/ -B5

# Silent modifiers (if without revert)
grep -rn "modifier\b" contracts/ -A8 | grep -B3 "if (" | grep -v "require\|revert"

# Uninitialized proxy
grep -rn "function initialize\b" contracts/ -A3
grep -rn "_disableInitializers()" contracts/
```

Check: Does EVERY sibling function in a family have the SAME modifiers?

## Step 3: Incomplete Code Path (17% of Criticals)

The function family comparison test:
```
1. List all state changes in function A (deposit/place/create)
2. List all state changes in function B (withdraw/update/cancel)
3. For each state change in A: does B have the corresponding reverse?
4. For each token transfer in A: does B have the corresponding refund?
```

```bash
grep -rn "safeApprove\b" contracts/    # safeApprove without zero-reset?
grep -rn "delete\b" contracts/ -B5     # delete before operation completes?
grep -rn "function deposit\|function mint\|function withdraw\|function redeem" contracts/ -A10
```

## Step 4: Off-By-One (22% of Highs)

Mental test: For EVERY `if (A > B)`: "What happens when A == B?" Is that correct?

```bash
# Boundary comparisons
grep -rn "Period\|Epoch\|Deadline\|period\|epoch\|deadline" contracts/ -A3 | grep "[<>][^=]"

# Loop breaks
grep -rn "\bbreak\b" contracts/ -B10

# Array bounds
grep -rn "\.length\s*-\s*1\|i\s*<=\s*.*\.length\b" contracts/
```

## Step 5: Oracle / Price Manipulation

```bash
# Missing staleness check
grep -rn "latestRoundData" contracts/ -A5 | grep -v "updatedAt\|timestamp"

# Pyth confidence interval
grep -rn "getPriceUnsafe\|getPrice\b" contracts/ -A8 | grep -v "conf\|confidence"

# TWAP windows
grep -rn "secondsAgo\|TWAP\|cardinality" contracts/ -A5
```

Check:
- Is staleness checked? (`require(block.timestamp - updatedAt <= MAX_AGE)`)
- Is Pyth confidence interval checked? (`require(conf * 10 <= price)`)
- Is TWAP window > 1800 seconds (30 min)?

## Step 6: ERC4626 Vaults

```bash
grep -rn "function deposit\|function mint\|function withdraw\|function redeem" contracts/ -A10
grep -rn "function transfer\|function transferFrom" contracts/ -A15
```

Check:
- Does `mint()` call the same validation as `deposit()`?
- Does `transfer()` move lock records along with shares?
- Is there a `_decimalsOffset()` virtual shares defense against first-depositor attack?

## Step 7: Reentrancy

```bash
# Effects after interactions
grep -rn "\.call{value\|safeTransfer\|transfer(" contracts/ -B10 | grep -v "require\|revert"

# Missing nonReentrant
grep -rn "function withdraw\|function redeem\|function claim" contracts/ -A2 | grep -v "nonReentrant"
```

Check: Does every function that transfers ETH or ERC20 follow CEI order?
(Checks → Effects → Interactions)

## Step 8: Flash Loan Oracle Manipulation

```bash
grep -rn "getReserves\|getAmountsOut\|slot0\b" contracts/ -A5
```

Check: Any spot price reading from Uniswap reserves/slot0? → flash loan manipulatable.

## Step 9: Signature Replay

```bash
grep -rn "ecrecover\|ECDSA\.recover" contracts/ -B20
grep -rn "nonce\|_nonces\|nonces\[" contracts/
```

Check: Does signed hash include: nonce + chainId + contract address?

## Step 10: Proxy / Upgrade

```bash
grep -rn "function initialize\b\|_disableInitializers\|initializer" contracts/
grep -rn "delegatecall\b" contracts/ -B3
grep -rn "0x360894\|_IMPLEMENTATION_SLOT\|EIP1967" contracts/
```

Check:
- `_disableInitializers()` in implementation constructor?
- Implementation can't be initialized directly by attacker?
- Storage layout compatible between versions?

## Confirming a Finding

Apply the 7-Question Gate:
```
1. Can I demonstrate this with a Foundry test?
2. What is the financial impact (quantify in $)?
3. Is this in the Immunefi scope?
4. Is it a known issue or acknowledged behavior?
5. Does my Foundry PoC actually run? (forge test -vvvv)
```

## Foundry PoC Template

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
import "forge-std/Test.sol";
import "../src/VulnerableContract.sol";

contract ExploitTest is Test {
    VulnerableContract target;
    address attacker = makeAddr("attacker");

    function setUp() public {
        vm.createSelectFork("mainnet", BLOCK_NUMBER);
        target = VulnerableContract(TARGET_ADDRESS);
        deal(address(token), attacker, INITIAL_BALANCE);
    }

    function test_exploit() public {
        uint256 before = token.balanceOf(attacker);
        vm.startPrank(attacker);
        // Execute exploit
        vm.stopPrank();
        assertGt(token.balanceOf(attacker), before, "Exploit failed");
    }
}
```

Run: `forge test --match-test test_exploit -vvvv`

## Where the detail lives

Each bug class has a checklist file (grep patterns, review questions, paid examples);
the runbook below walks them in order. Open a file with
`skill_view("web3-audit", "references/<file>")`.

| File | Covers |
|---|---|
| `references/bug-classes-1.md` | 1. ACCOUNTING STATE DESYNCHRONIZATION … 5. ORACLE / PRICE MANIPULATION (274 lines) |
| `references/bug-classes-2.md` | 6. ERC4626 VAULT ATTACKS … Operator Notes (DeepSeek-BugHunter) (210 lines) |
