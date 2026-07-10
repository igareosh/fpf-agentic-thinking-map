# Reflections

Not part of the package, not linked from the README. Just context on why this project took the shape it did.

## The wind tunnel

In 1899 Wilbur Wright wrote to the Smithsonian for everything they had on flight. He and Orville read Lilienthal, Chanute, Langley — the entire published record. Then their own gliders didn't fly the way the numbers said they should. Instead of assuming they'd built something wrong, they built a wind tunnel and tested 200 wing shapes themselves. Lilienthal's lift tables, which the whole field had been building on, turned out to be wrong. Not slightly off — wrong.

They didn't reject the literature. They read all of it first. What they refused to do was treat it as ground truth just because it was published, respected, and came before them.

## Why that's the reference point here

FPF (First Principles Framework) is the literature we started from — 51,000 lines, genuinely well-built for a human reader. The instinct with a framework like that is to hand the whole thing to a model and trust that if the framework is sound, the model's use of it will be sound too. That's the Langley move: trust the published table, scale it up, fly it.

We built the wind tunnel instead. `WHY_THIS_EXISTS.md` is the writeup of what we found when we actually tested how a model behaves when it reads raw FPF versus a compiled slice of it — the triple tax of parse/aggregate/generate, the same failure shape every time. `REJECTED_C32_CANDIDATE_SYNTHESIS.md` and `REJECTED_NQD_OEE_CULTURAL_EVOLUTION.md` are two specific results from that tunnel: patterns that read well in the spec and made model behavior worse in practice, so they didn't make it into the compiled map. Not because we doubted FPF as a framework for humans — we didn't. Because the question was never "is this framework good," it was "does this specific mechanism survive contact with how a language model actually reads it," and some of it didn't.

That's the whole difference between this package and just forwarding the spec to a model. Not more framework. Testing before trusting it, keeping what held up, publishing that.

## The part worth remembering

The Wright brothers didn't win because they had more resources — Langley had those, and more prestige, and crashed nine days earlier. They won because they treated first principles and existing frameworks as two different tools, not as competitors, and knew which one to reach for when the other one's numbers stopped matching what they were seeing in front of them.

Same rule applies here: use the framework for speed, use direct testing for truth, and don't confuse a well-written table for a verified one.

— igareosh

## Lego blocks and the five whys

There's a simpler way to say what the wind tunnel section above says, and it's the Lego-house one. Hand someone a finished house and most people rearrange a few blocks and call it improved. Take the house apart down to individual bricks and you can build a different house, or a bridge, or nothing house-shaped at all. The value isn't in going infinitely deep — it's in going one or two layers past where everyone else stopped.

FPF as published is a finished house. It's a good one. The default move is what most people do with any framework: take it whole, hand it to the model, rearrange a few prompts around the edges when it doesn't work, call that the improvement. We took it apart into bricks instead — the ten dataclasses, nine guards, six logic operators in `primitives.py`, `guards.py`, `logic.py` — and only reassembled the pieces that survived being asked *why* they needed to be there.

That's the other technique in this piece: the five whys. Not a metaphor, an actual thing we did on every FPF mechanism that made it into the compiled map. Why does the model need this concept at runtime — because it changes what the model is allowed to do next. Why does it need it phrased this way — it doesn't, that phrasing is for human readers, so it got compiled into a JSON key instead. Why does the model need to reason about "epistemic holons" — it doesn't, it needs to know if evidence is missing, so that's the field name now. Every layer of "why" that didn't terminate in something the model's next decision actually depended on got cut. `REJECTED_C32_CANDIDATE_SYNTHESIS.md` and `REJECTED_NQD_OEE_CULTURAL_EVOLUTION.md` are what's left over when you ask why enough times and the answer runs out before you reach something load-bearing.

The corporate-meeting version of this in the piece — ask why three times and someone says "let's take this offline" — is the same failure as handing a model the raw spec and hoping it self-organizes. Both are a refusal to go one layer deeper because the first layer was already familiar and already published. The whole point of this package is that we did the annoying part once, at compile time, so the model doesn't have to reason by analogy to a 51,000-line document on every single step. It gets the bricks that were already tested, not the house that was already built.

— igareosh
