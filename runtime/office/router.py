from __future__ import annotations

from typing import Any, Dict

from runtime.office.handlers.billing import handle_billing
from runtime.office.handlers.sales import handle_sales
from runtime.office.handlers.human_desk import handle_human
from runtime.office.tools_registry import get_allowed_tools


def route_office_handoff(decision: Any) -> Dict[str, Any]:
    office = getattr(decision, "target_office", None) or "FRONTDESK"

    allowed_tools = get_allowed_tools(office)

    if office == "HUMAN_DESK":
        result = handle_human()

    elif office == "BILLING":
        result = handle_billing()

    elif office == "SALES":
        result = handle_sales()

    else:
        result = {
            "reply": "Could you clarify your request?",
            "office_execution": {
                "mode": "office_router_v1",
                "target": office,
            }
        }

    # 🔥 Phase 16E
    result["office_execution"]["allowed_tools"] = allowed_tools

    return result