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
