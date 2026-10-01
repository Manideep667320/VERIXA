# HELP-POLICY — Policy evaluation

The active, versioned `policy/rules.yaml` determines which actions are permitted, their risk, approval requirements, and decision thresholds. The current action rules are generated from that policy file:

{{POLICY_ACTIONS}}

Policy checks are deterministic. A denied action or insufficient, missing, or conflicting evidence prevents autonomous execution.
