# Why this exists — compiled FPF vs raw FPF

This document explains why this package exists adjacent to the original FPF specification, and why feeding the raw spec text to a model is a fundamentally different (and worse) operation than feeding it the compiled thinking map.

This is not a critique of FPF itself. As a human-readable transdisciplinary framework, FPF is strong and well-structured. The problem is not the framework — it is the assumption that a language model can absorb a 51,000-line specification and then apply it the way a human reader would.

We are not trying to turn FPF into another giant AI stack. We took what was useful for bounded traversal, compiled it, and kept the result intentionally small. That is the product choice here: publish a practical instrument, not an empire.

## The triple tax: the original product intuition

The original product intuition was that when you give a language model the raw FPF specification text and ask it to make a decision, it is forced through three kinds of work: parsing framework vocabulary, mapping framework vocabulary onto the task, and then answering through that lens.

`TRIPLE_TAX_CALCULUS.md` confirmed the token/cost side of that diagnosis very strongly. It did **not** confirm a stable literal measured `3-pass` internal sequence. Read the sections below as product intuition about where the tax comes from, not as a measured introspection trace.

### Pass 1 — Parse

The model reads the FPF text and activates attention on terms like "U.BoundedContext", "holon", "meta-holon", "ontic", "episteme." These are high-entropy tokens — rare words that pull attention strongly. The model spends capacity figuring out what the text MEANS before it can use it.

This is not how the model processes familiar concepts. When the model sees "test results passed," it maps that to a decision in one attention step. When it sees "the epistemic holon satisfies the F-G-R assurance calculus under the bounded context's invariant constitution," it spends multiple attention layers parsing syntax, resolving references, and building an internal representation of what the sentence is saying. The actual meaning ("the evidence is good enough") is the same, but the computational cost is higher.

### Pass 2 — Aggregate

Now the model tries to map the FPF concepts onto the actual question. "The user asked about deploying. FPF says deployment requires a U.Work enacted under a U.RoleAssignment within a U.BoundedContext with evidence satisfying B.3 F-G-R..." The model is translating between two vocabularies — the FPF vocabulary and the task vocabulary. Every translation is a re-reasoning step.

This pass is where the model burns the most tokens for the least value. It is not solving the problem. It is translating the problem into FPF terms and then back into task terms. The translation adds nothing — the original question already contained everything the model needs. But the FPF text forces the model to route through the framework's terminology.

### Pass 3 — Generate

Now the model answers. But it is answering through the FPF lens, which means every sentence is hedged with FPF terminology: "According to the holon-based epistemic framework, the role-assignment binding suggests..." The output is the model performing FPF, not solving the problem.

The generated text sounds rigorous. It uses the right FPF terms. It follows the right FPF structure. But it is not a better answer than the model would have given without FPF — it is the same answer wrapped in framework-flavored prose that the human reader must then unwrap to extract the actual decision.

### The tax adds up

Reason about the framework → reason about the mapping → reason about the answer. Three passes where one should suffice. And each pass activates the same attention patterns (the FPF vocabulary), which means the model's prior biases about those scientific-sounding terms get amplified. "Holon" sounds important, so the model treats it as important, and spends more tokens on it.

On a multi-step traversal, the tax compounds. Each step re-reads the framework, re-maps the vocabulary, re-generates the FPF-flavored output. By step 5, the context is full of the model arguing with itself about whether a "U.RoleAssignment" is the same as an "actor binding" and whether "epistemic" means "evidential" in this context. The actual decision — should we deploy? — is buried under layers of framework self-interpretation.

## What this package does instead

We compiled 51,000 lines into 10 dataclasses, 9 guards, and 6 logic operators. The FPF thinking happened once, at compile time, when we wrote the code. At runtime, the model never sees "holon" or "episteme" or "ontic." It sees:

```json
{
  "can_fire": false,
  "blockers": ["missing evidence: ['owner_approval']"],
  "response_contract": {
    "basis": [{"id": "test_results", "freshness": "current", "ttl_remaining": 6}],
    "modality": [{"commitment": "No deployment without evidence", "force": "must"}],
    "canonical_terms": {"deploy": "push artefact to production environment"}
  }
}
```

One pass. No translation. No re-reasoning. The code already did the FPF thinking and handed the model a JSON with the answer pre-computed.

The model's job shrinks from "understand this 51k-line philosophy of reasoning and then apply it" to "read this small JSON, fill in the claim field, pick the next move."

That smallness matters. It gives the model a simple operating surface for self-addressing its own run: what can fire, what cannot, what is missing, what is risky, whether it should continue, bridge, idle, or escalate. Not mystical agency. Just enough instrumentation to behave properly.

## Three problems with feeding raw FPF to a model

### 1. It makes the model re-reason N times

Once per FPF concept layer (context → role → commitment → gate → evidence → transition). Each layer is a re-reasoning pass because the model has to carry forward all prior layers. On a 6-step traversal with 6 concept layers, the model performs 36 reasoning passes where 6 would suffice (one per step, each reading a pre-computed slice).

### 2. It feeds the model biased activations

FPF uses terms like "agency spectrum", "candidate synthesis", "novelty-quality-diversity" that are already strong priors in the training data. The model sees these and shifts into "academic reasoning mode" — verbose, hedge-heavy, option-multiplying. Exactly the opposite of what a per-step decision map needs.

This is why we rejected FPF patterns like C.32 (candidate-synthesis logic) and NQD/OEE (novelty-quality-diversity). These patterns amplify existing LLM biases instead of constraining them. See [REJECTED_C32_CANDIDATE_SYNTHESIS.md](REJECTED_C32_CANDIDATE_SYNTHESIS.md) and [REJECTED_NQD_OEE_CULTURAL_EVOLUTION.md](REJECTED_NQD_OEE_CULTURAL_EVOLUTION.md).

### 3. It is a word blob organized for human readers, not machine consumption

The 51k lines are structured as sections, subsections, cross-references, normative statements, and examples — a format designed for a human reader who can skim, jump between sections, and build a mental model over multiple readings. A model reading this does what it does with any large text: skims, activates on familiar patterns, and generates text that sounds like the input. The output is FPF-flavored prose, not decisions.

## What FPF gets right (for humans)

None of this means FPF is wrong. For a human practitioner:

- The bounded context discipline is genuinely useful — it stops people from conflating terms across domains.
- The role/method/work separation catches real organizational confusion.
- The evidence-based gate system maps directly to how decisions should be made in engineering.
- The deontic commitment framework (MUST/SHOULD/MAY) prevents the common mistake of treating guidelines as requirements or vice versa.

These insights are strong. We extracted them. We compiled them into code that a model can use without re-deriving them from first principles on every step.

## The fundamental misunderstanding

Treating an LLM like a human reader who can absorb a framework and then apply it. An LLM is a pattern completer. Give it a framework, it completes the framework's patterns. Give it a structured template with precomputed values, it fills the template. The second one is useful.

FPF as a human-readable specification: strong.
FPF as raw input to a language model: triple tax.
FPF compiled into a thinking map with precomputed state: what this package does.

This is also why we release it publicly. The value is not private magic. The value is that other people building agents can stop overfeeding models with giant conceptual blobs and start giving them smaller, inspectable decision surfaces instead.

---

prichindel.com | 2026-07-06 | v1.3.1
