
import uuid
from flask import Flask, request, jsonify
from signals.llm_signal import get_llm_signal
from signals.stylometry import get_stylometry_signal
from scoring import compute_confidence, get_attribution
from audit_log import log_entry, current_timestamp, get_log

app = Flask(__name__)


@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json(silent=True) or {}
    text = data.get("text")
    creator_id = data.get("creator_id")

    if not text or not creator_id:
        return jsonify({"error": "text and creator_id are required"}), 400

    content_id = str(uuid.uuid4())

    # Signal 1: Groq LLM classification
    signal_1_result = get_llm_signal(text)
    signal_1_score = signal_1_result["score"]

    # Signal 2: stylometric heuristics
    signal_2_result = get_stylometry_signal(text)
    signal_2_score = signal_2_result["score"]

    # Real combined confidence scoring and attribution (weighted average +
    # asymmetric thresholds, see planning.md and scoring.py).
    confidence = compute_confidence(signal_1_score, signal_2_score)
    attribution = get_attribution(confidence)

    # Placeholder label. Real transparency label logic arrives in Milestone 5.
    label = "placeholder label, real transparency label logic coming in Milestone 5"

    # Write structured audit log entry for this submission.
    log_entry({
        "content_id": content_id,
        "creator_id": creator_id,
        "timestamp": current_timestamp(),
        "attribution": attribution,
        "confidence": confidence,
        "signal_1_score": signal_1_score,
        "signal_2_score": signal_2_score,
        "status": "classified"
    })

    return jsonify({
        "content_id": content_id,
        "attribution": attribution,
        "confidence": confidence,
        "label": label,
        "signal_1_score": signal_1_score,
        "signal_1_reasoning": signal_1_result["reasoning"],
        "signal_2_score": signal_2_score,
        "signal_2_metrics": signal_2_result["metrics"]
    })


@app.route("/log", methods=["GET"])
def get_log_entries():
    return jsonify({"entries": get_log()})


if __name__ == "__main__":
    app.run(debug=True)