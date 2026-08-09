#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from typing import Any

import yaml

VERSION = "0.1.0"
PASS = 0
TOOL_FAILURE = 2


class EvaluatorError(RuntimeError):
    pass


def load_yaml(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise EvaluatorError(f"{label} must be a regular file: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise EvaluatorError(f"cannot parse {label}: {exc}") from exc
    if not isinstance(data, dict):
        raise EvaluatorError(f"{label} root must be a mapping")
    return data


def find_current_step(route: dict[str, Any], step_id: str) -> tuple[int, dict[str, Any]]:
    steps = route.get("steps")
    if not isinstance(steps, list):
        raise EvaluatorError("route.steps must be a list")
    matches = [(i, step) for i, step in enumerate(steps) if isinstance(step, dict) and step.get("step_id") == step_id]
    if len(matches) != 1:
        raise EvaluatorError(f"current_step_id must identify exactly one route step: {step_id}")
    return matches[0]


def find_runtime_node(spec: dict[str, Any], step: dict[str, Any]) -> dict[str, Any] | None:
    nodes = spec.get("nodes")
    if not isinstance(nodes, list):
        return None
    matches = [node for node in nodes if isinstance(node, dict) and (node.get("node_id") == step.get("step_id") or node.get("name") in {step.get("step_id"), step.get("task_name")})]
    return matches[0] if len(matches) == 1 else None


def skill_name(ref: Any) -> str | None:
    return ref.get("skill_name") if isinstance(ref, dict) else None


def result_skill_names(result: dict[str, Any]) -> tuple[str | None, str | None]:
    op = result.get("operation_result")
    val = result.get("validation_result")
    return (op.get("skill_name") if isinstance(op, dict) else None, val.get("skill_name") if isinstance(val, dict) else None)


def validate_context(ctx: dict[str, Any]) -> None:
    required = {
        "schema_version", "current_step_id", "task_id", "gate_status", "artifact_interface_status",
        "artifact_lineage_status", "route_affecting_evidence", "conditional_evidence_changed",
        "unexpected_output", "user_instruction_changed", "recovery_status", "high_risk_barrier",
        "next_inputs_status", "next_condition_status",
    }
    missing = required - set(ctx)
    if missing:
        raise EvaluatorError(f"evaluation context missing fields: {sorted(missing)}")
    if ctx["schema_version"] != 1:
        raise EvaluatorError("unsupported evaluation context schema_version")
    if not isinstance(ctx["current_step_id"], str) or not ctx["current_step_id"]:
        raise EvaluatorError("current_step_id must be a non-empty string")
    if not isinstance(ctx["task_id"], str) or not ctx["task_id"]:
        raise EvaluatorError("task_id must be a non-empty string")
    if ctx["gate_status"] not in {"PASS", "FAIL", "UNKNOWN"}:
        raise EvaluatorError("gate_status is invalid")
    if ctx["artifact_interface_status"] not in {"MATCH", "MISMATCH", "UNKNOWN"}:
        raise EvaluatorError("artifact_interface_status is invalid")
    if ctx["artifact_lineage_status"] not in {"OK", "CONFLICT", "UNKNOWN"}:
        raise EvaluatorError("artifact_lineage_status is invalid")
    if ctx["recovery_status"] not in {"NONE", "PROJECT", "WORKSTREAM"}:
        raise EvaluatorError("recovery_status is invalid")
    if ctx["next_inputs_status"] not in {"READY", "BLOCKED", "UNKNOWN"}:
        raise EvaluatorError("next_inputs_status is invalid")
    if ctx["next_condition_status"] not in {"NOT_APPLICABLE", "TRUE", "FALSE", "UNKNOWN"}:
        raise EvaluatorError("next_condition_status is invalid")
    for key in ("route_affecting_evidence", "conditional_evidence_changed", "unexpected_output", "user_instruction_changed", "high_risk_barrier"):
        if not isinstance(ctx[key], bool):
            raise EvaluatorError(f"{key} must be boolean")


def outcome(decision: str, route: dict[str, Any], ctx: dict[str, Any], reasons: list[str], current: dict[str, Any] | None = None, next_step: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "status": "PASS",
        "decision": decision,
        "route_id": route.get("route_id"),
        "workstream_id": route.get("workstream_id"),
        "task_id": ctx.get("task_id"),
        "from_step_id": current.get("step_id") if isinstance(current, dict) else ctx.get("current_step_id"),
        "to_step_id": next_step.get("step_id") if isinstance(next_step, dict) else None,
        "next_route_position": ({"workflow_name": next_step.get("workflow_name"), "substep": next_step.get("task_name") or next_step.get("step_id"), "task_id": None} if decision == "ADVANCE" and isinstance(next_step, dict) else None),
        "evaluator_version": VERSION,
        "reason_codes": reasons,
    }


def evaluate(route: dict[str, Any], state: dict[str, Any], result: dict[str, Any], spec: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    validate_context(ctx)
    if route.get("route_id") != state.get("active_route_id") or route.get("workstream_id") != state.get("workstream_id"):
        return outcome("BLOCKED", route, ctx, ["ACTIVE_ROUTE_STATE_IDENTITY_CONFLICT"])
    if result.get("task_id") != ctx["task_id"] or result.get("workstream_id") != route.get("workstream_id"):
        return outcome("BLOCKED", route, ctx, ["TASK_RESULT_IDENTITY_CONFLICT"])

    try:
        index, current = find_current_step(route, ctx["current_step_id"])
    except EvaluatorError:
        return outcome("BLOCKED", route, ctx, ["CURRENT_ROUTE_NODE_NOT_UNIQUE"])

    position = state.get("current_position")
    if not isinstance(position, dict) or position.get("workflow_name") != current.get("workflow_name") or position.get("substep") not in {current.get("step_id"), current.get("task_name")}:
        return outcome("BLOCKED", route, ctx, ["WORKSTREAM_POSITION_ROUTE_CONFLICT"], current=current)
    if position.get("task_id") not in (None, ctx["task_id"]):
        return outcome("BLOCKED", route, ctx, ["WORKSTREAM_TASK_IDENTITY_CONFLICT"], current=current)
    if result.get("task_unit_mode") != current.get("task_unit_mode"):
        return outcome("BLOCKED", route, ctx, ["TASK_MODE_ROUTE_CONFLICT"], current=current)

    runtime_node = find_runtime_node(spec, current)
    if runtime_node is None:
        return outcome("REENTER_WORKFLOW", route, ctx, ["COMPACT_RUNTIME_NODE_UNAVAILABLE"], current=current)
    if runtime_node.get("logical_mode") != current.get("task_unit_mode"):
        return outcome("REENTER_WORKFLOW", route, ctx, ["ROUTE_RUNTIME_SPEC_MISMATCH"], current=current)
    route_op, route_val = skill_name(current.get("operation")), skill_name(current.get("validator"))
    result_op, result_val = result_skill_names(result)
    if route_op != result_op or route_val != result_val:
        return outcome("BLOCKED", route, ctx, ["TASK_SKILL_IDENTITY_CONFLICT"], current=current)

    if ctx["recovery_status"] != "NONE" or ctx["artifact_lineage_status"] != "OK":
        reasons = ["RECOVERY_ACTIVE"] if ctx["recovery_status"] != "NONE" else ["ARTIFACT_LINEAGE_NOT_INTERPRETABLE"]
        return outcome("BLOCKED", route, ctx, reasons, current=current)

    semantic_reasons: list[str] = []
    if result.get("status") != "DONE":
        semantic_reasons.append("TASK_TERMINAL_STATUS_REQUIRES_SEMANTIC_REENTRY")
    if result.get("failure") is not None:
        semantic_reasons.append("FAILURE_PRESENT")
    confirmations = result.get("confirmation_items")
    if isinstance(confirmations, list) and confirmations:
        semantic_reasons.append("CONFIRMATION_ITEMS_PRESENT")
    if ctx["gate_status"] != "PASS":
        semantic_reasons.append("GATE_NOT_PASS")
    if ctx["artifact_interface_status"] != "MATCH":
        semantic_reasons.append("ARTIFACT_INTERFACE_NOT_CONFIRMED")
    if ctx["route_affecting_evidence"]:
        semantic_reasons.append("ROUTE_AFFECTING_EVIDENCE")
    if ctx["conditional_evidence_changed"]:
        semantic_reasons.append("CONDITIONAL_EVIDENCE_CHANGED")
    if ctx["unexpected_output"]:
        semantic_reasons.append("UNEXPECTED_OUTPUT")
    if ctx["user_instruction_changed"]:
        semantic_reasons.append("USER_INSTRUCTION_CHANGED")
    if ctx["high_risk_barrier"]:
        semantic_reasons.append("HIGH_RISK_BARRIER")
    if semantic_reasons:
        return outcome("REENTER_WORKFLOW", route, ctx, semantic_reasons, current=current)

    steps = route["steps"]
    if index == len(steps) - 1:
        if route.get("planning_status") == "PARTIAL" and route.get("known_blockers"):
            return outcome("BLOCKED", route, ctx, ["PARTIAL_ROUTE_BOUNDARY_BLOCKED"], current=current)
        return outcome("STOP_SCOPE", route, ctx, ["ACTIVE_ROUTE_SCOPE_END_REACHED"], current=current)

    next_step = steps[index + 1]
    if not isinstance(next_step, dict):
        return outcome("BLOCKED", route, ctx, ["NEXT_ROUTE_NODE_INVALID"], current=current)
    next_runtime = find_runtime_node(spec, next_step)
    if next_runtime is None:
        return outcome("REENTER_WORKFLOW", route, ctx, ["NEXT_COMPACT_RUNTIME_NODE_UNAVAILABLE"], current=current, next_step=next_step)
    if ctx["next_inputs_status"] != "READY":
        return outcome("REENTER_WORKFLOW", route, ctx, ["NEXT_NODE_INPUTS_NOT_READY"], current=current, next_step=next_step)
    necessity = next_step.get("necessity")
    if necessity == "CONDITIONAL":
        if ctx["next_condition_status"] != "TRUE":
            return outcome("REENTER_WORKFLOW", route, ctx, ["CONDITIONAL_NEXT_NODE_REQUIRES_WORKFLOW_DECISION"], current=current, next_step=next_step)
    elif necessity == "REQUIRED":
        if ctx["next_condition_status"] != "NOT_APPLICABLE":
            return outcome("REENTER_WORKFLOW", route, ctx, ["REQUIRED_NODE_CONDITION_CONTEXT_CONFLICT"], current=current, next_step=next_step)
    else:
        return outcome("BLOCKED", route, ctx, ["NEXT_NODE_NECESSITY_INVALID"], current=current, next_step=next_step)

    return outcome("ADVANCE", route, ctx, ["NORMAL_ROUTE_FAST_PATH"], current=current, next_step=next_step)


def run(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    started = time.perf_counter()
    try:
        route = load_yaml(Path(args.route), "route")
        state = load_yaml(Path(args.workstream_state), "workstream state")
        result = load_yaml(Path(args.result), "task result")
        spec = load_yaml(Path(args.runtime_spec), "workflow runtime spec")
        ctx = load_yaml(Path(args.context), "evaluation context")
        payload = evaluate(route, state, result, spec, ctx)
        payload["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 3)
        return PASS, payload
    except Exception as exc:
        return TOOL_FAILURE, {"status": "ERROR", "decision": "BLOCKED", "errors": [str(exc)], "evaluator_version": VERSION, "elapsed_ms": round((time.perf_counter() - started) * 1000, 3)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate deterministic active-route fast path")
    parser.add_argument("--route", required=True)
    parser.add_argument("--workstream-state", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--runtime-spec", required=True)
    parser.add_argument("--context", required=True)
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    code, payload = run(args)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
