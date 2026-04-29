from typing import Dict

def handle_sales() -> Dict:
    return {
        "reply": "Let me connect you to sales.",
        "office_execution": {
            "mode": "sales_handler_v1",
            "target": "SALES"
        }
    }