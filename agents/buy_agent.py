#!/usr/bin/env python3
import json
import sys
from typing import Any, Dict, List


def simulate_purchases(data: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate purchases for qualifying products (importable API)."""
    purchases: List[Dict[str, Any]] = []
    for p in data.get("products", [])[:2]:
        purchases.append(
            {
                "product": p["name"],
                "retailer": p["retailer"],
                "price": p["price"],
                "success": True,
                "purchase_id": "SIM12345",
            }
        )

    alerts_from_grading = data.get("alerts", [])

    result: Dict[str, Any] = {
        "set_name": data.get("set_name"),
        "purchase_count": len(purchases),
        "purchases": purchases,
        "simulation_mode": True,
    }

    if alerts_from_grading:
        result["alerts"] = alerts_from_grading

    return result


if __name__ == "__main__":
    input_data = sys.stdin.read() or "{}"
    data = json.loads(input_data)
    result = simulate_purchases(data)
    print(json.dumps(result))
