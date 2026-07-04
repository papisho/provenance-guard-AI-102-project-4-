
import uuid
from flask import Flask, request, jsonify
from signals.llm_signal import get_llm_signal
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

    # Signal 1: Groq LLM classification (real, working)
    signal_1_result = get_llm_signal(text)
    signal_1_score = signal_1_result["score"]

    # Placeholder confidence and attribution using Signal 1 alone.
    # Real combined confidence scoring (Signal 1 + Signal 2) arrives in
    # Milestone 4, along with the real threshold-based attribution logic.
    confidence = signal_1_score
    attribution = "likely_ai" if confidence >= 0.5 else "likely_human"

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
        "status": "classified"
    })

    return jsonify({
        "content_id": content_id,
        "attribution": attribution,
        "confidence": confidence,
        "label": label,
        "signal_1_score": signal_1_score,
        "signal_1_reasoning": signal_1_result["reasoning"]
    })


@app.route("/log", methods=["GET"])
def get_log_entries():
    return jsonify({"entries": get_log()})


if __name__ == "__main__":
    app.run(debug=True)