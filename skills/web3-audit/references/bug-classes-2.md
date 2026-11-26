## 6. ERC4626 VAULT ATTACKS

### Exchange Rate Manipulation (near-empty vault)
```solidity
// VULNERABLE — first depositor attack:
// 1. Attacker deposits 1 wei → gets 1 share
// 2. Attacker donates large amount directly (transfer, not deposit)
// 3. Exchange rate: 1 share = (1 + donation) assets
// 4. Victim deposits → rounds down to 0 shares → free donation to attacker

// CORRECT: virtual shares (OpenZeppelin v4.9+)
function _decimalsOffset() internal view virtual override returns (uint8) {
    return 9;  // add 1e9 virtual shares + assets to prevent manipulation
}
```

### ERC4626 Transfer (moves shares but not stake/lock records)
```solidity
// VULNERABLE: shares transferred, but lock records stay with original owner
// → shares stuck, can't redeem → permanent freeze (Belong pattern)
function transfer(address to, uint256 amount) external override {
    _transfer(msg.sender, to, amount);  // moves shares
    // MISSING: transfer lock record from msg.sender to `to`
}
```

### Grep Patterns
```bash
grep -rn "function transfer\|function transferFrom" contracts/ -A15
grep -rn "function deposit\|function mint\|function withdraw\|function redeem" contracts/ -A10
```

---

## 7. REENTRANCY
> 2016–present. CEI pattern prevents it. Still found in DeFi.

### Variants
- **Single-function**: attacker re-enters same function before state updated
- **Cross-function**: re-enters a sibling function with stale state
- **Cross-contract**: re-enters via a callback to another protocol
- **Read-only**: re-enters a view function that returns stale data used by attacker

### Root Cause Pattern
```solidity
// VULNERABLE (effects after interaction):
function withdraw(uint256 amount) external {
    require(balances[msg.sender] >= amount);
    (bool success,) = msg.sender.call{value: amount}("");  // INTERACTION first
    require(success);
    balances[msg.sender] -= amount;  // EFFECT after → reentrancy window
}

// CORRECT (CEI — Checks, Effects, Interactions):
function withdraw(uint256 amount) external {
    require(balances[msg.sender] >= amount);  // CHECK
    balances[msg.sender] -= amount;            // EFFECT
    (bool success,) = msg.sender.call{value: amount}("");  // INTERACTION last
    require(success);
}
```

### Grep Patterns
```bash
# External calls before state updates
grep -rn "\.call{value\|safeTransfer\|transfer(" contracts/ -B10 | grep -v "require\|revert"

# Missing nonReentrant modifier on critical functions
grep -rn "function withdraw\|function redeem\|function claim" contracts/ -A2 | grep -v "nonReentrant"

# Storage slot for reentrancy guard
grep -rn "nonReentrant\|ReentrancyGuard\|_notEntered" contracts/
```

---

## 8. FLASH LOAN ATTACKS

### Oracle Manipulation via Flash Loan
```solidity
// Attack flow:
// 1. Borrow $100M from Aave flash loan
// 2. Dump token in Uniswap pool → crash spot price
// 3. Protocol reads Uniswap spot → undercollateralized loans accepted
// 4. Borrow max against cheap collateral
// 5. Repay flash loan, keep profits
```

### Price Oracle Sanity Checks (what to look for)
```bash
grep -rn "getReserves\|getAmountsOut\|slot0\b" contracts/ -A5
# spot price from reserves = manipulatable with flash loan
# slot0 = Uniswap V3 spot price = manipulatable
```

---

## 9. SIGNATURE REPLAY

### Missing Nonce
```solidity
// VULNERABLE:
function permit(address owner, address spender, uint256 value,
                uint256 deadline, uint8 v, bytes32 r, bytes32 s) external {
    bytes32 hash = keccak256(abi.encodePacked(owner, spender, value, deadline));
    // MISSING: nonce not included → same signature usable multiple times
    require(ecrecover(hash, v, r, s) == owner);
}
```

### Missing Chain ID
```solidity
// VULNERABLE: signature valid on mainnet AND testnet AND all forks
bytes32 hash = keccak256(abi.encodePacked(params));
// MISSING: block.chainid not in hash → works on any chain
```

### Grep Patterns
```bash
grep -rn "ecrecover\|ECDSA\.recover" contracts/ -B20
# Check: does the signed hash include nonce + chainId + contract address?

grep -rn "nonce\|_nonces\|nonces\[" contracts/
```

---

## 10. PROXY / UPGRADE ISSUES

### Storage Collision
```solidity
// Implementation and proxy share storage layout
// Proxy slot 0: _owner
// Implementation slot 0: _initialized
// → writing to _initialized overwrites _owner
```

### Uninitialized Implementation
```solidity
// If implementation can be initialized directly → anyone becomes owner of implementation
// Attack: call initialize() on implementation contract → call upgradeTo() → replace logic
```

