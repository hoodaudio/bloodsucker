import os
import requests
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from functools import wraps

app = Flask(__name__)
CORS(app, origins="*", methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type", "x-api-key"])

# Read environment variables
API_KEY = os.getenv("BACKEND_API_KEY")
LALAL_API_KEY = os.getenv("LALAL_API_KEY")

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        client_key = request.headers.get("X-API-KEY")
        if not client_key or client_key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route("/test", methods=["GET"])
def test():
    return jsonify({"message": "API is live"})

@app.route("/split", methods=["POST"])
@require_api_key
def split():
    if 'audio_file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    audio_file = request.files['audio_file']
    if audio_file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    print(f"Received file: {audio_file.filename}")

    try:
        # Upload the file to LALAL.ai
        response = requests.post(
            "https://api.lalal.ai/v1/extract/",
            headers={"Authorization": f"Token {LALAL_API_KEY}"},
            files={"file": (audio_file.filename, audio_file.stream, audio_file.mimetype)}
        )

        response.raise_for_status()
        data = response.json()

        job_id = data.get("id")
        if job_id:
            return jsonify({
                "job_id": job_id,
                "status": "processing",
                "message": f"File sent to LALAL.ai for processing"
            })
        else:
            return jsonify({"error": "Failed to retrieve job ID"}), 500

    except requests.exceptions.RequestException as e:
        print(f"Error sending file to LALAL.ai: {e}")
        return jsonify({"error": "Failed to send file to LALAL.ai"}), 500

@app.route("/results/<job_id>", methods=["GET"])
@require_api_key
def results(job_id):
    try:
        response = requests.get(
            f"https://api.lalal.ai/v1/result/{job_id}/",
            headers={"Authorization": f"Token {LALAL_API_KEY}"}
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "done":
            stems = data.get("result", {})
            return jsonify({
                "status": "done",
                "vocal_link": stems.get("vocals"),
                "instrumental_link": stems.get("instrumental")
            })
        elif data.get("status") == "processing":
            return jsonify({"status": "processing"})
        else:
            return jsonify({"status": data.get("status"), "message": data.get("message")}), 202
    except requests.exceptions.RequestException as e:
        print(f"Error fetching results: {e}")
        return jsonify({"error": "Failed to fetch results from LALAL.ai"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
