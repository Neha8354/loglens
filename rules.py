def classify_event(event):
    message = event["message"].lower()

    if (
        "disk full" in message
        or "kernel panic" in message
        or "fatal" in message
        or "service failed" in message
        or "segmentation fault" in message
    ):
        return "CRITICAL", "SYSTEM"

    if (
        "failed password" in message
        or "authentication failure" in message
        or "login failure" in message
    ):
        return "WARNING", "AUTHENTICATION"

    if (
        "timeout" in message
        or "connection refused" in message
        or "warning" in message
    ):
        return "WARNING", "NETWORK"

    if "error" in message or "failed" in message:
        return "ERROR", "APPLICATION"

    if "started" in message or "stopped" in message:
        return "INFO", "SERVICE"

    return "INFO", "GENERAL"


def enrich_event(event):
    severity, category = classify_event(event)

    return {
        **event,
        "severity": severity,
        "category": category,
    }