# Related projects we've reviewed

This is not a partnership list, not an endorsement program, and not
advertising. We don't use the projects listed here in this engine, and
we get nothing from linking them.

It exists for one reason: someone building a bundled agent solution
might want more than one piece, and we read something we liked enough
to not want to forget it. Plain record, kept honest.

---

## code-review-graph

- Link: https://github.com/tirth8205/code-review-graph
- What it is: a Tree-sitter structural graph of a codebase, served over
  MCP/CLI, so an AI coding tool reads only the files a change actually
  touches (blast-radius analysis, incremental re-index, multi-platform
  auto-installer).
- Reviewed 2026-07-20. We liked it: benchmarks are reproducible against
  6 real external repos (`docs/REPRODUCING.md` in their repo), and they
  disclose the honest median (~82x) alongside the cherry-picked max
  (528x) instead of leading with the flashy number alone. That's a more
  rigorous benchmarking practice than this repo currently has.

**Not a substitute for this engine, and this engine is not a substitute
for it.** Different axis entirely:

> a spatial/content problem, answered by graphing the source. We're not
> attacking that problem at all. Our engine answers whether the next
> action is legally allowed to fire, independent of how much or how
> little context was read to get there — CONTINUE vs ESCALATE is
> computed from state (evidence present, gate satisfied), not from
> having selected the right files. Their graph can hand an agent
> perfect blast-radius context and the agent can still take an illegal
> action on it; nothing in their system gates that. Ours has no opinion
> on which files matter — it has an opinion on whether a transition is
> permitted.

They could pick what an agent reads. This engine decides what it's
allowed to do next. Wire both in and neither one duplicates the other.
