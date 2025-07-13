import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

LALAL_API_URL = "https://api.lalal.ai/api/v1"
LALAL_LICENSE_KEY = os.getenv("LALAL_LICENSE_KEY")

if not LALAL_LICENSE_KEY:
    raise RuntimeError("LALAL_LICENSE_KEY environment variable not set")

headers = {
    "Authorization": f"license {LALAL_LICENSE_KEY}"
}

@app.route("/test", methods=["GET"])
def test():
    return jsonify({"message": "API is live"})

@app.route("/split", methods=["POST"])
def split():
    if 'audio_file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    audio_file = request.files['audio_file']
    if audio_file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Upload file to LALAL.ai
    files = {"file": (audio_file.filename, audio_file.stream, audio_file.mimetype)}
    upload_resp = requests.post(f"{LALAL_API_URL}/upload/", headers=headers, files=files)
    if upload_resp.status_code != 200:
        return jsonify({"error": "Upload failed", "details": upload_resp.text}), 500

    upload_data = upload_resp.json()
    job_id = upload_data.get("job_id")
    if not job_id:
        return jsonify({"error": "No job ID received from upload"}), 500

    # Start stem separation job (example: 2 stems, "fast" model)
    split_resp = requests.post(
        f"{LALAL_API_URL}/split/",
        headers=headers,
        json={"job_id": job_id, "model": "fast", "stems": 2}
    )
    if split_resp.status_code != 200:
        return jsonify({"error": "Split start failed", "details": split_resp.text}), 500

    return jsonify({"job_id": job_id, "status": "processing"})

@app.route("/results/<job_id>", methods=["GET"])
def results(job_id):
    check_resp = requests.get(f"{LALAL_API_URL}/check/{job_id}/", headers=headers)
    if check_resp.status_code != 200:
        return jsonify({"error": "Job check failed", "details": check_resp.text}), 500

    data = check_resp.json()
    status = data.get("status")
    if status != "done":
        return jsonify({"status": status})

    # Example keys - confirm actual keys from LALAL.ai docs or API response
    vocal_link = data.get("vocals_url") or data.get("vocal_link") or data.get("vocals")
    instrumental_link = data.get("instrumentals_url") or data.get("instrumental_link") or data.get("instrumentals")

    if not vocal_link or not instrumental_link:
        return jsonify({"error": "No download links found in job results"}), 500

    return jsonify({
        "status": status,
        "vocal_link": vocal_link,
        "instrumental_link": instrumental_link
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
