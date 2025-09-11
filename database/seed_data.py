# database/seed_data.py
import os
from pymongo import MongoClient
from utils.csv_sync import sync_csv_to_mongo

# adjust path to backend package if running from project root:
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from utils.db import get_db

if __name__ == "__main__":
    csv_path = os.path.join(os.path.dirname(__file__), "police_records.csv")  # place CSV here
    db = get_db()
    inserted, upserted = sync_csv_to_mongo(csv_path, db)
    print(f"Inserted: {inserted}  Upserted: {upserted}")