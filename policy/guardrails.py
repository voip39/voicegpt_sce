from policy.contracts import PolicyDecision


def _read_state_value(state, key: str):
    if isinstance(state, dict):
        return state.get(key)
    return getattr(state, key, None)


def _normalize_skill_call(skill_name_or_decision, arguments=None):
    """
    Поддерживает оба формата:
    1) skill_name_or_decision = "memory_write", arguments = {...}
    2) skill_name_or_decision = {
           "skill_request": {
               "skill_name": "...",
               "arguments": {...}
           }
       }
    3) skill_name_or_decision = {
           "skill_name": "...",
           "arguments": {...}
       }
    """
    if isinstance(skill_name_or_decision, str):
        return skill_name_or_decision, (arguments or {})

    if isinstance(skill_name_or_decision, dict):
        # format: {"skill_request": {"skill_name": "...", "arguments": {...}}}
        skill_request = skill_name_or_decision.get("skill_request")
        if isinstance(skill_request, dict):
            skill_name = skill_request.get("skill_name")
            skill_args = skill_request.get("arguments") or {}
            return skill_name, skill_args

        # format: {"skill_name": "...", "arguments": {...}}
        skill_name = skill_name_or_decision.get("skill_name")
        skill_args = skill_name_or_decision.get("arguments") or {}
        return skill_name, skill_args

    return None, {}


def evaluate_skill_call(state, skill_name: str, arguments: dict | None = None) -> PolicyDecision:
    arguments = arguments or {}

    tenant_kind = _read_state_value(state, "tenant_kind")
    subject_type = _read_state_value(state, "subject_type")

    tenant_policy = tenant_kind or "default"

    # subject-level restrictions
    if skill_name == "send_sms" and subject_type != "user":
        return PolicyDecision(
            allowed=False,
            reason=f"skill '{skill_name}' requires subject_type='user', got '{subject_type}'",
            policy_code="blocked_subject_type",
        )

    if skill_name == "memory_write" and subject_type != "user":
        return PolicyDecision(
            allowed=False,
            reason=f"skill '{skill_name}' requires subject_type='user', got '{subject_type}'",
            policy_code="blocked_subject_type",
        )

    tenant_policy_rules = {
        "default": {
            "allow": {"kb_search", "handoff_request", "memory_write"},
            "block": {"send_sms"},
        },
        "business": {
            "allow": {"kb_search", "handoff_request"},
            "block": {"send_sms", "memory_write"},
        },
        "vip": {
            "allow": {"kb_search", "handoff_request", "send_sms", "memory_write"},
            "block": set(),
        },
    }

    rules = tenant_policy_rules.get(tenant_policy, tenant_policy_rules["default"])

    if skill_name in rules["block"]:
        return PolicyDecision(
            allowed=False,
            reason=f"skill '{skill_name}' is blocked for tenant policy '{tenant_policy}'",
            policy_code="blocked_tenant_policy",
        )

    if skill_name in rules["allow"]:
        return PolicyDecision(
            allowed=True,
            reason=f"skill '{skill_name}' allowed for tenant policy '{tenant_policy}'",
            policy_code="allowed_tenant_policy",
        )

    baseline_allowed = {"kb_search", "handoff_request"}
    baseline_blocked = {"send_sms", "memory_write"}

    if skill_name in baseline_blocked:
        return PolicyDecision(
            allowed=False,
            reason=f"skill '{skill_name}' is blocked by baseline policy",
            policy_code="blocked_baseline",
        )

    if skill_name in baseline_allowed:
        return PolicyDecision(
            allowed=True,
            reason=f"skill '{skill_name}' allowed by baseline policy",
            policy_code="allowed_baseline",
        )

    return PolicyDecision(
        allowed=False,
        reason=f"skill '{skill_name}' is not recognized by policy",
        policy_code="blocked_unknown_skill",
    )


def check_skill_allowed(state, skill_name_or_decision, arguments: dict | None = None) -> PolicyDecision:
    skill_name, normalized_arguments = _normalize_skill_call(skill_name_or_decision, arguments)

    if not skill_name:
        return PolicyDecision(
            allowed=False,
            reason="skill name could not be resolved from policy input",
            policy_code="blocked_invalid_policy_input",
        )

    return evaluate_skill_call(state, skill_name, normalized_arguments)
