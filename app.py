from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/test", methods=["GET"])
def test():
    return jsonify({"message": "API is live"})

@app.route("/split", methods=["POST"])
def mock_split():
    # Check if file is part of the request
    if 'audio_file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    audio_file = request.files['audio_file']
    if audio_file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # For now, just print file info to server log
    print(f"Received file: {audio_file.filename}")

    # Return a simulated response
    return jsonify({
        "job_id": "mock123",
        "status": "processing",
        "message": f"Received {audio_file.filename}, not sent to LALAL.ai yet"
    })

@app.route("/results/<job_id>", methods=["GET"])
def mock_results(job_id):
    return jsonify({
        "status": "done",
        "vocal_link": "https://example.com/vocals.wav",
        "instrumental_link": "https://example.com/instrumental.wav"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
