# Spec — Run Proposal Language For Raw FPF vs Compiled Product

Purpose: future `fpf-agentic` run proposals must describe the product's reason to exist using the measured findings in `TRIPLE_TAX_CALCULUS.md`, not the older unmeasured literal `3 passes` story.

This spec is about proposal language, not about changing the engine.

## Problem Being Fixed

Older wording said raw FPF causes:

1. Parse
2. Aggregate
3. Generate

as if that exact 3-pass structure had been measured.

It was not measured that way.

What **was** measured:

- raw FPF monolith: `2,247,567` tokens
- raw FPF monolith live attempt: context-window failure
- raw exact-section prompt mean: `138,977.2` tokens per decision
- compiled product mean: `481.4` tokens per decision
- compiled vs full raw ratio: `4668.8x`
- compiled vs exact-section raw ratio: `288.7x`

What was **not** stably measured:

- a literal `Parse -> Aggregate -> Generate` pass sequence
- a stable self-reported pass count
- a superlinear compounding curve on the shipped traversal

## Mandatory Proposal Position

Every run proposal discussing "why this product exists" must frame the comparison like this:

- **Raw FPF** is Aliev's framework and remains valuable as a human framework.
- **This product** is a compiled operational surface built so an LLM can use FPF-derived constraints inside realistic context budgets.
- The main measured problem is **context fit and cost**, not "raw FPF is wrong."

## Required Claims

A compliant proposal must say all of the following, in substance:

1. Raw FPF monolith does not fit current practical context windows.
2. Reducing raw FPF to only the exact cited sections still leaves a very large prompt.
3. The compiled product reduces that decision surface to a small prompt.
4. Therefore the compiled product is a context-fit layer and a cost-control layer.
5. This compression is not free: some raw-FPF strictness can be flattened away.

## Forbidden Claims

A proposal must **not** say any of the following unless a new measurement explicitly proves them:

- "raw FPF was measured to take exactly 3 passes"
- "the model proved Parse / Aggregate / Generate"
- "the product has exactly 1 reasoning pass"
- "compounding was measured as superlinear"
- "raw FPF is broken"
- "raw FPF is inferior as a framework"

## Allowed Claims

These are safe:

- "raw FPF monolith does not fit"
- "raw exact-section prompting is still expensive"
- "the compiled product is dramatically smaller"
- "the compiled product is easier for an LLM to operate on"
- "the compiled product operationalizes raw FPF rather than reproducing it literally"
- "some semantic strictness is traded for tractability"

## Proposal Template

Use this structure in run proposals:

### 1. Position

`This proposal compares raw FPF as framework text against this compiled product as an LLM operating surface.`

### 2. Measured Reason The Product Exists

`Raw FPF monolith does not fit current context windows. Even the exact-section raw prompt remains large. The compiled product compresses the same decision surface into a small, inspectable JSON slice.`

### 3. Tradeoff

`The product gains tractability and cost control. It may lose some of raw FPF's stricter semantics in edge cases.`

### 4. Limits

`This proposal does not claim a measured literal 3-pass decomposition. The measured claim is token/cost/context-fit, not introspected cognition structure.`

## Canonical Short Version

Use this when the proposal needs one compact paragraph:

`Raw FPF as a monolithic prompt does not fit practical LLM context windows, and even a reduced raw exact-section prompt remains very large. This product exists to compile that framework into a small operational decision surface an LLM can actually use. The gain is context fit, cost reduction, and runtime tractability. The tradeoff is that some raw-FPF strictness can be flattened away in edge cases.`

## Canonical Longer Version

Use this when the proposal can afford a fuller explanation:

`The product is not claiming that raw FPF is a bad framework. The measured issue is that raw FPF, as prompt material, is too large and too expensive for direct runtime use. The full raw spec does not fit current practical context windows, and even the exact raw section-pack relevant to one decision remains large. This product compiles that framework into a small JSON decision surface so the model can operate inside realistic context and cost budgets. That is the real measured reason the product exists. The tradeoff is that compiled runtime convenience can flatten some semantic strictness that the raw framework would preserve.`

## Proposal Fields

When a run proposal is structured, include these fields:

- `raw_monolith_fit_status`
- `raw_monolith_tokens`
- `raw_exact_section_mean_tokens`
- `compiled_mean_tokens`
- `compiled_vs_full_raw_ratio`
- `compiled_vs_exact_section_ratio`
- `product_gain`
- `product_tradeoff`
- `measurement_limit`

Recommended values:

- `raw_monolith_fit_status = "does-not-fit"`
- `product_gain = "context-fit + cost-control + runtime tractability"`
- `product_tradeoff = "possible flattening of raw-FPF strictness in some edge cases"`
- `measurement_limit = "3-pass structure not stably measured"`

## Current Evidence Anchor

For now, proposals should anchor themselves to `TRIPLE_TAX_CALCULUS.md`, not to the older prose-only `triple tax` story in isolation.

If future measurements improve, this spec can be revised. Until then, proposal language must stay with what is actually measured.

SIGNED: Research/Developer (Cursor) | fpf-thinking-map product context | 2026-07-10 | run proposal language spec
