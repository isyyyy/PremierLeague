import chromadb
import streamlit as st
import pandas as pd
import requests
import re
import os
import urllib.parse
from SPARQLWrapper import SPARQLWrapper, JSON
import json
import plotly.graph_objects as go
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path


env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

db_password = os.getenv("mongodb_password")
GRAPHDB_URL = "http://localhost:7200"
REPOSITORY = "premier-league"
SIMILARITY_INDEX = "player_profile"
SPARQL_ENDPOINT = f"{GRAPHDB_URL}/repositories/{REPOSITORY}"
MONGO_URI = f"mongodb+srv://tuanpn18_db_user:{db_password}@vectordb-cluster.sf6loqk.mongodb.net/?retryWrites=true&w=majority&appName=vectordb-cluster"




def search_graphdb(query):
    sparql_query = """PREFIX : <http://www.ontotext.com/graphdb/similarity/>
    PREFIX similarity-index: <http://www.ontotext.com/graphdb/similarity/instance/>
    PREFIX pubo: <http://ontology.ontotext.com/publishing#>

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

    headers = {
        'Accept': 'application/sparql-results+json'
    }

    url = "http://localhost:7200/repositories/premier-league"
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    results = response.json().get("results", {}).get("bindings", [])

    player_summaries = []

    for hit in results[:10]:  # Limit to top 10
        uri = hit["documentID"]["value"]
        score = float(hit["score"]["value"])
        player_id = uri.split("/")[-1]
        explore_url = f"{GRAPHDB_URL}/rest/explore/graph"
        params = {
            "bnodes": "true",
            "inference": "explicit",
            "role": "subject",
            "sameAs": "true",
            "uri": f"http://example.org/premierleague/{player_id}"
        }
        headers = {
            "Accept": "application/x-graphdb-table-results+json",
            "X-GraphDB-Repository": REPOSITORY
        }
        profile_response = requests.get(explore_url, params=params, headers=headers)
        profile_response.raise_for_status()
        profile_data = profile_response.json()
        bindings = profile_data.get("results", {}).get("bindings", [])
        properties = {}

        # Extract all literal values from triples
        for b in bindings:
            pred = b.get("predicate", {}).get("value", "")
            obj = b.get("object", {}).get("value", "")
            if pred and obj:
                key = pred.split("/")[-1]
                properties[key] = obj

        # Fallback: Extract missing fields from profileText if available
        profile_text = properties.get("profileText", "")
        if profile_text:

            fallback_fields = {
                "dateOfBirth": r"Date of Birth:\s+([0-9]{4}-[0-9]{2}-[0-9]{2})",
                "height": r"Height:\s+([0-9]+) cm",
                "weight": r"Weight:\s+([0-9]+) kg",
                "preferredFoot": r"Preferred Foot:\s+([^\n|]+)",
                "hasPosition": r"Position:\s+([^\n|]+)",
                "hasNationality": r"Nationality:\s+([^\(|\n]+)",
                "playsFor": r"Current Club:\s+([^\(]+)",
                "shirtNumber": r"Shirt Number:\s+([0-9]+)",
                "joinedSeason": r"Joined Season:\s+([0-9]+)"
            }
            for key, pattern in fallback_fields.items():
                if key not in properties or properties[key] == "-":
                    match = re.search(pattern, profile_text)
                    if match:
                        properties[key] = match.group(1).strip()

        player_name = properties.get("hasName", player_id)
        player_summaries.append({"uri": uri, "name": player_name, "score": score, "profile": properties})

    return player_summaries


def search_mongodb(query):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = MongoClient(MONGO_URI)
    db = client["premier_league"]
    collection = db["player_vectors"]

    embedded_query = model.encode(query).tolist()
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
    results = list(collection.aggregate(pipeline))
    # st.write(results)
    return [{"name": r["fullName"], "score": r.get("score", 0.0), "profile": {"profileText": r.get("profile_en", "No profile available.")}} for r in results]



def search_chromadb(query):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.HttpClient(host="localhost", port=8000)
    collection = client.get_collection("players")

    embedded_query = model.encode(query).tolist()
    result = collection.query(query_embeddings=[embedded_query], n_results=10)
    # st.write(result)
    documents = result["documents"][0]
    metadatas = result["metadatas"][0]
    distances = result["distances"][0]

    output = []
    for i in range(len(documents)):
        output.append({
            "name": metadatas[i].get("fullName", f"Player {i + 1}"),
            "score": distances[i],
            "profile": {"profileText": documents[i]}
        })

    return output



def render_player_card(player):
    props = player["profile"]
    st.markdown("---")
    st.subheader(player["name"])
    if source_choice == "GraphDB":
        st.write(f"**Similarity Score:** {player['score']:.3f}")
    else:
        st.write("**Similarity Score:** N/A (MongoDB does not return score)")

    st.markdown("**📄 Profile Summary**")
    st.code(props.get("profileText", "-"))



def render_comparison_mode(query):
    st.subheader("🔍 Compare GraphDB vs MongoDB vs ChromaDB")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🧠 GraphDB")
        data = search_graphdb(query)
        df = pd.DataFrame([{"Name": p["name"], "Score": f"{p['score']:.3f}"} for p in data])
        st.dataframe(df)

    with col2:
        st.markdown("### 🧮 MongoDB")
        data = search_mongodb(query)
        df = pd.DataFrame([{"Name": p["name"], "Score": "N/A"} for p in data])
        st.dataframe(df)

    with col3:
        st.markdown("### 🧊 ChromaDB")
        data = search_chromadb(query)
        df = pd.DataFrame([{"Name": p["name"], "Score": f"{p['score']:.3f}"} for p in data])
        st.dataframe(df)


def render_player_card(player):
    st.markdown("---")
    st.subheader(player["name"])
    st.write(f"**Similarity Score:** {player['score']:.3f}")
    st.markdown("**📄 Profile Summary**")
    st.code(player["profile"].get("profileText", "-"))

def render_single_source_mode(query, source):
    st.header(f"🔍 Results from {source}")
    if source == "GraphDB":
        results = search_graphdb(query)
    elif source == "MongoDB":
        results = search_mongodb(query)
    else:
        results = search_chromadb(query)

    if not results:
        st.warning("No results found.")
        return

    df = pd.DataFrame([{"Name": r["name"], "Score": f"{r['score']:.3f}"} for r in results])
    st.dataframe(df, use_container_width=True)

    selected_name = st.selectbox("Select player to view", df["Name"].tolist())
    selected = next((p for p in results if p["name"] == selected_name), None)
    if selected:
        render_player_card(selected)


def load_evaluation_report(path="ground_truth/evaluation_report.json"):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading evaluation report: {e}")
        return None



# UI
st.set_page_config(layout="wide")
st.title("⚽ Football Player Profile Search")
query = st.text_input("Enter your search (e.g., 'Goalkeeper taller than 185cm')")
st.sidebar.title("🔍 Search Configuration")
mode = st.sidebar.selectbox("Select Search Mode", ["Single Source Search", "Compare", "Evaluate"])
if mode == "Single Source Search":
    source_choice = st.sidebar.selectbox("Choose search source", ["GraphDB", "MongoDB", "ChromaDB"])
else:
    source_choice = None
show_eval = st.sidebar.checkbox("📊 Show Evaluation Report")


if query:
    if mode == "Compare":
        render_comparison_mode(query)
    else:
        render_single_source_mode(query, source_choice)

if show_eval:
    st.subheader("📊 Evaluation Report Summary")
    report = load_evaluation_report()
    if report:
        for source, metrics in report.items():
            st.markdown(f"### 🔎 {source.replace('_', ' ').title()}")
            df = pd.DataFrame(metrics.items(), columns=["Metric", "Value"])
            df["Value"] = df["Value"].apply(lambda x: round(x, 4))
            st.dataframe(df, use_container_width=True)
    else:
        st.warning("No evaluation report found.")
