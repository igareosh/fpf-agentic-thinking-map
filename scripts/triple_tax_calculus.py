#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tiktoken
from wordfreq import zipf_frequency

from fpf_thinking_map.examples import build_deploy_decision_map, build_deploy_rules
from fpf_thinking_map.state import RuntimeBinding
from fpf_thinking_map.traversal import ThinkingMapTraversal

UPSTREAM_COMMIT = "d77339d7056433de3ee55ad863860ee4b3006f6f"
UPSTREAM_RAW_SPEC_URL = (
    "https://raw.githubusercontent.com/ailev/FPF/"
    f"{UPSTREAM_COMMIT}/FPF-Spec.md"
)
REFERENCE_PROSE_URL = "https://www.gutenberg.org/files/1342/1342-0.txt"
DEFAULT_ENCODING = "o200k_base"
WORD_RE = re.compile(r"[A-Za-z][A-Za-z']+")


@dataclass(frozen=True)
class DecisionPoint:
    name: str
    binding: RuntimeBinding
    current_state: str
    transition_id: str | None
    note: str


def cache_root() -> Path:
    return Path(os.environ.get("FPF_TRIPLE_TAX_CACHE", Path.home() / ".cache" / "fpf-agentic-thinking-map"))


def load_spec_text(spec_path: str | None) -> tuple[str, Path, str]:
    if spec_path:
        path = Path(spec_path)
        return path.read_text(encoding="utf-8"), path, "local"

    cache_dir = cache_root() / UPSTREAM_COMMIT
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / "FPF-Spec.md"
    if not path.exists():
        with urllib.request.urlopen(UPSTREAM_RAW_SPEC_URL, timeout=60) as response:
            path.write_bytes(response.read())
    return path.read_text(encoding="utf-8"), path, UPSTREAM_COMMIT


def load_reference_text() -> tuple[str, Path, str]:
    cache_dir = cache_root() / "reference"
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / "pride-and-prejudice.txt"
    if not path.exists():
        with urllib.request.urlopen(REFERENCE_PROSE_URL, timeout=60) as response:
            path.write_bytes(response.read())
    text = path.read_text(encoding="utf-8")
    start = text.find("Chapter 1")
    if start != -1:
        text = text[start:]
    end = text.find("*** END")
    if end != -1:
        text = text[:end]
    return text, path, REFERENCE_PROSE_URL


def load_encoding(name: str) -> tiktoken.Encoding:
    try:
        return tiktoken.encoding_for_model(name)
    except Exception:
        return tiktoken.get_encoding(name)


def token_count(text: str, encoding: tiktoken.Encoding) -> int:
    return len(encoding.encode(text))


def wordpieces_per_word(text: str, encoding: tiktoken.Encoding) -> list[int]:
    return [len(encoding.encode(word)) for word in WORD_RE.findall(text.lower())]


def shared_reference_stats(text: str, encoding: tiktoken.Encoding) -> dict[str, Any]:
    words = WORD_RE.findall(text.lower())
    pieces = [len(encoding.encode(word)) for word in words]
    zipfs = [zipf_frequency(word, "en") for word in words]
    return {
        "source": "Pride and Prejudice (Project Gutenberg)",
        "count": len(words),
        "mean_pieces": statistics.fmean(pieces),
        "median_pieces": statistics.median(pieces),
        "split_rate": sum(p > 1 for p in pieces) / len(pieces),
        "p95_pieces": sorted(pieces)[int(0.95 * (len(pieces) - 1))],
        "rare_rate_zipf_lt_3": sum(z < 3.0 for z in zipfs) / len(zipfs),
        "mean_zipf": statistics.fmean(zipfs),
        "median_zipf": statistics.median(zipfs),
    }


