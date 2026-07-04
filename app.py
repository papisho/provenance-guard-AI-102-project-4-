
import uuid
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from signals.llm_signal import get_llm_signal
from signals.stylometry import get_stylometry_signal
from scoring import compute_confidence, get_attribution
from labels import get_label
from audit_log import log_entry, current_timestamp, get_log, find_entry_by_content_id, update_entry_status

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)


@app.route("/submit", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
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

    # Transparency label matching the confidence-based attribution category.
    label = get_label(confidence)

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


@app.route("/appeal", methods=["POST"])
def appeal():
    data = request.get_json(silent=True) or {}
    content_id = data.get("content_id")
    creator_reasoning = data.get("creator_reasoning")

    if not content_id or not creator_reasoning:
        return jsonify({"error": "content_id and creator_reasoning are required"}), 400

    existing_entry = find_entry_by_content_id(content_id)
    if existing_entry is None:
        return jsonify({"error": f"No submission found with content_id {content_id}"}), 404

    updated = update_entry_status(
        content_id=content_id,
        status="under_review",
        appeal_reasoning=creator_reasoning,
        appeal_timestamp=current_timestamp()
    )

    if not updated:
        return jsonify({"error": "Failed to update entry"}), 500

    return jsonify({
        "content_id": content_id,
        "status": "under_review",
        "message": "Your appeal has been received and is under review."
    })


@app.route("/log", methods=["GET"])
def get_log_entries():
    return jsonify({"entries": get_log()})


if __name__ == "__main__":
    app.run(debug=True)