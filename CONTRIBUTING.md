# Contributing

This package is maintained by **prichindel.com**.

## How to contribute

Submit contributions that improve the agentic runtime. Do not submit expansions of the semantic model for their own sake.

Before writing code, open an issue that states what agentic behavior your change affects. One sentence is enough: "the agent currently does X, it should do Y because Z."

### Review focus

- Bug fixes where the runtime produces a wrong outcome (wrong gate decision, wrong guard verdict, evidence check that doesn't enforce)
- New guards or logic rules that change what the agent does on a single move
- Improvements to the per-move slice size or prompt payload
- New example scenarios that demonstrate real domain use
- Documentation fixes

### Out of scope

- Additions that enrich the semantic model without changing per-move agent behavior
- FPF spec fidelity patches (we intentionally compress 51k lines into 10 primitives — that is the design, not a gap)
- Runtime payload growth (more fields in the LLM prompt state, wider slices, ambient scanning)
- Framework abstractions, plugin systems, or configuration layers

### Design rule

**Only add structure when a missing relation changes what the agent does on a single move.**

If your change makes the per-step chew larger without making the per-step decision better, do not ship it here. See `FPF_AUDIT_RESPONSE.md` for concrete examples of choices we left out and why.

## How to verify

```bash
python -m fpf_thinking_map.verify
```

Require all checks to pass. If you add new behavior, add a verification check for it.

## Process

1. Fork the repo
2. Create a branch from `main`
3. Make your change
4. Run `python -m fpf_thinking_map.verify` — all checks must pass
5. Open a pull request with a one-line description of the agentic behavior change

We review PRs manually. Response time varies.

## Contact

For questions about contributing: open a GitHub issue.

For anything unrelated to this package: **igareosh@igareosh.com**

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
