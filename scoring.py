
# Weights for combining Signal 1 (LLM) and Signal 2 (stylometrics).
# Signal 1 is weighted more heavily since it captures holistic meaning;
# Signal 2 acts as a supporting structural check. See planning.md.
SIGNAL_1_WEIGHT = 0.6
SIGNAL_2_WEIGHT = 0.4

# Threshold bands. Deliberately asymmetric: it takes a higher score to
# reach "likely_ai" than it does to reach "likely_human", reflecting that
# a false positive (accusing a human of AI use) is worse than a false
# negative on a creative writing platform. See planning.md.
LIKELY_AI_THRESHOLD = 0.75
LIKELY_HUMAN_THRESHOLD = 0.35


def compute_confidence(signal_1_score: float, signal_2_score: float) -> float:
    """
    Combines the two signal scores into a single confidence score (0-1)
    using a weighted average.
    """
    combined = (SIGNAL_1_WEIGHT * signal_1_score) + (SIGNAL_2_WEIGHT * signal_2_score)
    return round(max(0.0, min(1.0, combined)), 3)


def get_attribution(confidence: float) -> str:
    """
    Maps a confidence score to one of three attribution categories using
    the asymmetric threshold bands defined in planning.md:
        0.75 - 1.0  -> likely_ai
        0.35 - 0.74 -> uncertain
        0.0  - 0.34 -> likely_human
    """
    if confidence >= LIKELY_AI_THRESHOLD:
        return "likely_ai"
    elif confidence >= LIKELY_HUMAN_THRESHOLD:
        return "uncertain"
    else:
        return "likely_human"


if __name__ == "__main__":
    # Quick standalone sanity check using signal scores we already measured
    # for our 4 test inputs (Signal 1 scores are illustrative estimates
    # for the borderline cases, since we only tested Signal 1 on the
    # clearly-AI and clearly-human samples so far).
    test_cases = {
        "Clearly AI-generated": (0.8, 0.343),
        "Clearly human-written": (0.2, 0.167),
        "Borderline: formal human writing": (0.55, 0.281),
        "Borderline: lightly edited AI output": (0.55, 0.532),
    }

    for label, (s1, s2) in test_cases.items():
        confidence = compute_confidence(s1, s2)
        attribution = get_attribution(confidence)
        print(f"{label}:")
        print(f"  signal_1={s1}, signal_2={s2} -> confidence={confidence} -> {attribution}")
        print()