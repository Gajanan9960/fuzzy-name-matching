from pymongo import MongoClient

def get_db():
    client = MongoClient("mongodb://localhost:27017/")  # Compass default
    db = client["police_records"]
    return db