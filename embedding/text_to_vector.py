from sentence_transformers import SentenceTransformer
import json

# Load the embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

def get_embedding(text: str):
    embedding = model.encode(text)
    return embedding.tolist()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert text to embedding vector")
    parser.add_argument("--text", type=str, required=True, help="Input query text")
    args = parser.parse_args()

    vector = get_embedding(args.text)
    print(json.dumps(vector, indent=2))
    with open("embedding/output_vector.json", "w") as f:
        json.dump(vector, f, indent=2)
    print("Vector saved to output_vector.json")
