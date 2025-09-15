import json
import os

from pymongo import MongoClient,errors
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from dotenv import load_dotenv
from pathlib import Path
import logging


# ---------- Setup Logging ----------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Load password from file .env
db_password = os.getenv("mongodb_password")
uri = f"mongodb+srv://tuanpn18_db_user:{db_password}@vectordb-cluster.sf6loqk.mongodb.net/?retryWrites=true&w=majority&appName=vectordb-cluster"
print(uri)
# Connect to MongoDB
client = MongoClient(uri)  # or your MongoDB Atlas URI

db_name = "premier_league"
collection_name = "player_vectors"

if db_name not in client.list_database_names():
    db = client[db_name]
else:
    db = client.get_database(db_name)

if collection_name not in db.list_collection_names():
    collection = db.create_collection(collection_name)
else:
    collection = db.get_collection(collection_name)

# Load the JSON file
with open("profile_data/player_profiles_detailed.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Flatten dict to list
players = data

# Load embedding model (MiniLM or better)
model = SentenceTransformer("all-MiniLM-L6-v2")


# Embed and insert into MongoDB
inserted_count = 0
skipped_count = 0

for player in tqdm(data, desc="Processing Players"):
    try:
        profile = player.get("profile_en", "").strip()
        if not profile:
            skipped_count += 1
            continue

        embedding = model.encode(profile).tolist()
        player_doc = {
            "playerId": player.get("playerId"),
            "fullName": player.get("fullName"),
            "profile_en": profile,
            "embedding": embedding
        }

        collection.insert_one(player_doc)
        inserted_count += 1

    except errors.PyMongoError as e:
        logging.error(f"Mongo error for player {player.get('playerId')}: {e}")
    except Exception as ex:
        logging.error(f"General error for player {player.get('playerId')}: {ex}")

# ---------- Summary ----------
logging.info(f"✅ Inserted {inserted_count} player documents.")
logging.info(f"⚠️ Skipped {skipped_count} players due to missing profile_en.")