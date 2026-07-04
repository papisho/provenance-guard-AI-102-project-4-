
from scoring import get_attribution

LABEL_HIGH_AI = (
    "This content shows strong indicators of AI generation based on our analysis. "
    "If you believe this is a mistake, you can appeal this classification."
)

LABEL_UNCERTAIN = (
    "Our system could not confidently determine whether this content was "
    "AI-generated or human-written. This result reflects genuine uncertainty "
    "in the analysis."
)

LABEL_HIGH_HUMAN = (
    "This content shows strong indicators of human authorship based on our analysis."
)


def get_label(confidence: float) -> str:
    """
    Maps a confidence score to the exact transparency label text, using the
    same threshold bands as scoring.get_attribution, so the label always
    matches the attribution category returned to the user.
    """
    attribution = get_attribution(confidence)

    if attribution == "likely_ai":
        return LABEL_HIGH_AI
    elif attribution == "likely_human":
        return LABEL_HIGH_HUMAN
    else:
        return LABEL_UNCERTAIN


if __name__ == "__main__":
    # Quick standalone check that all three variants are reachable.
    test_scores = [0.9, 0.5, 0.1]
    for score in test_scores:
        print(f"confidence={score} -> {get_label(score)}")
        print()