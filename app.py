import os
import requests
import json
from flask import Flask, request, jsonify
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
        print(f"MIME type: {audio_file.mimetype}")
        
        # Read file content
        file_content = audio_file.read()
        file_size = len(file_content)
        print(f"File size: {file_size} bytes ({file_size/1024:.2f} KB)")
        
        # Step 1: Upload file to LALAL.ai
        print("Step 1: Uploading file to LALAL.ai...")
        
        headers = {
            "Authorization": f"license {LALAL_API_KEY}",
            "Content-Disposition": f'attachment; filename="{audio_file.filename}"'
        }
        
        upload_response = requests.post(
            "https://www.lalal.ai/api/upload/",
            headers=headers,
            data=file_content,  # Send as binary data, not multipart
            timeout=60
        )
        
        print(f"Upload response status: {upload_response.status_code}")
        print(f"Upload response: {upload_response.text}")
        
        upload_response.raise_for_status()
        upload_result = upload_response.json()
        
        if upload_result.get("status") != "success":
            return jsonify({
                "error": "Upload failed",
                "details": upload_result.get("error", "Unknown error")
            }), 500
        
        file_id = upload_result.get("id")
        print(f"File uploaded successfully. ID: {file_id}")
        
        # Step 2: Start split process
        print("Step 2: Starting split process...")
        
        split_headers = {
            "Authorization": f"license {LALAL_API_KEY}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Create split parameters
        split_params = [{
            "id": file_id,
            "stem": "vocals",  # or "voice" for voice isolation
            "splitter": "phoenix"  # Use the latest splitter
        }]
        
        split_data = {
            "params": json.dumps(split_params)
        }
        
        split_response = requests.post(
            "https://www.lalal.ai/api/split/",
            headers=split_headers,
            data=split_data,
            timeout=60
        )
        
        print(f"Split response status: {split_response.status_code}")
        print(f"Split response: {split_response.text}")
        
        split_response.raise_for_status()
        split_result = split_response.json()
        
        if split_result.get("status") != "success":
            return jsonify({
                "error": "Split failed",
                "details": split_result.get("error", "Unknown error")
            }), 500
        
        # Return the file ID for checking results
        return jsonify({
            "file_id": file_id,
            "task_id": split_result.get("task_id"),
            "status": "processing",
            "message": "File uploaded and split started successfully",
            "upload_info": {
                "size": upload_result.get("size"),
                "duration": upload_result.get("duration"),
                "expires": upload_result.get("expires")
            }
        })

    except requests.exceptions.RequestException as e:
        print(f"Error with LALAL.ai API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        return jsonify({"error": f"LALAL.ai API error: {str(e)}"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route("/results/<file_id>", methods=["GET"])
@require_api_key
def results(file_id):
    try:
        headers = {
            "Authorization": f"license {LALAL_API_KEY}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "id": file_id
        }
        
        response = requests.post(
            "https://www.lalal.ai/api/check/",
            headers=headers,
            data=data,
            timeout=30
        )
        
        print(f"Check response status: {response.status_code}")
        print(f"Check response: {response.text}")
        
        response.raise_for_status()
        result = response.json()
        
        if result.get("status") != "success":
            return jsonify({
                "error": "Check failed",
                "details": result.get("error", "Unknown error")
            }), 500
        
        file_result = result.get("result", {}).get(file_id, {})
        
        if file_result.get("status") == "success":
            split_info = file_result.get("split")
            task_info = file_result.get("task")
            
            if split_info:
                return jsonify({
                    "status": "done",
                    "stem_track": split_info.get("stem_track"),
                    "back_track": split_info.get("back_track"),
                    "duration": split_info.get("duration"),
                    "stem_type": split_info.get("stem")
                })
            elif task_info:
                task_state = task_info.get("state")
                if task_state == "progress":
                    return jsonify({
                        "status": "processing",
                        "progress": task_info.get("progress", 0)
                    })
                elif task_state == "error":
                    return jsonify({
                        "status": "error",
                        "error": task_info.get("error", "Processing failed")
                    }), 500
                elif task_state == "cancelled":
                    return jsonify({
                        "status": "cancelled"
                    }), 500
        
        return jsonify({
            "status": "processing",
            "message": "Still processing..."
        })
        
    except requests.exceptions.RequestException as e:
        print(f"Error checking results: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        return jsonify({"error": f"Failed to check results: {str(e)}"}), 500

@app.route("/cancel/<file_id>", methods=["POST"])
@require_api_key
def cancel(file_id):
    try:
        headers = {
            "Authorization": f"license {LALAL_API_KEY}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "id": file_id
        }
        
        response = requests.post(
            "https://www.lalal.ai/api/cancel/",
            headers=headers,
            data=data,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        return jsonify(result)
        
    except requests.exceptions.RequestException as e:
        print(f"Error cancelling task: {e}")
        return jsonify({"error": f"Failed to cancel task: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)