def status(llm_available: bool) -> dict:
    return {
        "internet_calls": 0,
        "cloud_api_calls": 0,
        "data_egress": 0,
        "external_ai_apis": 0,
        "ocr": "LOCAL",
        "embeddings": "LOCAL",
        "vector_db": "LOCAL",
        "llm": "LOCAL",
        "qwen2_vl": "ACTIVE" if llm_available else "UNAVAILABLE",
        "ollama": "ACTIVE" if llm_available else "UNAVAILABLE",
        "system": "SOVEREIGN / OFFLINE",
    }

