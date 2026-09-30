import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { delimiter, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const projectRoot = resolve(fileURLToPath(new URL("../..", import.meta.url)));
const backendRoot = resolve(projectRoot, "backend");

const backendChecks = [
  {
    name: "shadow mode records its recommendation without ticket or technician writes",
    nodeId: "tests/test_shadow.py::test_shadow_mode_blocks_ticket_and_technician_writes",
  },
  {
    name: "policy simulation reports decisions changed by a candidate threshold",
    nodeId: "tests/test_policy_versions.py::test_candidate_threshold_replay_returns_only_changed_runs",
  },
  {
    name: "failed verification rolls back and escalates",
    nodeId: "tests/test_phase10_executor.py::test_failed_verification_rolls_back_immediately_and_escalates",
  },
  {
    name: "the seeded document conflict forces escalation",
    nodeId: "tests/test_phase13_insights.py::test_seeded_conflict_is_attached_to_evidence_and_forces_escalation",
  },
  {
    name: "analytics totals match the known scenario run count",
    nodeId: "tests/test_analytics.py::test_summary_metrics_match_hand_calculated_twenty_run_fixture",
  },
  {
    name: "the audit chain verifies after the scenario checks",
    nodeId: "tests/test_audit_chain.py::test_untouched_chain_and_verify_endpoint_pass",
  },
];

for (const { name, nodeId } of backendChecks) {
  test(name, () => {
    const python = process.env.PYTHON ?? "py";
    const pythonArgs = process.env.PYTHON
      ? []
      : process.platform === "win32"
        ? ["-3.11"]
        : [];
    const pythonPath = [backendRoot, process.env.PYTHONPATH]
      .filter(Boolean)
      .join(delimiter);
    const result = spawnSync(
      python,
      [...pythonArgs, "-m", "pytest", "-q", nodeId],
      {
        cwd: backendRoot,
        encoding: "utf8",
        env: { ...process.env, PYTHONPATH: pythonPath },
      },
    );

    assert.equal(
      result.error,
      undefined,
      `Could not start backend pytest runner: ${result.error?.message ?? "unknown error"}`,
    );
    assert.equal(
      result.status,
      0,
      [result.stdout, result.stderr].filter(Boolean).join("\n"),
    );
  });
}
