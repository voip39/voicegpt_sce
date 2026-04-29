from typing import Dict

def handle_human() -> Dict:
    return {
        "reply": "Let me connect you to someone who can help you.",
        "office_execution": {
            "mode": "human_desk_handler_v1",
            "target": "HUMAN_DESK"
        }
    }