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

    try:
        print(f"Received file: {audio_file.filename}")

        lalal_api_key = os.getenv("LALAL_API_KEY")
        files = {"file": (audio_file.filename, audio_file.stream, audio_file.mimetype)}
        data = {"stem_type": "voice"}  # required by LALAL.ai

        headers = {
            "Authorization": f"Token {lalal_api_key}"
        }

        response = requests.post(
            "https://api.lalal.ai/v1/extract/",
            headers=headers,
            files=files,
            data=data
        )
        response.raise_for_status()
        result = response.json()

        return jsonify({
            "job_id": result["id"],
            "status": result["status"]
        })

    except requests.exceptions.RequestException as e:
        print(f"Error sending file to LALAL.ai: {e}")
        return jsonify({"error": "Failed to send to LALAL.ai"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