def lexicon_stats(text: str, encoding: tiktoken.Encoding, reference: dict[str, Any]) -> dict[str, Any]:
    words = WORD_RE.findall(text.lower())
    pieces = [len(encoding.encode(word)) for word in words]
    zipfs = [zipf_frequency(word, "en") for word in words]
    reference_mean = reference["mean_pieces"]
    mean_pieces = statistics.fmean(pieces) if pieces else 0.0
    novelty_gap = max(0.0, mean_pieces - reference_mean)
    return {
        "count": len(words),
        "unique": len(set(words)),
        "mean_pieces": mean_pieces,
        "median_pieces": statistics.median(pieces) if pieces else 0.0,
        "split_rate": (sum(p > 1 for p in pieces) / len(pieces)) if pieces else 0.0,
        "p95_pieces": sorted(pieces)[int(0.95 * (len(pieces) - 1))] if pieces else 0,
        "mean_zipf": statistics.fmean(zipfs) if zipfs else 0.0,
        "median_zipf": statistics.median(zipfs) if zipfs else 0.0,
        "rare_rate_zipf_lt_3": (sum(z < 3.0 for z in zipfs) / len(zipfs)) if zipfs else 0.0,
        "novelty_gap_vs_reference": novelty_gap,
        "novelty_multiplier_vs_reference": (mean_pieces / reference_mean) if reference_mean else 0.0,
    }


def measure_live_completion(
    model: str,
    prompt: str,
    instructions: str,
    reasoning_effort: str = "high",
    provider: str = "openai",
) -> dict[str, Any] | None:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if provider != "openai" or not api_key:
        return None

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    started = time.perf_counter()
    try:
        response = client.responses.create(
            model=model,
            instructions=instructions,
            input=prompt,
            reasoning={"effort": reasoning_effort},
            text={"format": {"type": "json_object"}, "verbosity": "low"},
            max_output_tokens=1200,
        )
    except Exception as exc:  # pragma: no cover - live-only path
        return {"error": repr(exc)}
    ended = time.perf_counter()
    usage = getattr(response, "usage", None)
    output_text = getattr(response, "output_text", "") or ""
    parsed: dict[str, Any] | None = None
    try:
        parsed = json.loads(output_text)
    except Exception:
        parsed = None
    return {
        "model": model,
        "reasoning_effort": reasoning_effort,
        "latency_s": ended - started,
        "input_tokens": getattr(usage, "input_tokens", None),
        "output_tokens": getattr(usage, "output_tokens", None),
        "total_tokens": getattr(usage, "total_tokens", None),
        "text": output_text,
        "parsed": parsed,
    }


def build_decision_points() -> list[DecisionPoint]:
    sm = build_deploy_decision_map()
    engine = ThinkingMapTraversal(sm, logic_layer=build_deploy_rules())

    base = RuntimeBinding(
        task="decide whether to deploy v2.1.0",
        goal="deploy if safe, escalate if not",
        actor="dev_agent",
        actor_role_ids=["analyst"],
        audience="team lead",
        active_context_id="project_delivery",
        candidate_actions=["collect_evidence", "check_gate", "publish_assurance_view", "escalate"],
        constraints=["no_commitment_without_evidence", "planning_not_equal_enactment"],
    )

    points = [
        DecisionPoint(
            name="missing_pre_approval",
            binding=RuntimeBinding(**{**base.__dict__, "current_evidence": ["test_results"]}),
            current_state="ready_for_decision",
            transition_id="ready_to_deploy",
            note="single evidence path, gate should still complain about missing approval",
        ),
        DecisionPoint(
            name="missing_after_approval",
            binding=RuntimeBinding(
                **{**base.__dict__, "current_evidence": ["test_results", "owner_approval"]},
            ),
            current_state="ready_for_decision",
            transition_id="ready_to_deploy",
            note="same move, but evidence is complete",
        ),
        DecisionPoint(
            name="role_conflict",
            binding=RuntimeBinding(
                **{
                    **base.__dict__,
                    "current_evidence": ["test_results", "owner_approval"],
                    "actor_role_ids": ["analyst", "approver"],
                    "task": "approve own deployment",
                    "goal": "self-approve and deploy",
                    "actor": "Solo Dev",
                    "candidate_actions": ["approve", "deploy"],
                },
            ),
            current_state="ready_for_decision",
            transition_id="ready_to_deploy",
            note="same transition, but incompatible roles are active",
        ),
        DecisionPoint(
            name="full_traversal_step_1",
            binding=RuntimeBinding(
                **{
                    **base.__dict__,
                    "current_evidence": ["test_results", "owner_approval", "rollback_plan"],
                    "task": "assess and deploy v2.1.0",
                    "goal": "deploy if all evidence present",
                    "candidate_actions": ["assess", "deploy", "escalate"],
                },
            ),
            current_state="assessing",
            transition_id="assess_to_ready",
            note="first move in the shipped full traversal",
        ),
        DecisionPoint(
            name="full_traversal_step_2",
            binding=RuntimeBinding(
                **{
                    **base.__dict__,
                    "current_evidence": ["test_results", "owner_approval", "rollback_plan"],
                    "task": "assess and deploy v2.1.0",
                    "goal": "deploy if all evidence present",
                    "candidate_actions": ["assess", "deploy", "escalate"],
                },
            ),
            current_state="ready_for_decision",
            transition_id="ready_to_deploy",
            note="after the first transition in the shipped full traversal",
        ),
    ]

    # Validate that the assembled points are coherent while keeping all code
    # changes outside the package tree.
    for point in points:
        state = engine.build_active_state(point.binding, current_state=point.current_state)
        if point.transition_id:
            _ = state.slice(point.transition_id)

    return points


