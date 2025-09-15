import json
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
import chromadb
import os
from dotenv import load_dotenv
import requests
from pathlib import Path


env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# === Load input queries ===
with open("ground_truth/results.json", "r") as f:
    queries = json.load(f)

with open("raw_data/players.json", "r") as f:
    players = json.load(f)

player_info = {p["playerId"]: p["fullName"] for p in players}
# === Initialize embedding model ===
model = SentenceTransformer("all-MiniLM-L6-v2")

# === MongoDB Setup ===
db_password = os.getenv("mongodb_password")
MONGO_URI = f"mongodb+srv://tuanpn18_db_user:{db_password}@vectordb-cluster.sf6loqk.mongodb.net/?retryWrites=true&w=majority&appName=vectordb-cluster"
mongo_client = MongoClient(MONGO_URI)
mongo_collection = mongo_client["premier_league"]["player_vectors"]

# === ChromaDB Setup ===
chroma_client = chromadb.HttpClient(host="localhost", port=8000)
chroma_collection = chroma_client.get_or_create_collection("players")

# === GraphDB Setup ===
GRAPHDB_URL = "http://localhost:7200"
REPOSITORY = "premier-league"

def query_graphdb(query):
    sparql_query = """PREFIX : <http://www.ontotext.com/graphdb/similarity/>
    PREFIX similarity-index: <http://www.ontotext.com/graphdb/similarity/instance/>
    SELECT ?documentID ?score {
        ?search a ?index ;
                ?searchType ?query ;
                :searchParameters ?parameters ;
                ?resultType ?result .
        ?result :value ?documentID ;
                :score ?score .
    }
    """
    params = {
        '$index': '<http://www.ontotext.com/graphdb/similarity/instance/player_profile>',
        '$query': f'"{query}"',
        '$parameters': '""',
        '$resultType': '<http://www.ontotext.com/graphdb/similarity/documentResult>',
        '$searchType': '<http://www.ontotext.com/graphdb/similarity/searchTerm>',
        'query': sparql_query
    }
    headers = {'Accept': 'application/sparql-results+json'}
    url = f"{GRAPHDB_URL}/repositories/{REPOSITORY}"

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json().get("results", {}).get("bindings", [])
        results = []
        for r in data[:10]:
            uri = r["documentID"]["value"]
            pid = uri.split("/")[-1]
            id = pid.split("_")[1]
            full_name = player_info.get(id, id)
            results.append({"name": full_name, "score": float(r["score"]["value"])})
        return results
    except Exception as e:
        print(f"[GraphDB Error] {query}: {e}")
        return []

def query_mongodb(query_text):
    try:
        embedded_query = model.encode(query_text).tolist()
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "queryVector": embedded_query,
                    "path": "embedding",
                    "numCandidates": 100,
                    "limit": 10
                }
            }
        ]
        results = list(mongo_collection.aggregate(pipeline))
        return [{"name": r.get("fullName", ""), "score": r.get("score", 0.0)} for r in results]
    except Exception as e:
        print(f"[MongoDB Error] {query_text}: {e}")
        return []

def query_chromadb(query_text):
    try:
        query_embedding = model.encode([query_text])
        result = chroma_collection.query(query_embeddings=query_embedding, n_results=10, include=["documents", "metadatas", "distances"])
        return [{
            "name": result["metadatas"][0][i].get("fullName", ""),
            "score": result["distances"][0][i]
        } for i in range(len(result["metadatas"][0]))]
    except Exception as e:
        print(f"[ChromaDB Error] {query_text}: {e}")
        return []

# === Query and Save Results ===
all_results = []
for q in tqdm(queries):
    query_text = q["query"]

    mongo = query_mongodb(query_text)
    chroma = query_chromadb(query_text)
    graph = query_graphdb(query_text)

    all_results.append({
        "query": query_text,
        "mongo_results": mongo,
        "chroma_results": chroma,
        "graphdb_results": graph
    })

with open("ground_truth/vector_results.json", "w") as f:
    json.dump(all_results, f, indent=2)

print("✅ Done. Results saved to data ground_truth/vector_results.json")