### delegatecall to User-Controlled Address
```solidity
function execute(address target, bytes calldata data) external onlyOwner {
    target.delegatecall(data);  // target is validated, but what if owner is compromised?
}
```

### Grep Patterns
```bash
# UUPS initialization protection
grep -rn "function initialize\b\|_disableInitializers\|initializer" contracts/

# Delegate call
grep -rn "delegatecall\b" contracts/ -B3 -A5

# Storage layout — proxy uses EIP-1967 slots?
grep -rn "0x360894\|EIP1967\|_IMPLEMENTATION_SLOT" contracts/
```

---

## Operator Notes (DeepSeek-BugHunter)

> Engagement-derived + 2026-specific additions to the vendored foundation.
> Wisdom from real authorized engagements + Phase 2 verification across
> this repo's 31+ skill-area live tests. The upstream content covers the WHAT;
> this layer covers the WHEN-IT-WORKS-vs-WHEN-IT-DOESN'T.

### Bug classes still paying in 2026

Flash-loan attacks remain top-paid on Immunefi (top 5 in 2024-2026 by bounty). The economic primitive — borrow $50M, manipulate price oracle, drain pool, repay — keeps reappearing because new protocols keep shipping with composability assumptions that don't hold under flash-loaned imbalance.

Reentrancy IS still paying because new protocols keep shipping with ERC-777 / hooks / callbacks. Don't assume the class is dead — the 2023-2025 paid corpus contains 40+ reentrancy bugs against post-Checks-Effects-Interactions codebases (cross-function reentrancy, read-only reentrancy via view functions called during state-mid-flight).

Oracle manipulation: still paid heavily but harder. Most projects use Chainlink price feeds now; the attack target is the SECONDARY oracle most projects also use (TWAP from a low-liquidity Uniswap V2 pair, the protocol's own internal oracle, a stale fallback path). Audit the failover chain, not just the primary feed.

### What's new since the vendored content was written

- **EIP-1153 (transient storage)** — introduced in 2024. New reentrancy classes: transient-storage reads cached across the same transaction can desync from persistent storage. Audit any `tload`/`tstore` usage for read-after-external-call.
- **EIP-7702 (Pectra hard fork 2025)** — added EOA-to-smart-account upgrades. New ATO-like primitives via re-delegation: an EOA signed-once can delegate to a contract that the attacker controls, then signature replay across delegations.
- **Account abstraction (ERC-4337 bundlers)** — paymaster sponsorship abuse and bundler griefing. Paymaster contracts that don't enforce strict sender allowlists drain on first call.
- **ZK-rollup bridge bugs** — proof-replay across rollups, off-chain prover compromise, sequencer censorship leading to forced-inclusion edge cases.
- **LST/LRT depeg dynamics** — liquid-staking and liquid-restaking tokens that assume 1:1 peg under loss conditions; oracle assumes peg, market reflects depeg, liquidation logic breaks.

### Tool stack for 2026

Foundry remains the test framework. `forge test --gas-report --debug` for invariant testing; `forge fuzz` for property-based testing; `forge inspect` for storage-layout audits. Slither + Echidna for static + fuzz. Mythril for symbolic execution on smaller contracts. tenderly.co for forking + simulation (best UX for replicating attacks against mainnet state).

For Solana: anchor framework, sealevel-attacks corpus (curated PoCs by anchor maintainers), soteria-sec / sec3 scanner. For Move (Aptos, Sui): move-prover, aptos-cli `aptos move test`.

For cross-chain: hyperlane and LayerZero each have audit-tooling repos; bridge bugs require simulating both endpoints, not just one.

### Where pre-dive kill signals matter

TVL under $500K isn't worth the audit time unless the bounty floor is high. Audit firm already covered it = low ROI unless you find what they missed — look at the audit-report scope-exclusion section for what they EXPLICITLY didn't audit (oracles, governance, off-chain components, frontend, the admin path).

Multisig signers > 5 + timelock > 48h = low rug-pull risk; if your finding requires team-malicious assumptions, it's low-impact and likely out of scope per Immunefi's "centralization risk" exclusion. Read the program brief — most Immunefi programs explicitly downgrade or reject findings that assume admin malice.

### Reporting discipline

Immunefi requires Foundry PoC. Submission without PoC is auto-rejected. Submission with a PoC that requires manual setup ("first deploy this, then call that") usually gets downgraded — the PoC should be a single `forge test` invocation that proves the impact, with explicit `assertEq` on the drained balance / minted token / corrupted state.

Severity claims must use Immunefi's severity matrix exactly; don't invent severities. The matrix gates on direct economic loss percentage of TVL — a critical against a $500K protocol pays differently than a critical against a $500M one. Read the program's specific severity assignment before claiming Critical.


---
