import json
from collections import defaultdict

K = 5  # Top K results to evaluate

def precision_at_k(results, ground_truth, k=10):
    retrieved = results[:k]
    relevant = set(ground_truth)
    retrieved_relevant = [r for r in retrieved if r in relevant]
    return len(retrieved_relevant) / k

def recall_at_k(results, ground_truth, k=10):
    retrieved = results[:k]
    relevant = set(ground_truth)
    retrieved_relevant = [r for r in retrieved if r in relevant]
    return len(retrieved_relevant) / len(relevant) if relevant else 0.0

def f1_score(p, r):
    return 2 * p * r / (p + r) if p + r > 0 else 0.0

with open("ground_truth/results.json", "r") as f:
    ground_truth_data = json.load(f)

with open("ground_truth/vector_results.json", "r") as f:
    vector_data = json.load(f)

# Convert ground truth into a lookup dict
ground_truth_map = {item["query"]: set(item["ground_truth_names"]) for item in ground_truth_data}

# List of DB modes
db_modes = ["mongo_results", "chroma_results", "graphdb_results"]

# Collect scores
scores = defaultdict(lambda: defaultdict(list))  # scores[db][metric] = [..]

for item in vector_data:
    query = item["query"]
    gt_names = ground_truth_map.get(query, set())

    for db in db_modes:
        if db not in item:
            continue
        result_names = [r["name"] for r in item[db]]

        p = precision_at_k(result_names, gt_names, K)
        r = recall_at_k(result_names, gt_names, K)
        f1 = f1_score(p, r)

        scores[db]["precision"].append(p)
        scores[db]["recall"].append(r)
        scores[db]["f1"].append(f1)


summary = {}
for db in db_modes:
    summary[db] = {}
    for metric in ["precision", "recall", "f1"]:
        values = scores[db][metric]
        avg = sum(values) / len(values) if values else 0.0
        summary[db][f"{metric}@{K}"] = round(avg, 4)
        print(f"{db} - {metric}@{K}: {avg:.3f}")

# Lưu vào file JSON
with open("ground_truth/evaluation_report.json", "w") as f:
    json.dump(summary, f, indent=2)

print("✅ Evaluation results saved to ground_truth/evaluation_report.json")