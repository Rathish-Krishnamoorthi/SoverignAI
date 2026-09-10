def verify_threshold(measured: float, limit: float) -> dict:
    exceeds = measured > limit
    return {
        "measured": measured,
        "limit": limit,
        "operator": ">",
        "expression": f"{measured} > {limit}",
        "result": exceeds,
        "status": "EXCEEDS_LIMIT" if exceeds else "WITHIN_LIMIT",
        "verified_by": "Python",
    }

