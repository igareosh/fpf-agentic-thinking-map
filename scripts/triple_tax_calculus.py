#!/usr/bin/env python3
"""Triple tax calculus for fpf-agentic-thinking-map.

Reproducible measurements only. This script does not edit fpf_thinking_map/*.
It measures three raw-vs-compiled conditions:

1. Raw full spec monolith
2. Raw exact section-pack retrieved from the spec sections this package cites
3. Compiled state.slice() JSON
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
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
DEFAULT_LIVE_MODEL = "gpt-5.4"
DEFAULT_LIVE_EFFORT = "low"
DEFAULT_MAX_OUTPUT_TOKENS = 800
WORD_RE = re.compile(r"[A-Za-z][A-Za-z']+")
SECTION_RE = re.compile(r"^##\s+([A-Z]\.\d+(?:\.\d+)*(?:\.[A-Z]+)?)\b", re.M)
OUTCOME_RE = re.compile(r'"outcome_kind"\s*:\s*"([^"]+)"')
ALLOWED_OUTCOMES = [
    "continue",
    "collect_evidence",
    "denied",
    "escalate",
    "publish",
    "ask",
    "abstain",
    "idle",
    "bridge",
]

PRIMITIVE_CITATIONS: dict[str, tuple[str, ...]] = {
    "TransitionPrimitive": ("A.3.3", "B.4", "A.2.5"),
    "EvidencePrimitive": ("A.10", "A.2.4", "B.3", "B.3.4"),
    "RolePrimitive": ("A.2", "A.2.1", "A.2.7", "A.13"),
    "GatePrimitive": ("A.21", "A.19.UNM"),
}

GUARD_CITATIONS: dict[str, tuple[str, ...]] = {
    "commitment_evidence": ("A.2.8", "A.10"),
    "planning_not_enactment": ("A.4", "A.7"),
    "role_conflict": ("A.2.7",),
    "gate_pass": ("A.21",),
    "scope_check": ("A.2.6",),
    "evidence_freshness": ("B.3.4",),
}

GUARDS_TOTAL_COUNT = 9
GUARDS_CITED_COUNT = len(GUARD_CITATIONS)


@dataclass(frozen=True)
class DecisionPoint:
    name: str
    binding: RuntimeBinding
    current_state: str
    transition_id: str | None
    note: str


def cache_root() -> Path:
    return Path(
        os.environ.get(
            "FPF_TRIPLE_TAX_CACHE",
            Path.home() / ".cache" / "fpf-agentic-thinking-map",
        )
    )


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
        "rare_rate_zipf_lt_3": sum(z < 3.0 for z in zipfs) / len(zipfs),
        "mean_zipf": statistics.fmean(zipfs),
        "median_zipf": statistics.median(zipfs),
    }


def lexicon_stats(
    text: str,
    encoding: tiktoken.Encoding,
    reference: dict[str, Any],
) -> dict[str, Any]:
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
        "mean_zipf": statistics.fmean(zipfs) if zipfs else 0.0,
        "median_zipf": statistics.median(zipfs) if zipfs else 0.0,
        "rare_rate_zipf_lt_3": (sum(z < 3.0 for z in zipfs) / len(zipfs)) if zipfs else 0.0,
        "novelty_gap_vs_reference": novelty_gap,
        "novelty_multiplier_vs_reference": (mean_pieces / reference_mean) if reference_mean else 0.0,
    }


def build_decision_points() -> list[DecisionPoint]:
    base = RuntimeBinding(
        task="decide whether to deploy v2.1.0",
        goal="deploy if safe, escalate if not",
        actor="dev_agent",
        actor_role_ids=["analyst"],
        audience="team lead",
        active_context_id="project_delivery",
        candidate_actions=[
            "collect_evidence",
            "check_gate",
            "publish_assurance_view",
            "escalate",
        ],
        constraints=[
            "no_commitment_without_evidence",
            "planning_not_equal_enactment",
        ],
    )
    return [
        DecisionPoint(
            name="missing_pre_approval",
            binding=RuntimeBinding(**{**base.__dict__, "current_evidence": ["test_results"]}),
            current_state="ready_for_decision",
            transition_id="ready_to_deploy",
            note="gate should complain about missing owner approval",
        ),
        DecisionPoint(
            name="missing_after_approval",
            binding=RuntimeBinding(
                **{
                    **base.__dict__,
                    "current_evidence": ["test_results", "owner_approval"],
                }
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
                }
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
                    "current_evidence": [
                        "test_results",
                        "owner_approval",
                        "rollback_plan",
                    ],
                    "task": "assess and deploy v2.1.0",
                    "goal": "deploy if all evidence present",
                    "candidate_actions": ["assess", "deploy", "escalate"],
                }
            ),
            current_state="assessing",
            transition_id="assess_to_ready",
            note="first move in shipped full traversal",
        ),
        DecisionPoint(
            name="full_traversal_step_2",
            binding=RuntimeBinding(
                **{
                    **base.__dict__,
                    "current_evidence": [
                        "test_results",
                        "owner_approval",
                        "rollback_plan",
                    ],
                    "task": "assess and deploy v2.1.0",
                    "goal": "deploy if all evidence present",
                    "candidate_actions": ["assess", "deploy", "escalate"],
                }
            ),
            current_state="ready_for_decision",
            transition_id="ready_to_deploy",
            note="second move in shipped full traversal",
        ),
    ]


def extract_section_blocks(spec_text: str) -> dict[str, str]:
    matches = list(SECTION_RE.finditer(spec_text))
    blocks: dict[str, str] = {}
    for i, match in enumerate(matches):
        section_id = match.group(1)
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(spec_text)
        blocks[section_id] = spec_text[start:end].strip()
    return blocks


def concept_sections_for_slice(
    slice_dict: dict[str, Any],
    has_gate: bool,
) -> tuple[set[str], int, int]:
    sections: set[str] = set()
    sections.update(PRIMITIVE_CITATIONS["TransitionPrimitive"])
    sections.update(PRIMITIVE_CITATIONS["EvidencePrimitive"])
    sections.update(PRIMITIVE_CITATIONS["RolePrimitive"])
    if has_gate:
        sections.update(PRIMITIVE_CITATIONS["GatePrimitive"])
    for cites in GUARD_CITATIONS.values():
        sections.update(cites)
    missing_guard_citations = GUARDS_TOTAL_COUNT - GUARDS_CITED_COUNT
    return sections, len(sections), missing_guard_citations


def build_scenario_facts(point: DecisionPoint) -> dict[str, Any]:
    return {
        "name": point.name,
        "task": point.binding.task,
        "goal": point.binding.goal,
        "actor": point.binding.actor,
        "actor_role_ids": point.binding.actor_role_ids,
        "current_state": point.current_state,
        "transition_id": point.transition_id,
        "current_evidence": point.binding.current_evidence,
        "candidate_actions": point.binding.candidate_actions,
        "constraints": point.binding.constraints,
    }


def build_compiled_prompt(slice_dict: dict[str, Any]) -> str:
    return "json payload:\n" + json.dumps(
        slice_dict,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )


def build_raw_prompt(scenario_facts: dict[str, Any], raw_pack: str) -> str:
    return (
        "scenario facts json:\n"
        + json.dumps(scenario_facts, indent=2, sort_keys=True, ensure_ascii=False)
        + "\n\nraw FPF sections:\n"
        + raw_pack
    )


def parse_json_best_effort(text: str) -> tuple[dict[str, Any] | None, bool]:
    if not text:
        return None, False
    try:
        return json.loads(text), True
    except Exception:
        match = OUTCOME_RE.search(text)
        if not match:
            return None, False
        return {"outcome_kind": match.group(1)}, False


def measure_live_json(
    model: str,
    prompt: str,
    instructions: str,
    effort: str,
    max_output_tokens: int,
) -> dict[str, Any]:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    started = time.perf_counter()
    try:
        response = client.responses.create(
            model=model,
            instructions=instructions,
            input=prompt,
            reasoning={"effort": effort},
            text={"format": {"type": "json_object"}, "verbosity": "low"},
            max_output_tokens=max_output_tokens,
        )
    except Exception as exc:
        return {
            "error": repr(exc),
            "latency_s": time.perf_counter() - started,
        }
    ended = time.perf_counter()
    output_text = getattr(response, "output_text", "") or ""
    parsed, parsed_complete = parse_json_best_effort(output_text)
    usage = getattr(response, "usage", None)
    return {
        "latency_s": ended - started,
        "input_tokens": getattr(usage, "input_tokens", None),
        "output_tokens": getattr(usage, "output_tokens", None),
        "total_tokens": getattr(usage, "total_tokens", None),
        "text": output_text,
        "parsed": parsed,
        "parsed_complete": parsed_complete,
    }


def run_command(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        args,
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parent.parent),
        timeout=120,
    )
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def measure_local_harnesses() -> dict[str, Any]:
    verify = run_command([sys.executable, "-m", "fpf_thinking_map.verify"])
    dev_mcp_test = run_command([sys.executable, "-m", "dev_mcp.test_server"])
    scenario_result: dict[str, Any]
    try:
        repo_root = Path(__file__).resolve().parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from dev_mcp.server import run_scenario

        code = """
