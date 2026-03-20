from flask import Flask, request, jsonify
from intake import handle_project_intake
from processor import generate_project_output
from models import NormalizedIntake

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.post("/intake")
def intake():
    payload = request.get_json(silent=True) or {}
    intake_result = handle_project_intake(payload)

    if intake_result.get("status") != "ok":
        return jsonify(intake_result), 400

    normalized = NormalizedIntake(**intake_result["normalized"])
    output = generate_project_output(normalized)
    return jsonify(output), 200


if __name__ == "__main__":
    app.run(debug=True)
