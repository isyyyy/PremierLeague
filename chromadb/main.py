import os
import json
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
import chromadb


# ----------------------------
# Config
# ----------------------------
DATA_FILE = "profile_data/player_profiles_detailed.json"
CHROMA_COLLECTION_NAME = "players"
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000

# ----------------------------
# Initialize Chroma Client
# ----------------------------
client = chromadb.HttpClient(
    host=CHROMA_HOST,
    port=CHROMA_PORT,
)

collection = client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)

# ----------------------------
# Load Embedding Model
# ----------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")


# ----------------------------
# Load Data
# ----------------------------
if not os.path.exists(DATA_FILE):
    raise FileNotFoundError(f"Could not find {DATA_FILE}")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# ----------------------------
# Index to Chroma
# ----------------------------
print(f"📦 Indexing {len(data)} players to ChromaDB...")

for player in tqdm(data):
    player_id = player.get("playerId")
    text = player.get("profile_en", "").strip()
    if not player_id or not text:
        continue

    embedding = model.encode(text).tolist()

    try:
        collection.add(
            ids=[player_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[{
                "fullName": player.get("fullName", ""),
            }]
        )
    except Exception as e:
        print(f"⚠️ Failed to index player {player_id}: {e}")

print("✅ Done indexing!")