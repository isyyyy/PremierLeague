import json
import psycopg2
from pathlib import Path

input_path = Path("ground_truth/queries_with_sql.json")
output_path = Path("ground_truth/results.json")

# Kết nối đến PostgreSQL
conn = psycopg2.connect(
    dbname="premier_league",
    user="postgres",
    password="postgres",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# Đọc queries
with open(input_path, "r") as f:
    queries = json.load(f)

results = []

for item in queries:
    query_text = item["query"]
    sql = item["sql"]

    try:
        cursor.execute(sql)
        players = cursor.fetchall()
        player_ids = [p[0] for p in players]
        player_names = [p[1] for p in players]

        results.append({
            "query": query_text,
            "sql": sql,
            "ground_truth_player_ids": player_ids,
            "ground_truth_names": player_names
        })

    except Exception as e:
        print(f"❌ Lỗi với query '{query_text}': {e}")

cursor.close()
conn.close()

# Ghi file kết quả
with open(output_path, "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("✅ Đã lưu ground truth vào ground_truth/results.json")