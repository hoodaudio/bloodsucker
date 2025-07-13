import os
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from functools import wraps

app = Flask(__name__)
CORS(app)

# Read the secret key from environment variable
API_KEY = os.getenv("BACKEND_API_KEY")

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

    # TODO: Call LALAL.ai API here with audio_file

    return jsonify({
        "job_id": "mock123",
        "status": "processing",
        "message": f"Received {audio_file.filename}, processing started"
    })

@app.route("/results/<job_id>", methods=["GET"])
@require_api_key
def results(job_id):
    # TODO: Fetch real results from LALAL.ai by job_id
    return jsonify({
        "status": "done",
        "vocal_link": "https://example.com/vocals.wav",
        "instrumental_link": "https://example.com/instrumental.wav"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
