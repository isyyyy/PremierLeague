"""
Run multiple SPARQL queries against a GraphDB endpoint from a file.
✓ Tách đúng từng truy vấn
✓ Tự động thêm PREFIX nếu thiếu
✓ Hiển thị lỗi và gợi ý rõ ràng
"""

import requests
import argparse
import re

# Các PREFIX phổ biến cần kiểm tra & chèn nếu thiếu
COMMON_PREFIXES = {
    "ex": "http://example.org/premierleague/",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
}

def final_split_queries(content):
    lines = content.strip().splitlines()
    queries = []
    current_query = []
    prefixes = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("prefix"):
            prefixes.append(line)
            continue
        if line.lower().startswith("select") and current_query:
            queries.append("\n".join(prefixes + current_query).strip())
            current_query = []
        current_query.append(line)

    if current_query:
        queries.append("\n".join(prefixes + current_query).strip())
    return queries

def ensure_common_prefixes(query):
    existing = set(re.findall(r"PREFIX\s+(\w+):", query))
    missing = [f"PREFIX {p}: <{COMMON_PREFIXES[p]}>" for p in COMMON_PREFIXES if p not in existing]
    return "\n".join(missing + [query]) if missing else query

def run_queries(query_file, endpoint):
    with open(query_file, "r", encoding="utf-8") as f:
        content = f.read()

    raw_queries = final_split_queries(content)
    queries = [ensure_common_prefixes(q) for q in raw_queries]

    headers = {'Accept': 'application/sparql-results+json'}

    for i, q in enumerate(queries):
        print(f"\n===== Query {i+1} =====")
        try:
            resp = requests.post(endpoint, data={'query': q}, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            results = data.get('results', {}).get('bindings', [])
            if results:
                for row in results:
                    print({k: v['value'] for k, v in row.items()})
            else:
                print("⚠️ No results returned.")
        except requests.exceptions.HTTPError as err:
            print(f"⚠️ HTTP Error on query {i+1}: {err}")
            print("❗ Query was:\n", q[:300], "..." if len(q) > 300 else "")
        except Exception as e:
            print(f"❌ Unexpected error on query {i+1}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="SPARQL .rq file path")
    parser.add_argument("--endpoint", default="http://localhost:7200/repositories/premier-league", help="SPARQL endpoint URL")
    args = parser.parse_args()
    run_queries(args.file, args.endpoint)
