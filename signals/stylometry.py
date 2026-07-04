
import re
import statistics


def _split_sentences(text: str) -> list:
    # Simple sentence splitter on ., !, ? followed by whitespace or end of string.
    sentences = re.split(r'[.!?]+(?:\s+|$)', text.strip())
    return [s for s in sentences if s.strip()]


def _sentence_length_variance_score(text: str) -> float:
    """
    Measures variance in sentence length (word count per sentence).
    Human writing tends to vary sentence length more; AI text tends to be
    more uniform. Low variance -> higher AI-likelihood score.

    Calibrated against real measured variance across test samples, which
    ranged roughly 20 (more uniform) to 45 (more variable) on short
    3-5 sentence passages.
    """
    sentences = _split_sentences(text)
    if len(sentences) < 2:
        # Not enough sentences to measure variance reliably.
        return 0.5

    lengths = [len(s.split()) for s in sentences]
    variance = statistics.pvariance(lengths)

    # Map variance 15 (very uniform, AI-likely) to 50 (highly variable,
    # human-likely) onto a 1.0 to 0.0 score.
    score = max(0.0, min(1.0, 1.0 - ((variance - 15) / 35)))
    return score


def _type_token_ratio_score(text: str) -> float:
    """
    Measures vocabulary diversity: unique words / total words.
    On short passages (under ~30 words), this ratio clusters tightly near
    0.85-0.90 regardless of authorship, since there's little chance for
    repetition either way. This is a known blind spot: TTR is only a
    reliable AI/human indicator on longer text where genuine repetition
    patterns can emerge. It remains a comparatively weak signal at short
    text lengths.
    Lower ratio -> higher AI-likelihood score (more repetitive/uniform).
    """
    words = re.findall(r"\b\w+\b", text.lower())
    if len(words) < 5:
        return 0.5

    unique_words = set(words)
    ratio = len(unique_words) / len(words)

    # Map ratio 0.5 (repetitive, AI-likely) to 1.0 (fully diverse,
    # human-likely) onto a 1.0 to 0.0 score.
    score = max(0.0, min(1.0, 1.0 - ((ratio - 0.5) / 0.5)))
    return score


def _punctuation_density_score(text: str) -> float:
    """
    Measures density of punctuation marks relative to text length.
    Higher density of connective punctuation (commas, semicolons, dashes)
    suggests more complex, formally structured sentences, leaning
    AI-likely. This is the weakest and most blind-spot-prone of the three
    metrics on its own, since plenty of human writing also uses dense
    punctuation and plenty of AI writing doesn't.
    """
    if len(text) == 0:
        return 0.5

    punctuation_marks = re.findall(r"[,;:\-\u2014()\"']", text)
    density = len(punctuation_marks) / len(text)

    # Map density 0 (sparse, human-likely) to 0.03 (dense, AI-likely)
    # onto a 0.0 to 1.0 score.
    score = max(0.0, min(1.0, density / 0.03))
    return score


def get_stylometry_signal(text: str) -> dict:
    """
    Signal 2: Stylometric heuristics (pure Python, no external libraries).

    Combines three structural metrics into a single 0-1 AI-likelihood score:
        - sentence length variance
        - type-token ratio (vocabulary diversity)
        - punctuation density

    Returns a dict:
        {
            "score": float,  # 0.0 - 1.0, combined AI-likelihood score
            "metrics": {
                "sentence_length_variance_score": float,
                "type_token_ratio_score": float,
                "punctuation_density_score": float
            }
        }

    Blind spot: naturally uniform formal/technical human writing can score
    similarly to AI text. Short text samples don't give enough data for
    these metrics to be reliable.
    """
    sentence_score = _sentence_length_variance_score(text)
    ttr_score = _type_token_ratio_score(text)
    punctuation_score = _punctuation_density_score(text)

    combined_score = (sentence_score + ttr_score + punctuation_score) / 3.0

    return {
        "score": round(combined_score, 3),
        "metrics": {
            "sentence_length_variance_score": round(sentence_score, 3),
            "type_token_ratio_score": round(ttr_score, 3),
            "punctuation_density_score": round(punctuation_score, 3)
        }
    }


if __name__ == "__main__":
    # Quick standalone test. Run with: python signals/stylometry.py
    test_inputs = {
        "Clearly AI-generated": (
            "Artificial intelligence represents a transformative paradigm shift in "
            "modern society. It is important to note that while the benefits of AI "
            "are numerous, it is equally essential to consider the ethical "
            "implications. Furthermore, stakeholders across various sectors must "
            "collaborate to ensure responsible deployment."
        ),
        "Clearly human-written": (
            "ok so i finally tried that new ramen place downtown and honestly? "
            "underwhelming. the broth was fine but they put WAY too much sodium in "
            "it and i was thirsty for like three hours after. my friend got the "
            "spicy version and said it was better. probably won't go back unless "
            "someone drags me there"
        ),
        "Borderline: formal human writing": (
            "The relationship between monetary policy and asset price inflation "
            "has been extensively studied in the literature. Central banks face a "
            "fundamental tension between their mandate for price stability and the "
            "unintended consequences of prolonged low interest rates on equity and "
            "real estate valuations."
        ),
        "Borderline: lightly edited AI output": (
            "I've been thinking a lot about remote work lately. There are genuine "
            "tradeoffs, flexibility and no commute on one side, isolation and "
            "blurred work-life boundaries on the other. Studies show productivity "
            "varies widely by individual and role type."
        ),
    }

    for label, text in test_inputs.items():
        result = get_stylometry_signal(text)
        print(f"{label}:")
        print(f"  Combined score: {result['score']}")
        print(f"  Metrics: {result['metrics']}")
        print()