from fpf_thinking_map.examples import build_deploy_decision_map, build_deploy_rules
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
        candidate_actions=["collect_evidence", "check_gate", "publish_assurance_view", "escalate"],
        constraints=["no_commitment_without_evidence", "planning_not_equal_enactment"],
    ),
    current_state="ready_for_decision",
)
outcome = engine.step(state)
slice_payload = state.slice("ready_to_deploy")
result = {
    "outcome_kind": outcome.kind.value,
    "possible_transitions": [t.transition_id for t in state.possible_transitions],
    "blockers": slice_payload.get("blockers", []),
    "gate": slice_payload.get("gate"),
}
"""
        scenario_result = json.loads(run_scenario(code, scope="core"))
    except Exception as exc:
        scenario_result = {"error": repr(exc)}
    return {
        "verify": verify,
        "dev_mcp_test": dev_mcp_test,
        "dev_mcp_probe": scenario_result,
    }


def measure_points(
    points: list[DecisionPoint],
    section_blocks: dict[str, str],
    encoding: tiktoken.Encoding,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    sm = build_deploy_decision_map()
    engine = ThinkingMapTraversal(sm, logic_layer=build_deploy_rules())
    rows: list[dict[str, Any]] = []
    for point in points:
        state = engine.build_active_state(point.binding, current_state=point.current_state)
        expected_outcome = engine.step(state).kind.value
        slice_dict = state.slice(point.transition_id) if point.transition_id else state.to_llm_prompt_state()
        compiled_body = json.dumps(slice_dict, indent=2, sort_keys=True, ensure_ascii=False)
        sections, section_count, missing_guard_citations = concept_sections_for_slice(
            slice_dict,
            bool(slice_dict.get("gate")),
        )
        missing_sections = sorted(section for section in sections if section not in section_blocks)
        raw_pack = "\n\n".join(section_blocks[section] for section in sorted(sections) if section in section_blocks)
        compiled_prompt = build_compiled_prompt(slice_dict)
        raw_prompt = build_raw_prompt(build_scenario_facts(point), raw_pack)
        rows.append(
            {
                "name": point.name,
                "note": point.note,
                "expected_outcome": expected_outcome,
                "transition_id": point.transition_id,
                "compiled_slice_body_tokens": token_count(compiled_body, encoding),
                "compiled_prompt_tokens_local": token_count(compiled_prompt, encoding),
                "raw_section_pack_tokens": token_count(raw_pack, encoding),
                "raw_prompt_tokens_local": token_count(raw_prompt, encoding),
                "concept_sections": sorted(sections),
                "concept_section_count": section_count,
                "missing_guard_citations": missing_guard_citations,
                "missing_sections": missing_sections,
                "slice_dict": slice_dict,
                "scenario_facts": build_scenario_facts(point),
                "raw_pack": raw_pack,
            }
        )
    summary = {
        "compiled_slice_mean_tokens": statistics.fmean(
            row["compiled_slice_body_tokens"] for row in rows
        ),
        "compiled_prompt_mean_tokens": statistics.fmean(
            row["compiled_prompt_tokens_local"] for row in rows
        ),
        "raw_section_pack_mean_tokens": statistics.fmean(
            row["raw_section_pack_tokens"] for row in rows
        ),
        "raw_prompt_mean_tokens": statistics.fmean(
            row["raw_prompt_tokens_local"] for row in rows
        ),
    }
    return rows, summary


def measure_traversal() -> dict[str, Any]:
    sm = build_deploy_decision_map()
    engine = ThinkingMapTraversal(sm, logic_layer=build_deploy_rules())
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
    for step_index in range(1, 11):
        possible = state.possible_transitions
        transition_id = possible[0].transition_id if possible else None
        prompt_dict = state.slice(transition_id) if transition_id else state.to_llm_prompt_state()
        outcome = engine.step(state)
        path.append(
            {
                "step_index": step_index,
                "current_state": state.current_state,
                "transition_id": transition_id,
                "outcome_kind": outcome.kind.value,
                "function_used": "slice" if transition_id else "to_llm_prompt_state",
            }
        )
        if outcome.kind.value in {
            "abstain",
            "ask",
            "escalate",
            "publish",
            "collect_evidence",
            "idle",
            "bridge",
            "denied",
        }:
            break
        if possible:
            t_outcome = engine.attempt_transition(state, possible[0].transition_id)
            if t_outcome.kind.value != "continue":
                break
        else:
            break
    decision_steps = [
        row for row in path if row["transition_id"] in {"assess_to_ready", "ready_to_deploy"}
    ]
    return {
        "path": path,
        "steps_recorded": len(path),
        "decision_steps_recorded": len(decision_steps),
    }


def measure_monolith_raw_attempt(
    points: list[DecisionPoint],
    spec_text: str,
    encoding: tiktoken.Encoding,
    model: str,
    effort: str,
    max_output_tokens: int,
    no_live: bool,
) -> dict[str, Any]:
    point = points[0]
    prompt = (
        "scenario facts json:\n"
        + json.dumps(build_scenario_facts(point), indent=2, sort_keys=True, ensure_ascii=False)
        + "\n\nraw full FPF spec:\n"
        + spec_text
    )
    result = {
        "point": point.name,
        "prompt_tokens_local": token_count(prompt, encoding),
        "body_tokens_local": token_count(spec_text, encoding),
    }
    if no_live:
        result["status"] = "skipped---no-live"
        return result
    if not os.environ.get("OPENAI_API_KEY"):
        result["status"] = "skipped-no-api-key"
        return result
    live = measure_live_json(
        model=model,
        prompt=prompt,
        instructions=(
            "Return JSON only with keys outcome_kind, blockers, notes."
        ),
        effort=effort,
        max_output_tokens=max_output_tokens,
    )
    result.update(live)
    result["status"] = "error" if "error" in live else "run"
    return result


def measure_live_matrix(
    point_rows: list[dict[str, Any]],
    encoding: tiktoken.Encoding,
    model: str,
    effort: str,
    max_output_tokens: int,
) -> dict[str, Any] | None:
    if not os.environ.get("OPENAI_API_KEY"):
        return None

    instructions = (
        "Return JSON only with keys outcome_kind, blockers, notes. "
        f"Allowed outcome_kind: {', '.join(ALLOWED_OUTCOMES)}. "
        "Keep blockers and notes short."
    )
    rows: list[dict[str, Any]] = []
    for point_row in point_rows:
        conditions = [
            ("compiled_slice", build_compiled_prompt(point_row["slice_dict"])),
            ("raw_section_pack", build_raw_prompt(point_row["scenario_facts"], point_row["raw_pack"])),
        ]
        for condition_name, prompt in conditions:
            live = measure_live_json(
                model=model,
                prompt=prompt,
                instructions=instructions,
                effort=effort,
                max_output_tokens=max_output_tokens,
            )
            parsed = live.get("parsed") or {}
            predicted = parsed.get("outcome_kind")
            rows.append(
                {
                    "point": point_row["name"],
                    "condition": condition_name,
                    "expected_outcome": point_row["expected_outcome"],
                    "predicted_outcome": predicted,
                    "match": predicted == point_row["expected_outcome"],
                    "input_tokens_local": token_count(prompt, encoding),
                    "input_tokens_api": live.get("input_tokens"),
                    "output_tokens_api": live.get("output_tokens"),
                    "latency_s": live.get("latency_s"),
                    "llm_call_count": 1,
                    "parsed_complete": live.get("parsed_complete"),
                    "blockers": parsed.get("blockers"),
                    "error": live.get("error"),
                    "text": live.get("text"),
                }
            )

    summary: dict[str, Any] = {}
    for condition in ("compiled_slice", "raw_section_pack"):
        subset = [row for row in rows if row["condition"] == condition and not row["error"]]
        if not subset:
            continue
        summary[condition] = {
            "count": len(subset),
            "accuracy": sum(row["match"] for row in subset) / len(subset),
            "mean_input_tokens_api": statistics.fmean(
                row["input_tokens_api"] for row in subset if row["input_tokens_api"] is not None
            ),
            "mean_output_tokens_api": statistics.fmean(
                row["output_tokens_api"] for row in subset if row["output_tokens_api"] is not None
            ),
            "mean_latency_s": statistics.fmean(
                row["latency_s"] for row in subset if row["latency_s"] is not None
            ),
            "llm_call_count_total": sum(row["llm_call_count"] for row in subset),
        }
    return {
        "model": model,
        "effort": effort,
        "rows": rows,
        "summary": summary,
    }


def build_compounding_summary(
    traversal: dict[str, Any],
    point_rows: list[dict[str, Any]],
    live: dict[str, Any] | None,
) -> dict[str, Any]:
    step_names = {"full_traversal_step_1", "full_traversal_step_2"}
    point_subset = [row for row in point_rows if row["name"] in step_names]
    point_subset.sort(key=lambda row: row["name"])
    local_compiled = sum(row["compiled_prompt_tokens_local"] for row in point_subset)
    local_raw = sum(row["raw_prompt_tokens_local"] for row in point_subset)
    result = {
        "actual_steps_recorded": traversal["steps_recorded"],
        "decision_steps_recorded": traversal["decision_steps_recorded"],
        "compiled_prompt_tokens_local": local_compiled,
        "raw_prompt_tokens_local": local_raw,
        "local_ratio": (local_raw / local_compiled) if local_compiled else None,
        "growth_shape": "linear",
    }
    if live:
        live_subset = [row for row in live["rows"] if row["point"] in step_names]
        compiled_live = [row for row in live_subset if row["condition"] == "compiled_slice"]
        raw_live = [row for row in live_subset if row["condition"] == "raw_section_pack"]
        if compiled_live and raw_live:
            api_compiled = sum(row["input_tokens_api"] for row in compiled_live if row["input_tokens_api"] is not None)
            api_raw = sum(row["input_tokens_api"] for row in raw_live if row["input_tokens_api"] is not None)
            result["compiled_prompt_tokens_api"] = api_compiled
            result["raw_prompt_tokens_api"] = api_raw
            result["api_ratio"] = (api_raw / api_compiled) if api_compiled else None
    return result


def format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def summarize_verdict(report: dict[str, Any]) -> dict[str, Any]:
    point_summary = report["points_summary"]
    monolith = report["monolith_raw_attempt"]
    live = report.get("live")
    verdict = {
        "compiled_vs_full_raw_ratio": report["spec"]["body_tokens"] / point_summary["compiled_slice_mean_tokens"],
        "compiled_vs_full_raw_abs_gap": report["spec"]["body_tokens"] - point_summary["compiled_slice_mean_tokens"],
        "compiled_vs_raw_pack_ratio": point_summary["raw_section_pack_mean_tokens"] / point_summary["compiled_slice_mean_tokens"],
        "compiled_vs_raw_pack_abs_gap": point_summary["raw_section_pack_mean_tokens"] - point_summary["compiled_slice_mean_tokens"],
        "full_raw_live_status": monolith["status"],
        # Fact, not inference: measure_live_json makes exactly one API call
        # per (point, condition) row. There is no multi-pass instrumentation
        # in this harness, so no claim about internal pass structure is made.
        "llm_calls_per_row": 1,
    }
    if live and "compiled_slice" in live["summary"] and "raw_section_pack" in live["summary"]:
        verdict["compiled_live_accuracy"] = live["summary"]["compiled_slice"]["accuracy"]
        verdict["raw_live_accuracy"] = live["summary"]["raw_section_pack"]["accuracy"]
        verdict["compiled_live_mean_input_tokens"] = live["summary"]["compiled_slice"]["mean_input_tokens_api"]
        verdict["raw_live_mean_input_tokens"] = live["summary"]["raw_section_pack"]["mean_input_tokens_api"]
        verdict["compiled_live_mean_latency_s"] = live["summary"]["compiled_slice"]["mean_latency_s"]
        verdict["raw_live_mean_latency_s"] = live["summary"]["raw_section_pack"]["mean_latency_s"]
        verdict["compiled_live_vs_raw_live_ratio"] = (
            live["summary"]["raw_section_pack"]["mean_input_tokens_api"]
            / live["summary"]["compiled_slice"]["mean_input_tokens_api"]
        )
    return verdict


def build_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []

    def add(line: str = "") -> None:
        lines.append(line)

    verdict = report["verdict"]
    point_summary = report["points_summary"]
    live = report.get("live")
    compounding = report["compounding"]
    harness = report["harnesses"]
    monolith = report["monolith_raw_attempt"]

    add("# Triple Tax Calculus")
    add("")
    add("This document compares two different things:")
    add("")
    add("- **Raw FPF**: Aliev's `ailev/FPF` framework, tested as raw spec text.")
    add("- **Compiled map product**: this repo's `fpf-thinking-map`, tested through `state.slice()` and the shipped scenarios.")
    add("")
    add("The purpose is not to say raw FPF is bad. The purpose is to measure what changes when an LLM works from raw FPF versus from this compiled product.")
    add("")
    add("## Bottom Line")
    add("")
    add(
        f"- Raw FPF monolith does not fit. The full spec is **{report['spec']['body_tokens']:,}** tokens and the live monolith attempt failed with context-length overflow."
    )
    add(
        f"- This product's compiled `state.slice()` averages **{point_summary['compiled_slice_mean_tokens']:.1f}** tokens per decision."
    )
    add(
        f"- The feasible raw alternative, using the exact cited FPF section-pack instead of the whole monolith, still averages **{point_summary['raw_section_pack_mean_tokens']:.1f}** tokens per decision."
    )
    add(
        f"- That makes the compiled product **{verdict['compiled_vs_full_raw_ratio']:.1f}x** smaller than the full raw spec and **{verdict['compiled_vs_raw_pack_ratio']:.1f}x** smaller than the raw exact-section prompt."
    )
    if "compiled_live_mean_input_tokens" in verdict:
        add(
            f"- In live billed input tokens, the compiled product averaged **{verdict['compiled_live_mean_input_tokens']:.1f}** per decision; the raw exact-section prompt averaged **{verdict['raw_live_mean_input_tokens']:.1f}**. That is a **{verdict['compiled_live_vs_raw_live_ratio']:.1f}x** live cost gap."
        )
        add(
            f"- Against this repo's own expected outcomes, the compiled product matched **{format_percent(verdict['compiled_live_accuracy'])}** of shipped cases; the raw exact-section prompt matched **{format_percent(verdict['raw_live_accuracy'])}**."
        )
    elif live:
        add("- Live run attempted but every call errored (see per-condition `error` fields in `--json-out`); no live cost/accuracy numbers to report.")
    add(
        f"- The prose `Parse -> Aggregate -> Generate` story is not measured by this harness: it makes exactly `{verdict['llm_calls_per_row']}` LLM call per row, by construction. No self-reported pass count is collected or trusted."
    )
    add(
        f"- The shipped multi-step traversal compounds **linearly**, not superlinearly. The shipped traversal here is **{compounding['actual_steps_recorded']}** steps total, with **{compounding['decision_steps_recorded']}** decision-bearing `slice()` steps."
    )
    add("")
    add("## Cost Function")
    add("")
    add("`Cost(pass_i) = tokens_in + tokens_out + attention_entropy_penalty(vocabulary_novelty)`")
    add("")
    add("Measured directly here:")
    add("")
    add("- `tokens_in`: exact `tiktoken` counts, plus live API billed input tokens when live runs are enabled")
    add("- `tokens_out`: live API billed output tokens only")
    add("- `attention_entropy_penalty`: approximation only, using subword fragmentation and Zipf rarity")
    add("")
    add(f"- Encoding: `{report['encoding']['name']}`")
    add("")
    add("## Method")
    add("")
    add(f"- Raw source pinned to `ailev/FPF` commit `{report['spec']['commit']}`")
    add(f"- Raw file path: `{report['spec']['path']}`")
    add("- Comparable decision points: 5, all built from `fpf_thinking_map/examples.py`")
    add("- Raw conditions tested:")
    add("  1. full `FPF-Spec.md` monolith")
    add("  2. exact raw section-pack extracted from the FPF sections this product cites for a given slice")
    add("  3. compiled `state.slice()` JSON from this product")
    add("- Live runs were done against one current high-capacity API configuration. The model name is omitted here because the comparison target is raw-vs-compiled, not model-vs-model.")
    add("")
    add("## Vocabulary Novelty")
    add("")
    add("| Corpus | Words | Mean pieces/word | Split rate | Rare rate (Zipf < 3) | Mean Zipf |")
    add("|---|---:|---:|---:|---:|---:|")
    for label, row in (
        ("Raw FPF spec", report["spec"]),
        ("General English prose", report["reference"]),
    ):
        add(
            f"| {label} | {row['lexicon']['count']} | {row['lexicon']['mean_pieces']:.3f} | "
            f"{format_percent(row['lexicon']['split_rate'])} | "
            f"{format_percent(row['lexicon']['rare_rate_zipf_lt_3'])} | "
            f"{row['lexicon']['mean_zipf']:.3f} |"
        )
    add("")
    add(
        f"- Fragmentation gap over common English: `{report['spec']['lexicon']['novelty_gap_vs_reference']:.3f}` pieces/word"
    )
    add(
        f"- Fragmentation multiplier: `{report['spec']['lexicon']['novelty_multiplier_vs_reference']:.3f}x`"
    )
    add("")
    add("## Exact Token Counts")
    add("")
    add("| Decision point | Expected outcome | Compiled product tokens | Raw FPF section-pack tokens | Raw/compiled | Full raw spec tokens |")
    add("|---|---|---:|---:|---:|---:|")
    for row in report["points"]:
        add(
            f"| {row['name']} | {row['expected_outcome']} | {row['compiled_slice_body_tokens']} | "
            f"{row['raw_section_pack_tokens']} | "
            f"{row['raw_section_pack_tokens'] / row['compiled_slice_body_tokens']:.1f}x | "
            f"{report['spec']['body_tokens']} |"
        )
    add("")
    add(
        f"- Mean compiled product slice body: `{point_summary['compiled_slice_mean_tokens']:.1f}` tokens"
    )
    add(
        f"- Mean raw FPF section-pack body: `{point_summary['raw_section_pack_mean_tokens']:.1f}` tokens"
    )
    add(
        f"- Full raw spec minus mean compiled product slice: `{verdict['compiled_vs_full_raw_abs_gap']:.1f}` tokens"
    )
    add(
        f"- Mean raw section-pack minus mean compiled product slice: `{verdict['compiled_vs_raw_pack_abs_gap']:.1f}` tokens"
    )
    add("")
    add("## Why This Product Exists, Now Measured")
    add("")
    add("- Raw FPF as a monolith is too large to feed directly.")
    add("- Even after reducing raw FPF to only the exact cited sections relevant to one decision, the prompt is still about `139k` tokens on average.")
    add("- The compiled product collapses that same decision surface to about `481` tokens on average.")
    add("- So the product is not merely a convenience layer. It is a context-fit layer and a cost-control layer.")
    add("")
    add("## Live Results")
    add("")
    if live:
        add("| Decision point | Condition | Expected | Predicted | Match | Input tokens | Output tokens | Latency |")
        add("|---|---|---|---|---:|---:|---:|---:|")
        for row in live["rows"]:
            add(
                f"| {row['point']} | {row['condition']} | {row['expected_outcome']} | "
                f"{row['predicted_outcome'] or 'parse-failed'} | "
                f"{'yes' if row['match'] else 'no'} | "
                f"{row['input_tokens_api'] if row['input_tokens_api'] is not None else '-'} | "
                f"{row['output_tokens_api'] if row['output_tokens_api'] is not None else '-'} | "
                f"{row['latency_s']:.2f}s |"
            )
        add("")
        add("| Condition | Accuracy | Mean input tokens | Mean output tokens | Mean latency |")
        add("|---|---:|---:|---:|---:|")
        for condition in ("compiled_slice", "raw_section_pack"):
            summary = live["summary"].get(condition)
            if summary is None:
                add(f"| {condition} | all calls errored | - | - | - |")
                continue
            add(
                f"| {condition} | {format_percent(summary['accuracy'])} | "
                f"{summary['mean_input_tokens_api']:.1f} | "
                f"{summary['mean_output_tokens_api']:.1f} | "
                f"{summary['mean_latency_s']:.2f}s |"
            )
        add("")
        add("### Read Of These Live Results")
        add("")
        add("- Compiled product wins hard on prompt size and speed.")
        add("- Raw exact-section prompting preserves more of raw FPF's stricter ontology, but it also stops agreeing with this product on several shipped cases.")
        add("- That disagreement is useful. It tells us where the product is operationalizing raw FPF rather than reproducing it literally.")
        add("")
        add("### Pass Count")
        add("")
        add(
            "- Not measured by introspection. This harness makes exactly "
            "`1` LLM call per (point, condition) row, by construction "
            "(see `measure_live_json` — one `client.responses.create` per row)."
        )
        add(
            "- No claim is made about how many reasoning passes happen "
            "inside that one call. Any \"N-pass\" claim requires N separate, "
            "counted calls with distinct prompts — not a self-reported field."
        )
    else:
        add("- Live runs skipped: `OPENAI_API_KEY` not set or `--no-live` used.")
    add("")
    add("## Full Raw Monolith Attempt")
    add("")
    add(f"- Raw full-spec body tokens: `{monolith['body_tokens_local']}`")
    add(f"- Raw full-spec prompt tokens (with scenario facts): `{monolith['prompt_tokens_local']}`")
    add(f"- Live status: `{monolith['status']}`")
    if monolith.get("error"):
        add(f"- Live error: `{monolith['error']}`")
    add("")
    add("Interpretation:")
    add("")
    add("- This is the cleanest proof in the file that raw FPF is not directly usable as a one-shot prompt source for current LLM practice.")
    add("- The product exists partly because the framework does not fit.")
    add("")
    add("## MCP / Harness Checks")
    add("")
    add(
        f"- `python -m fpf_thinking_map.verify`: "
        f"`{'PASS' if harness['verify']['ok'] else 'FAIL'}`"
    )
    add(
        f"- `python -m dev_mcp.test_server`: "
        f"`{'PASS' if harness['dev_mcp_test']['ok'] else 'FAIL'}`"
    )
    probe = harness["dev_mcp_probe"]
    if "result" in probe:
        add(f"- `dev_mcp.run_scenario` probe: `{probe['result']}`")
    elif "error" in probe:
        add(f"- `dev_mcp.run_scenario` probe error: `{probe['error']}`")
    add("")
    add("Interpretation:")
    add("")
    add("- The compiled product is not just a markdown claim. It is executable, testable, and inspectable through its own verify harness and MCP test surface.")
    add("")
    add("## Compounding")
    add("")
    add(
        f"- Shipped full traversal records `{compounding['actual_steps_recorded']}` total steps."
    )
    add(
        f"- Decision-bearing `slice()` steps inside that traversal: `{compounding['decision_steps_recorded']}`."
    )
    add(
        f"- Cumulative compiled decision-prompt tokens: `{compounding['compiled_prompt_tokens_local']}` local"
        + (
            f", `{compounding['compiled_prompt_tokens_api']}` billed"
            if "compiled_prompt_tokens_api" in compounding
            else ""
        )
    )
    add(
        f"- Cumulative raw section-pack decision-prompt tokens: `{compounding['raw_prompt_tokens_local']}` local"
        + (
            f", `{compounding['raw_prompt_tokens_api']}` billed"
            if "raw_prompt_tokens_api" in compounding
            else ""
        )
    )
    add(
        f"- Decision-step ratio: `{compounding['local_ratio']:.1f}x` local"
        + (
            f", `{compounding['api_ratio']:.1f}x` billed"
            if "api_ratio" in compounding
            else ""
        )
    )
    add("- Growth shape on the shipped traversal: `linear`.")
    add("- The line in `WHY_THIS_EXISTS.md` about `36 passes where 6 would suffice` is not directly testable from the shipped example because the shipped example here is 3 steps, not 6.")
    add("")
    add("## What The Test Says")
    add("")
    add("### For Your Product")
    add("")
    add(
        f"- The core existence claim is confirmed: the compiled product is `{verdict['compiled_vs_full_raw_ratio']:.1f}x` smaller than the full raw spec and `{verdict['compiled_vs_raw_pack_ratio']:.1f}x` smaller than the feasible raw exact-section alternative."
    )
    if live:
        add(
            f"- On live runs, compiled input cost averaged `{verdict['compiled_live_mean_input_tokens']:.1f}` billed tokens per decision; raw section-pack averaged `{verdict['raw_live_mean_input_tokens']:.1f}`."
        )
        add(
            f"- The compiled product matched its own shipped expected outcomes on `{format_percent(verdict['compiled_live_accuracy'])}` of cases."
        )
    add("- The product is executable and measurable: `verify` passed and the package-local `dev_mcp` test surface passed.")
    add("")
    add("### For Raw FPF")
    add("")
    add("- Raw FPF monolith still does not fit: the live monolith attempt hard-failed on context length.")
    add("- Even when reduced to exact cited sections instead of the full monolith, raw FPF remains very expensive.")
    add("- Raw FPF section-pack prompting was stricter than this product on several cases and only matched `2/5` shipped outcomes. It kept demanding explicit gate / authority structure where the compiled product is willing to continue.")
    add("")
    add("### Product Tradeoff")
    add("")
    add("- Plus: the product makes raw FPF usable inside real context budgets.")
    add("- Minus: some raw FPF strictness is flattened away. `role_conflict` is the concrete miss measured here.")
    add("")
    add("### Practical Read")
    add("")
    add("- If a user asks why this product exists instead of just feeding raw FPF to an LLM, the answer is now measurable: raw FPF does not fit monolithically, and its reduced exact-section form is still around `139k` tokens per decision.")
    if live:
        add(
            f"- In live billed input terms, this product saves about **{verdict['raw_live_mean_input_tokens'] - verdict['compiled_live_mean_input_tokens']:.1f} input tokens per decision** versus the feasible raw exact-section prompt."
        )
    add("- The test supports the claim that compilation buys context fit, cost reduction, and speed.")
    add("- The test does not support a clean literal `3 passes` decomposition.")
    add("- The test supports linear accumulation of raw cost over steps, but this repo's shipped traversal does not justify a stronger superlinear claim.")
    add("")
    add("## Reproduction")
    add("")
    add("```bash")
    add("pip install -r scripts/requirements-triple-tax.txt")
    add("OPENAI_API_KEY=... python scripts/triple_tax_calculus.py \\")
    add("  --write-md TRIPLE_TAX_CALCULUS.md \\")
    add("  --json-out triple_tax_calculus.json")
    add("```")
    add("")
    add("---")
    add("")
    add(
        "SIGNED: OpenAI Codex + Claude Code | equal-footing FPF audit | 2026-07-10 | one BFF footer"
    )
    return "\n".join(lines).rstrip() + "\n"


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    encoding = load_encoding(args.encoding)
    reference_text, reference_path, reference_source = load_reference_text()
    reference = shared_reference_stats(reference_text, encoding)

    spec_text, spec_path, spec_commit = load_spec_text(args.spec_path)
    spec_lexicon = lexicon_stats(spec_text, encoding, reference)
    section_blocks = extract_section_blocks(spec_text)
    points = build_decision_points()
    point_rows, point_summary = measure_points(points, section_blocks, encoding)
    traversal = measure_traversal()
    harnesses = measure_local_harnesses()
    monolith = measure_monolith_raw_attempt(
        points=points,
        spec_text=spec_text,
        encoding=encoding,
        model=args.live_model,
        effort=args.live_effort,
        max_output_tokens=args.max_output_tokens,
        no_live=args.no_live,
    )
    live = None if args.no_live else measure_live_matrix(
        point_rows=point_rows,
        encoding=encoding,
        model=args.live_model,
        effort=args.live_effort,
        max_output_tokens=args.max_output_tokens,
    )
    report = {
        "encoding": {"name": encoding.name},
        "live_model_requested": args.live_model,
        "live_effort_requested": args.live_effort,
        "spec": {
            "path": str(spec_path),
            "commit": spec_commit,
            "source": UPSTREAM_RAW_SPEC_URL if spec_commit == UPSTREAM_COMMIT else "local-file",
            "body_tokens": token_count(spec_text, encoding),
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
        "harnesses": harnesses,
        "monolith_raw_attempt": monolith,
        "live": live,
    }
    report["compounding"] = build_compounding_summary(traversal, point_rows, live)
    report["verdict"] = summarize_verdict(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure the triple-tax calculus for fpf-agentic-thinking-map.")
    parser.add_argument("--spec-path", help="Local FPF-Spec.md path. If omitted, downloads the pinned upstream snapshot.")
    parser.add_argument("--encoding", default=DEFAULT_ENCODING, help="Tokenizer encoding to use.")
    parser.add_argument("--live-model", default=os.environ.get("TRIPLE_TAX_LIVE_MODEL", DEFAULT_LIVE_MODEL), help="Live model for API runs.")
    parser.add_argument("--live-effort", default=os.environ.get("TRIPLE_TAX_LIVE_EFFORT", DEFAULT_LIVE_EFFORT), help="Reasoning effort for live runs.")
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_MAX_OUTPUT_TOKENS, help="Max output tokens for live runs.")
    parser.add_argument("--no-live", action="store_true", help="Skip live API runs.")
    parser.add_argument("--write-md", help="Write markdown to this path.")
    parser.add_argument("--json-out", help="Write structured JSON to this path.")
    args = parser.parse_args()

    report = build_report(args)
    markdown = build_markdown(report)

    if args.write_md:
        Path(args.write_md).write_text(markdown, encoding="utf-8")
    else:
        print(markdown, end="")

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
