# Recreate aggregate script after reset
import json
import argparse
from collections import defaultdict

def aggregate_player_totals(stats_file, players_file, output_file):
    # Load player stats
    with open(stats_file, "r", encoding="utf-8") as f:
        stats = json.load(f)

    # Aggregate totals
    totals = defaultdict(lambda: {"goals": 0, "assists": 0, "appearances": 0})
    for record in stats:
        pid = str(record.get("playerId"))
        if not pid:
            continue
        totals[pid]["goals"] += record.get("goals", 0) or 0
        totals[pid]["assists"] += record.get("assists", 0) or 0
        totals[pid]["appearances"] += record.get("appearances", 0) or 0

    # Load players
    with open(players_file, "r", encoding="utf-8") as f:
        players = json.load(f)

    # Update players with aggregated totals
    for p in players:
        pid = str(p.get("playerId"))
        if pid in totals:
            p["totalGoals"] = totals[pid]["goals"]
            p["totalAssists"] = totals[pid]["assists"]
            p["totalAppearances"] = totals[pid]["appearances"]
        else:
            p["totalGoals"] = 0
            p["totalAssists"] = 0
            p["totalAppearances"] = 0

    # Write back
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(players, f, indent=2, ensure_ascii=False)
    print(f"✔ Aggregated totals written to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stats", required=True, help="Path to player_season_stats.json")
    parser.add_argument("--players", required=True, help="Path to players.json")
    parser.add_argument("--output", required=True, help="Path to output updated players.json")
    args = parser.parse_args()
    aggregate_player_totals(args.stats, args.players, args.output)
