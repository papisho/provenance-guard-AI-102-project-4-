
from audit_log import get_all_entries


def compute_analytics() -> dict:
    """
    Stretch feature: analytics dashboard.

    Reads every entry in the audit log and computes:
        - detection_patterns: count of submissions per attribution category
        - appeal_rate: appeals filed / total submissions
        - average_confidence: mean confidence score across all submissions
    """
    entries = get_all_entries()
    total = len(entries)

    if total == 0:
        return {
            "total_submissions": 0,
            "detection_patterns": {
                "likely_ai": 0,
                "uncertain": 0,
                "likely_human": 0
            },
            "appeal_rate": 0.0,
            "average_confidence": 0.0
        }

    detection_patterns = {
        "likely_ai": 0,
        "uncertain": 0,
        "likely_human": 0
    }
    appeal_count = 0
    confidence_sum = 0.0

    for entry in entries:
        attribution = entry.get("attribution")
        if attribution in detection_patterns:
            detection_patterns[attribution] += 1

        if entry.get("status") == "under_review":
            appeal_count += 1

        confidence_sum += entry.get("confidence", 0.0)

    return {
        "total_submissions": total,
        "detection_patterns": detection_patterns,
        "appeal_rate": round(appeal_count / total, 3),
        "average_confidence": round(confidence_sum / total, 3)
    }