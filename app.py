from flask import Flask, request, jsonify
from azure.storage.blob import BlobServiceClient
from datetime import datetime
import json
import os
import pathlib
from dotenv import load_dotenv
# 如果.env存在，讀取.env檔案
env_path = pathlib.Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

# 取得環境變數
AZURE_CONNECTION_STRING = os.getenv('AZURE_CONNECTION_STRING')
CONTAINER_NAME = os.getenv('CONTAINER_NAME')

app = Flask(__name__)

blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

@app.route("/scan", methods=["POST"])
def scan():
    try:
        data = request.get_json()
        if not data or "result" not in data:
            return jsonify({"error": "請提供 result 欄位"}), 400

        try:
            result_data = json.loads(data["result"])
        except json.JSONDecodeError:
            return jsonify({"error": "請提供正確的 JSON 格式"}), 400

        user_id = result_data.get("id")
        user_name = result_data.get("name")

        if not user_id or not user_name:
            return jsonify({"error": "缺少 id 或 name 欄位"}), 400

        timestamp = datetime.utcnow().isoformat() + "Z"

        record = {
            "id": user_id,
            "name": user_name,
            "timestamp": timestamp
        }
        print(record)
        # 檔案名稱，例如 S12345678-20240603T143000.json
        filename = f"{user_id}-{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}.json"

        blob_client = container_client.get_blob_client(filename)
        blob_client.upload_blob(json.dumps(record, ensure_ascii=False), overwrite=True)

        return jsonify({"message": "簽到成功", "data": record})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test', methods=['GET'])
def test():
    return "Flask server is working", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
