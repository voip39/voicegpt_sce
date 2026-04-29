from __future__ import annotations

from typing import Dict, List


OFFICE_TOOLS: Dict[str, List[str]] = {
    "FRONTDESK": [],
    "HUMAN_DESK": [],
    "BILLING": [
        "lookup_invoice",
        "process_payment",
    ],
    "SALES": [
        "crm_lookup",
        "create_lead",
    ],
}


def get_allowed_tools(office: str) -> List[str]:
    return OFFICE_TOOLS.get(office, [])