# Reflections

Not part of the package, not linked from the README. Just context on why this project took the shape it did.

## The wind tunnel

In 1899 Wilbur Wright wrote to the Smithsonian for everything they had on flight. He and Orville read Lilienthal, Chanute, Langley — the entire published record. Then their own gliders didn't fly the way the numbers said they should. Instead of assuming they'd built something wrong, they built a wind tunnel and tested 200 wing shapes themselves. Lilienthal's lift tables, which the whole field had been building on, turned out to be wrong. Not slightly off — wrong.

They didn't reject the literature. They read all of it first. What they refused to do was treat it as ground truth just because it was published, respected, and came before them.

## Why that's the reference point here

FPF (First Principles Framework) is the literature we started from — 51,000 lines, genuinely well-built for a human reader. The instinct with a framework like that is to hand the whole thing to a model and trust that if the framework is sound, the model's use of it will be sound too. That's the Langley move: trust the published table, scale it up, fly it.

We built the wind tunnel instead. `docs/deep/WHY_THIS_EXISTS.md` is the writeup of what we found when we actually tested how a model behaves when it reads raw FPF versus a compiled slice of it — the triple tax of parse/aggregate/generate, the same failure shape every time. `docs/deep/REJECTED_C32_CANDIDATE_SYNTHESIS.md` and `docs/deep/REJECTED_NQD_OEE_CULTURAL_EVOLUTION.md` are two specific results from that tunnel: patterns that read well in the spec and made model behavior worse in practice, so they didn't make it into the compiled map. Not because we doubted FPF as a framework for humans — we didn't. Because the question was never "is this framework good," it was "does this specific mechanism survive contact with how a language model actually reads it," and some of it didn't.

That's the whole difference between this package and just forwarding the spec to a model. Not more framework. Testing before trusting it, keeping what held up, publishing that.

## The part worth remembering

The Wright brothers didn't win because they had more resources — Langley had those, and more prestige, and crashed nine days earlier. They won because they treated first principles and existing frameworks as two different tools, not as competitors, and knew which one to reach for when the other one's numbers stopped matching what they were seeing in front of them.

Same rule applies here: use the framework for speed, use direct testing for truth, and don't confuse a well-written table for a verified one.

— igareosh

## Lego blocks and the five whys

There's a simpler way to say what the wind tunnel section above says, and it's the Lego-house one. Hand someone a finished house and most people rearrange a few blocks and call it improved. Take the house apart down to individual bricks and you can build a different house, or a bridge, or nothing house-shaped at all. The value isn't in going infinitely deep — it's in going one or two layers past where everyone else stopped.

FPF as published is a finished house. It's a good one. The default move is what most people do with any framework: take it whole, hand it to the model, rearrange a few prompts around the edges when it doesn't work, call that the improvement. We took it apart into bricks instead — the ten dataclasses, nine guards, six logic operators in `primitives.py`, `guards.py`, `logic.py` — and only reassembled the pieces that survived being asked *why* they needed to be there.

That's the other technique in this piece: the five whys. Not a metaphor, an actual thing we did on every FPF mechanism that made it into the compiled map. Why does the model need this concept at runtime — because it changes what the model is allowed to do next. Why does it need it phrased this way — it doesn't, that phrasing is for human readers, so it got compiled into a JSON key instead. Why does the model need to reason about "epistemic holons" — it doesn't, it needs to know if evidence is missing, so that's the field name now. Every layer of "why" that didn't terminate in something the model's next decision actually depended on got cut. `docs/deep/REJECTED_C32_CANDIDATE_SYNTHESIS.md` and `docs/deep/REJECTED_NQD_OEE_CULTURAL_EVOLUTION.md` are what's left over when you ask why enough times and the answer runs out before you reach something load-bearing.

The corporate-meeting version of this in the piece — ask why three times and someone says "let's take this offline" — is the same failure as handing a model the raw spec and hoping it self-organizes. Both are a refusal to go one layer deeper because the first layer was already familiar and already published. The whole point of this package is that we did the annoying part once, at compile time, so the model doesn't have to reason by analogy to a 51,000-line document on every single step. It gets the bricks that were already tested, not the house that was already built.

— igareosh

## The scope rail

"First Principles Framework" promises something small — the load-bearing few things underneath everything else, the way Feynman's "you must not fool yourself" is one sentence, not a specification. What actually exists at `ailev/FPF` is 51,000 lines. That's not a contradiction by itself; distilling first principles into something usable can take a lot of scaffolding. But go a layer deeper and a pattern shows up worth naming plainly: whole parts of that 51,000 lines exist to manage problems the other parts of it created. F.8 exists because a spec this large invites naming drift — convenient phrases becoming durable ontology by accident. F.17 exists because term decisions made in one corner of a framework this size stop being legible in another corner. E.20 exists because a kernel this large can't be edited safely without an eleven-step protocol just to add one mechanism without breaking three others. I.2 exists because picking the right entry pattern out of the rest of it is hard enough to need an eight-case worked-example annex. E.23 exists because the natural response to "this isn't working" at this scale is blind agentic retry, so someone had to write the pattern that stops that.

None of that is incompetence. It's what happens to anything that grows past the size a person can hold in their head at once: it starts spending real effort on its own internal consistency instead of on the problem it was originally for. A framework maintaining coherence against itself is a framework treating its own girth as a standing cost of doing business, and once you're 51,000 lines in, the fix on offer is always more framework — another pattern, another protocol, another annex — because within that world, more structured text is the only tool available. That's a reasonable answer if your readers are humans with sustained attention across a career. It is close to the worst possible answer if your reader is a language model doing one step of one task, because more structured text is exactly the thing `docs/deep/WHY_THIS_EXISTS.md` calls the triple tax: parse it, map it onto the actual question, generate through it. FPF's own self-maintenance patterns are proof the framework knows this size has a cost. They just pay that cost in more framework, because that's the only currency a spec has. An LLM-shaped answer would be the opposite move: stop adding pattern, start compiling it away.

That's the rail for this package, stated as plainly as it can be stated: never let this repository's own size become the next thing it has to manage. Ten primitives, nine guards, six operators is not an accident of where we happened to stop — it is the actual bet, that a per-move constraint surface has to stay small enough that it never needs its own F.8, its own E.20, its own eleven-step protocol for adding to itself. The day this package needs a pattern to govern how it adds patterns to itself is the day it has become the thing it was built to avoid feeding a model. `docs/deep/REJECTED_C32_CANDIDATE_SYNTHESIS.md` and `docs/deep/REJECTED_F17_UNIFIED_TERM_SHEET.md` are both, underneath the specific reasoning in each, the same refusal: not "is this a good idea," but "does adding this make the next person's next move smaller, or does it make the machinery around every move a little bit bigger." Smaller is the only direction this repository is allowed to grow.

— igareosh
