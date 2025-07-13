from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/test", methods=["GET"])
def test():
    return jsonify({"message": "API is live"})

@app.route("/split", methods=["POST"])
def mock_split():
    return jsonify({
        "job_id": "mock123",
        "status": "processing",
        "message": "This is a mock response"
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
