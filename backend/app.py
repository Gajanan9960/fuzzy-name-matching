# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.db import get_db
from utils.preprocessing import normalize_text, transliterate_text
from utils.matching import fuzzy_match
from utils.csv_sync import sync_csv_to_mongo
import os
import tempfile

app = Flask(__name__)
CORS(app)

db = get_db()

@app.route("/upload_csv", methods=["POST"])
def upload_csv():
    """
    Accepts multipart/form-data file upload (key = 'file').
    Example: curl -F "file=@../database/police_records.csv" http://127.0.0.1:5000/upload_csv
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request (use key 'file')"}), 400

    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Save to temp file
    tmp_dir = tempfile.gettempdir()
    tmp_path = os.path.join(tmp_dir, f.filename)
    f.save(tmp_path)

    try:
        inserted, upserted = sync_csv_to_mongo(tmp_path, db)
        return jsonify({"status": "ok", "inserted": inserted, "upserted": upserted})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

@app.route("/search_name", methods=["POST"])
def search_name():
    data = request.json or {}
    query_name = data.get("name", "").strip()
    if not query_name:
        return jsonify({"error": "Please provide 'name' in JSON body"}), 400

    # produce hindi+english forms for query
    query_forms = transliterate_text(query_name)
    query_eng = query_forms.get("english", "").lower()

    # naive scan (optimize later with indexes / blocking)
    cursor = db.records.find({})
    results = []
    for rec in cursor:
        # ensure a value for english name in record
        rec_eng = rec.get("name_english") or ""
        rec_eng = rec_eng.lower()

        score = fuzzy_match(query_eng, rec_eng)
        if score >= 40:  # low threshold to include borderline candidates; tune later
            results.append({
                "id": str(rec.get("_id")),
                "name_hindi": rec.get("name_hindi", ""),
                "name_english": rec.get("name_english", ""),
                "score": round(score, 2),
                "case_id": rec.get("case_id", "")
            })

    # sort highest first and return top 50 (limit)
    results = sorted(results, key=lambda x: x["score"], reverse=True)[:50]
    return jsonify({"query": query_name, "results": results})

if __name__ == "__main__":
    # For production use a WSGI server like Gunicorn and disable debug
    app.run(host="0.0.0.0", port=5001, debug=True)