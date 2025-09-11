# backend/utils/csv_sync.py
import pandas as pd
import os
from utils.preprocessing import normalize_text, transliterate_text
from pymongo import errors

def sync_csv_to_mongo(csv_path: str, db, key_field: str = "case_id"):
    """
    Read CSV and upsert into MongoDB collection db.records.
    Returns tuple (inserted_count, upserted_count)
    """
    inserted = 0
    upserted = 0

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"{csv_path} not found")

    df = pd.read_csv(csv_path, dtype=str).fillna("")

    # Ensure index on key_field (if present)
    try:
        db.records.create_index([(key_field, 1)], unique=True, sparse=True)
    except Exception:
        pass

    for _, row in df.iterrows():
        # Normalize and prepare document
        doc = {
            "name_hindi": str(row.get("name_hindi", "")).strip(),
            "name_english": str(row.get("name_english", "")).strip(),
            "father_name": str(row.get("father_name", "")).strip(),
            "address": str(row.get("address", "")).strip(),
            "case_id": str(row.get("case_id", "")).strip()
        }

        # If one of the name fields is missing, transliterate the other
        try:
            if doc["name_hindi"] and not doc["name_english"]:
                forms = transliterate_text(doc["name_hindi"])
                doc["name_english"] = forms.get("english", "").lower()
            elif doc["name_english"] and not doc["name_hindi"]:
                forms = transliterate_text(doc["name_english"])
                doc["name_hindi"] = forms.get("hindi", "")
        except Exception:
            # fallback: leave as-is
            pass

        # Normalize strings
        doc["name_hindi"] = normalize_text(doc["name_hindi"])
        doc["name_english"] = normalize_text(doc["name_english"])
        doc["father_name"] = normalize_text(doc["father_name"])
        doc["address"] = normalize_text(doc["address"])
        doc["case_id"] = doc["case_id"]  # keep original case_id (often IDs are case sensitive)

        # Upsert by key_field if available, else try match by english+father_name
        try:
            if doc.get(key_field):
                res = db.records.update_one(
                    {key_field: doc[key_field]},
                    {"$set": doc},
                    upsert=True
                )
                # If a new doc was upserted, res.upserted_id is not None
                if res.upserted_id:
                    inserted += 1
                else:
                    upserted += 1
            else:
                # try to find an existing record with same english name + father
                query = {"name_english": doc["name_english"]}
                if doc["father_name"]:
                    query["father_name"] = doc["father_name"]

                existing = db.records.find_one(query)
                if existing:
                    db.records.update_one({"_id": existing["_id"]}, {"$set": doc})
                    upserted += 1
                else:
                    db.records.insert_one(doc)
                    inserted += 1
        except errors.DuplicateKeyError:
            # rare race condition; count as upsert
            upserted += 1
        except Exception as e:
            # Log and continue (in production: use logger)
            print(f"Error saving row {doc.get('case_id') or doc.get('name_english')}: {e}")
            continue

    return inserted, upserted