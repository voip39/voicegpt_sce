from typing import Dict

from runtime.office.tools.billing_tools import lookup_invoice_stub


def handle_billing() -> Dict:
    invoice = lookup_invoice_stub()

    reply = (
        f"I found your invoice {invoice['invoice_id']} "
        f"for {invoice['amount']} {invoice['currency']} "
        f"with status '{invoice['status']}'. "
        "Let me help you proceed with payment."
    )

    return {
        "reply": reply,
        "office_execution": {
            "mode": "billing_handler_v2",
            "target": "BILLING",
            "tool_used": "lookup_invoice",
            "tool_result": invoice,
        }
    }