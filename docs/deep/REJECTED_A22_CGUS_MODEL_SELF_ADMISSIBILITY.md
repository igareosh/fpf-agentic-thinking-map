# Rejected: A.22.CGUS as a model self-admissibility procedure

**Status**: Acknowledged as a real FPF pattern — rejected as a practice for this package.
**Date**: 2026-07-17
**Decision by**: igareosh (prichindel.com)
**FPF source**: `A.22.CGUS` — Constraint-Governed Unfolding Structure, added to [ailev/FPF](https://github.com/ailev/FPF) 2026-07-09 (post-dates our 2026-06-24 vendoring snapshot; not yet a row in `SOURCES.md`)

---

## In plain terms

This note started as a conversation, not a spec review: someone pointed out a well-known FPF pattern called CGUS and asked whether it changes anything about how our engine lets a model make decisions. The honest answer turned out to be no — but working out *why* it's no is worth writing down, because the reasoning applies well beyond this one pattern.

CGUS, unpacked below, is really just a naming rule: don't call a single example "the structure" unless you can show the whole shape — the branches, the rules connecting them, what a reader loses by only seeing one path. It's about how you *write down* a structure you already have. It says nothing about how a model should generate or choose between options when it doesn't yet know the answer.

The question worth asking is what happens if someone borrows CGUS's language to dress up a different thing entirely: an LLM asked to "consider several options and pick the best one." Does listing ten options and picking one actually involve weighing ten options? Or does the model already know, in some sense, what it's going to say — and the list is just decoration around a conclusion that was reached the moment the model started answering?

That question matters for a document engine like this one, because it's exactly the same question we already answered once before, for a different FPF pattern (`ESEO`, see `RELATED_WORK_GOFLOW_FPF_SKILL.md`): can a model be trusted to honestly report on its own reasoning process? Our answer there was no. This note is that same answer, re-derived for a new pattern, so the "no" doesn't quietly get forgotten the next time a plausible-sounding pattern shows up wearing new vocabulary.

## What A.22.CGUS actually is

A.22.CGUS is a specialization of a broader FPF pattern (`A.22`, "Structure and Structural Views") for one specific situation: a structure that has several branch points and rules about which branches can connect to which — not just one path from start to finish. It's only meant to be invoked when that complexity is real.

Its actual content is a three-way distinction:

1. **A provisional demonstration** — showing one example path, before anyone has actually laid out the full shape (all the branches, all the rules). Showing an example is not the same as proving the full structure exists.
2. **A whole-structure description** — after the full shape has actually been laid out: every branch, every rule connecting positions, what's kept and what's lost when you move between them.
3. **A demonstrative slice** — after that full shape exists, walking one chosen path through it for a reader, clearly labeled as one path among many, not the whole thing.

The purpose is narrow and reasonable: stop people from showing a single tidy example — a README diagram, a slide, a rehearsed explanation — and letting it silently stand in for a much messier reality with branches the example never mentions. That's a discipline about *documentation honesty*. It is not a decision-making procedure, and it does not claim to be one. It has nothing to say about how a model that doesn't yet know the answer should go about generating or choosing between candidate answers.

## The practice we're actually rejecting

The thing under evaluation here isn't CGUS itself — it's a *use* of CGUS's vocabulary: dressing up an LLM's "generate several options, then pick one" behavior as if the enumeration were a genuine search through admissible possibilities, and the pick a considered judgment about which one satisfies the constraints.

**Rejected**, for the same underlying reason we already rejected `ESEO` (a different FPF pattern that asks a model to classify which phase of reasoning it's currently in): both ask a model to honestly report on something happening inside its own generation process, with no way for anyone — including the model — to check the report against anything outside the model's own words.

Here's the mechanism in plain terms. A language model generates one token at a time, and every token it writes is generated conditioned on every token before it — including its own. So picture an agent asked to weigh a decision. It writes: *"Let me consider several options. Option 1... Option 2... Option 3... I'll go with option 3 because..."* That reads like careful deliberation. But by the time it's writing option 2, option 1's wording has already shaped what follows; by option 3, the model is continuing a pattern it started, not independently re-deriving an answer from scratch. Whatever the model was already leaning toward writing is what get elaborated and then selected — the list is decoration around a conclusion the model reached the moment it started answering, not a real comparison of ten independent candidates.

This gets worse the longer the visible reasoning runs, not better. Once a model has already written five paragraphs building toward an answer, a sixth paragraph is far more likely to agree with the first five than to seriously contradict them — because agreeing with prior context is what a next-token predictor is built to do well. A weak, late-arriving option can get "approved" for no better reason than that the accumulated text already leaned toward yes. That's sycophancy toward one's own prior output, not evaluation.

None of this is CGUS's fault. CGUS never claimed to generate or judge candidate options — it's silent on that question entirely. The thing being rejected here is borrowing its name to imply a safety property that was never on offer.

## What this actually requires, stated plainly

Not a new rule for this package — a sharper statement of one we already committed to when we rejected `ESEO`: **whatever decides "this option is admissible" cannot be the same model, in the same conversation, that generated the option.** Concretely, that check has to come from one of two places:

- a genuinely separate model or agent, started fresh, with no memory of the conversation that produced the option — nothing in its own prior output to feel obligated to agree with; or
- something that isn't a language model at all: ordinary code, checking plain facts (does the required evidence exist? is the gate open? is there a role conflict?) and returning a fixed answer.

"The same model pauses and double-checks itself two paragraphs later" does not count. It's still finishing the same sentence it started, in the sense that matters — same context, same accumulated momentum toward agreement. It looks like a second opinion. It's an echo of the first one.

This package's guard stack already takes the second path: ordinary Python, checking facts about state, with no language model involved in the checking at all. That's not an incidental implementation detail — it's the entire reason the guards can't be talked into approving a bad option no matter how much prior text argued for it. There's no "prior text" the guard code is trying to stay consistent with. It just checks the fact.

## What would change this

If A.22.CGUS (or something built on it) were ever adopted here purely to *describe* our own engine's branch structure for a human reader auditing the code — with no claim that a model uses it to pick between branches — that's a different, much narrower use, and this rejection wouldn't apply to it. That's the one door left open: documentation, never decision-making.

---

prichindel.com | 2026-07-17 | v1.5.0
