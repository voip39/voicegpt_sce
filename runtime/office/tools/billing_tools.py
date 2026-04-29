from typing import Dict


def lookup_invoice_stub() -> Dict:
    return {
        "invoice_id": "INV-1001",
        "amount": 125.00,
        "currency": "USD",
        "status": "due"
    }