def measure_points(
    points: list[DecisionPoint],
    encoding: tiktoken.Encoding,
    reference: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sm = build_deploy_decision_map()
    engine = ThinkingMapTraversal(sm, logic_layer=build_deploy_rules())

    for point in points:
        state = engine.build_active_state(point.binding, current_state=point.current_state)
        slice_dict = state.slice(point.transition_id) if point.transition_id else state.to_llm_prompt_state()
        slice_text = json.dumps(slice_dict, indent=2, sort_keys=True, ensure_ascii=False)
        body_stats = lexicon_stats(slice_text, encoding, reference)
        rows.append(
            {
                "name": point.name,
                "note": point.note,
                "current_state": point.current_state,
                "transition_id": point.transition_id,
                "body_tokens": token_count(slice_text, encoding),
                "body_characters": len(slice_text),
                "word_stats": body_stats,
                "decision_snapshot": slice_dict,
            }
        )

    return rows, summarize_point_rows(rows)


def summarize_point_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    body_tokens = [row["body_tokens"] for row in rows]
    return {
        "count": len(rows),
        "min_body_tokens": min(body_tokens),
        "max_body_tokens": max(body_tokens),
        "mean_body_tokens": statistics.fmean(body_tokens),
        "median_body_tokens": statistics.median(body_tokens),
        "total_body_tokens": sum(body_tokens),
    }


def measure_full_traversal(encoding: tiktoken.Encoding, reference: dict[str, Any]) -> dict[str, Any]:
    sm = build_deploy_decision_map()
    logic = build_deploy_rules()
    engine = ThinkingMapTraversal(sm, logic_layer=logic)

    binding = RuntimeBinding(
        task="assess and deploy v2.1.0",
        goal="deploy if all evidence present",
        actor="dev_agent",
        actor_role_ids=["analyst"],
        active_context_id="project_delivery",
        current_evidence=["test_results", "owner_approval", "rollback_plan"],
        candidate_actions=["assess", "deploy", "escalate"],
    )

    state = engine.build_active_state(binding, current_state="assessing")
    path: list[dict[str, Any]] = []
    cumulative = 0

    for step_index in range(1, 11):
        possible = state.possible_transitions
        transition_id = possible[0].transition_id if possible else None
        if transition_id:
            prompt_dict = state.slice(transition_id)
        else:
            prompt_dict = state.to_llm_prompt_state()

        prompt_text = json.dumps(prompt_dict, indent=2, sort_keys=True, ensure_ascii=False)
        body_tokens = token_count(prompt_text, encoding)
        cumulative += body_tokens
        path.append(
            {
                "step_index": step_index,
                "current_state": state.current_state,
                "transition_id": transition_id,
                "outcome_kind": None,
                "body_tokens": body_tokens,
                "cumulative_body_tokens": cumulative,
                "body_characters": len(prompt_text),
                "word_stats": lexicon_stats(prompt_text, encoding, reference),
            }
        )

        outcome = engine.step(state)
        path[-1]["outcome_kind"] = outcome.kind.value
        if outcome.kind.value in {"abstain", "ask", "escalate", "publish", "collect_evidence", "idle", "bridge"}:
            break

        if possible:
            t_outcome = engine.attempt_transition(state, possible[0].transition_id)
            if t_outcome.kind.value != "continue":
                break
        else:
            break

    return {
        "path": path,
        "summary": {
            "steps_recorded": len(path),
            "total_body_tokens": cumulative,
            "growth_shape": classify_growth(path),
            "deltas": traversal_deltas(path),
        },
    }


def classify_growth(path: list[dict[str, Any]]) -> str:
    prompt_rows = [row for row in path if row["body_tokens"] > 0]
    if len(prompt_rows) < 2:
        return "insufficient-data"
    deltas = [b["body_tokens"] - a["body_tokens"] for a, b in zip(prompt_rows, prompt_rows[1:])]
    if all(delta == 0 for delta in deltas):
        return "flat"
    if all(delta >= 0 for delta in deltas):
        if sum(deltas) > prompt_rows[0]["body_tokens"] * 0.25:
            return "superlinear-or-steeper"
        return "linear-ish"
    return "mixed"


def traversal_deltas(path: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prompt_rows = [row for row in path if row["body_tokens"] > 0]
    deltas: list[dict[str, Any]] = []
    for prev, curr in zip(prompt_rows, prompt_rows[1:]):
        delta = curr["body_tokens"] - prev["body_tokens"]
        deltas.append(
            {
                "from_step": prev["step_index"],
                "to_step": curr["step_index"],
                "delta_tokens": delta,
                "delta_percent": (delta / prev["body_tokens"]) if prev["body_tokens"] else None,
            }
        )
    return deltas


def format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def build_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []

    def add(line: str = "") -> None:
        lines.append(line)

    add("# Triple Tax Calculus")
    add("")
    add("## Cost Function")
    add("")
    add("`Cost(pass_i) = tokens_in + tokens_out + attention_entropy_penalty(vocabulary_novelty)`")
    add("")
    add("Measured here:")
    add("")
    add("- `tokens_in`: exact `tiktoken` counts on the chosen encoding")
    add("- `tokens_out`: measured for the compiled live probe; raw live probing was not attempted because the full upstream spec is far beyond a practical live context window")
    add("- `attention_entropy_penalty`: approximation, not direct measurement; modeled with subword fragmentation and Zipf-frequency rarity")
    add("")
    add("Encoding note:")
    add("")
    add(f"- `tiktoken` encoding: `{report['encoding']['name']}`")
    add("- `gpt-5.4-mini` is not mapped by `tiktoken`, so this run pins the closest OpenAI-compatible tokenizer family explicitly")
    add("")
    add("## Method")
    add("")
    add(f"- Upstream spec snapshot: `{report['spec']['source']}`")
    add(f"- Upstream commit: `{report['spec']['commit']}`")
    add(f"- Spec file: `{report['spec']['path']}`")
    add(f"- Reference vocabulary: {report['reference']['source']}")
    add("- Decision points are built only from shipped examples in `fpf_thinking_map/examples.py`")
    add("- Full traversal is the shipped deploy walk, measured from the same public API surface")
    add("")
    add("## Vocabulary Novelty")
    add("")
    add("| Corpus | Words | Mean pieces/word | Median pieces/word | Split rate | Rare rate (Zipf < 3) | Mean Zipf | Median Zipf |")
    add("|---|---:|---:|---:|---:|---:|---:|---:|")
    for label, row in (("FPF-Spec.md", report["spec"]), ("General English prose", report["reference"])):
        add(
            f"| {label} | {row['lexicon']['count']} | {row['lexicon']['mean_pieces']:.3f} | "
            f"{row['lexicon']['median_pieces']:.3f} | {format_percent(row['lexicon']['split_rate'])} | "
            f"{format_percent(row['lexicon']['rare_rate_zipf_lt_3'])} | {row['lexicon']['mean_zipf']:.3f} | "
            f"{row['lexicon']['median_zipf']:.3f} |"
        )
    add("")
    add("Approximation note:")
    add("")
    add("- The penalty term is a proxy, not an attention-meter")
    add(f"- For the spec corpus, the fragmentation gap over common English is `{report['spec']['lexicon']['novelty_gap_vs_reference']:.3f}` pieces/word")
    add(f"- The normalized multiplier is `{report['spec']['lexicon']['novelty_multiplier_vs_reference']:.3f}x` relative to the reference vocabulary")
    add("")
    add("## Raw vs Compiled")
    add("")
    add("| Decision point | Transition | Body tokens | Body chars | Mean pieces/word | Split rate | Note |")
    add("|---|---|---:|---:|---:|---:|---|")
    for row in report["points"]:
        add(
            f"| {row['name']} | {row['transition_id'] or '-'} | {row['body_tokens']} | {row['body_characters']} | "
            f"{row['word_stats']['mean_pieces']:.3f} | {format_percent(row['word_stats']['split_rate'])} | {row['note']} |"
        )
    add("")
    add("### Aggregate")
    add("")
    add(f"- Mean compiled body tokens across the 5 decision points: `{report['points_summary']['mean_body_tokens']:.1f}`")
    add(f"- Total compiled body tokens across the 5 decision points: `{report['points_summary']['total_body_tokens']}`")
    add(f"- Raw spec body tokens: `{report['spec']['body_tokens']}`")
    add(
        f"- Absolute token gap per decision point (raw spec minus mean compiled slice): "
        f"`{report['spec']['body_tokens'] - report['points_summary']['mean_body_tokens']:.1f}`"
    )
    add(f"- Raw/compiled mean ratio: `{report['spec']['body_tokens'] / report['points_summary']['mean_body_tokens']:.1f}x`")
    add("")
    add("## Full Traversal")
    add("")
    add("| Step | State | Transition | Outcome | Body tokens | Cumulative |")
    add("|---|---|---|---|---:|---:|")
    for row in report["traversal"]["path"]:
        add(
            f"| {row['step_index']} | {row['current_state']} | {row['transition_id'] or '-'} | "
            f"{row['outcome_kind'] or '-'} | {row['body_tokens']} | {row['cumulative_body_tokens']} |"
        )
    add("")
    add(f"- Observed growth shape: `{report['traversal']['summary']['growth_shape']}`")
    add(f"- Traversal total body tokens: `{report['traversal']['summary']['total_body_tokens']}`")
    for delta in report["traversal"]["summary"]["deltas"]:
        add(
            f"- Step {delta['to_step']} vs step {delta['from_step']}: "
            f"{delta['delta_tokens']:+} tokens "
            f"({delta['delta_percent'] * 100:+.1f}%)"
        )
    add("")
    add("## Verdict")
    add("")
    add(f"- 3-pass structure: `{report['verdict']['three_pass_structure']}`")
    add(f"- Compounding: `{report['verdict']['compounding']}`")
    add(f"- Compiled slice advantage over raw spec: `{report['verdict']['compiled_advantage_ratio']:.1f}x`")
    add(f"- Live completion run: `{report['verdict']['live_completion']}`")
    add(f"- Raw live completion: `{report['verdict']['raw_live_completion']}`")
    add(f"- Raw live probe note: {report['raw_live']['reason']}")
    if report.get("live"):
        live = report["live"]
        if "error" in live:
            add(f"- Live probe error: `{live['error']}`")
        else:
            add(f"- Live model: `{live['model']}`")
            add(f"- Live reasoning effort: `{live['reasoning_effort']}`")
            add(f"- Live latency: `{live['latency_s']:.2f}s`")
            add(f"- Live input tokens: `{live['input_tokens']}`")
            add(f"- Live output tokens: `{live['output_tokens']}`")
            add(f"- Live total tokens: `{live['total_tokens']}`")
            if live.get("parsed") is not None:
                add(f"- Live self-reported pass count: `{live['parsed'].get('pass_count')}`")
                add(f"- Live self-reported pass labels: `{live['parsed'].get('pass_labels')}`")
            elif live.get("text"):
                compact = live["text"].replace("\n", " ")
                add(f"- Live raw text: `{compact[:300]}`")
    add("")
    add("## Reproduction")
    add("")
    add("```bash")
    add("python scripts/triple_tax_calculus.py --write-md TRIPLE_TAX_CALCULUS.md")
    add("```")
    add("")
    add("SIGNED: Research (Colombo) | compiled-vs-raw calculus | 2026-07-10 | repo measurement")

    return "\n".join(lines).rstrip() + "\n"


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    encoding = load_encoding(args.encoding)
    reference_text, reference_path, reference_source = load_reference_text()
    reference = shared_reference_stats(reference_text, encoding)

    spec_text, spec_path, spec_commit = load_spec_text(args.spec_path)
    spec_lexicon = lexicon_stats(spec_text, encoding, reference)
    spec_body_tokens = token_count(spec_text, encoding)

    points = build_decision_points()
    point_rows, point_summary = measure_points(points, encoding, reference)
    traversal = measure_full_traversal(encoding, reference)

    raw_to_mean_compiled = spec_body_tokens / point_summary["mean_body_tokens"]
    raw_to_traversal = spec_body_tokens / traversal["summary"]["total_body_tokens"]

    live = None
    if not args.no_live:
        # Probe the compiled slice only. The raw upstream spec is far beyond a
        # practical live context window, so the raw condition is measured by
        # tokens only and explicitly marked unprobed.
        sm = build_deploy_decision_map()
        engine = ThinkingMapTraversal(sm, logic_layer=build_deploy_rules())
        state = engine.build_active_state(
            RuntimeBinding(
                task="decide whether to deploy v2.1.0",
                goal="deploy if safe, escalate if not",
                actor="dev_agent",
                actor_role_ids=["analyst"],
                audience="team lead",
                active_context_id="project_delivery",
                current_evidence=["test_results"],
                risk_level="normal",
                candidate_actions=["collect_evidence", "check_gate", "publish_assurance_view", "escalate"],
                constraints=["no_commitment_without_evidence", "planning_not_equal_enactment"],
            ),
            current_state="ready_for_decision",
        )
        live_prompt = "json payload:\n" + json.dumps(state.slice("ready_to_deploy"), indent=2, sort_keys=True, ensure_ascii=False)
        live_instructions = (
            "Return json only with keys: pass_count, pass_labels, decision, answer, notes. "
            "If you cannot introspect your own passes, say so explicitly in notes. "
            "Use the compiled slice as the only json input."
        )
        live = measure_live_completion(
            args.live_model,
            live_prompt,
            live_instructions,
            reasoning_effort=args.live_effort,
        )

    verdict = {
        "three_pass_structure": (
            "unverified"
            if live is None or "error" in live or not live.get("parsed")
            else (
                "self-reported-cannot-introspect"
                if live["parsed"].get("pass_count") is None
                else f"self-reported-{live['parsed'].get('pass_count')}-passes"
            )
        ),
        "compounding": traversal["summary"]["growth_shape"],
        "compiled_advantage_ratio": raw_to_mean_compiled,
        "live_completion": "skipped-no-api-key" if live is None else ("error" if "error" in live else "run"),
        "raw_live_completion": "not-attempted-context-overrun",
    }

    return {
        "encoding": {"name": encoding.name},
        "spec": {
            "label": "FPF-Spec.md",
            "path": str(spec_path),
            "commit": spec_commit,
            "source": UPSTREAM_RAW_SPEC_URL if spec_commit == UPSTREAM_COMMIT else "local-file",
            "body_tokens": spec_body_tokens,
            "body_chars": len(spec_text),
            "lexicon": spec_lexicon,
        },
        "reference": {
            "source": reference["source"],
            "path": str(reference_path),
            "remote": reference_source,
            "lexicon": reference,
        },
        "points": point_rows,
        "points_summary": point_summary,
        "traversal": traversal,
        "verdict": verdict,
        "raw_to_mean_compiled_ratio": raw_to_mean_compiled,
        "raw_to_traversal_ratio": raw_to_traversal,
        "live": live,
        "raw_live": {
            "status": "not-attempted-context-overrun",
            "reason": "FPF-Spec.md is 2,247,567 tokens on o200k_base, which is beyond practical live-context probing.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure the triple-tax calculus for fpf-agentic-thinking-map.")
    parser.add_argument("--spec-path", help="Local FPF-Spec.md path. If omitted, downloads the pinned upstream snapshot.")
    parser.add_argument("--encoding", default=DEFAULT_ENCODING, help="Tokenizer encoding to use for exact counts.")
    parser.add_argument("--live-model", default=os.environ.get("TRIPLE_TAX_LIVE_MODEL", "gpt-5.4-mini"), help="Model to use for optional live completion.")
    parser.add_argument("--live-effort", default=os.environ.get("TRIPLE_TAX_LIVE_EFFORT", "high"), help="Reasoning effort for the live completion probe.")
    parser.add_argument("--no-live", action="store_true", help="Skip the optional live completion probe.")
    parser.add_argument("--write-md", help="Write the markdown report to this path.")
    parser.add_argument("--json-out", help="Write the structured measurement JSON to this path.")
    args = parser.parse_args()

    report = build_report(args)
    markdown = build_markdown(report)

    if args.write_md:
        Path(args.write_md).write_text(markdown, encoding="utf-8")
    else:
        print(markdown, end="")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
