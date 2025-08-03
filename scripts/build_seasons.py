import json
import argparse
from typing import Dict, Any, List


def load_player_season_stats(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_seasons(input_path: str, output_path: str) -> None:
    """
    Build Season records from PlayerSeasonStats. For each seasonId, compute
    seasonName (e.g. 2024 -> "2024/25"), startYear, endYear, and list of
    included PlayerSeasonStats identifiers.

    Args:
        input_path: Path to PlayerSeasonStats JSON file.
        output_path: Path to write Seasons JSON file.
    """
    stats = load_player_season_stats(input_path)
    seasons: Dict[int, Dict[str, Any]] = {}
    for rec in stats:
        season_id = rec.get("seasonId")
        if season_id is None:
            continue
        entry = seasons.setdefault(
            season_id,
            {
                "seasonId": season_id,
                "seasonName": None,
                "startYear": str(season_id),
                "endYear": str(season_id + 1),
                "includesPlayerSeasonStats": [],
            },
        )
        entry["includesPlayerSeasonStats"].append(rec.get("playerSeasonStatsId"))
    # Compute seasonName for each
    for entry in seasons.values():
        start_year = int(entry["startYear"])
        end_suffix = str((start_year + 1) % 100).zfill(2)
        entry["seasonName"] = f"{start_year}/{end_suffix}"
        # Sort the list of IDs for consistency
        entry["includesPlayerSeasonStats"] = sorted(entry["includesPlayerSeasonStats"])
    # Sort seasons by seasonId
    seasons_list = sorted(seasons.values(), key=lambda x: x["seasonId"])
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(seasons_list, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Season records from PlayerSeasonStats")
    parser.add_argument("--input", required=True, help="Path to player season stats JSON")
    parser.add_argument("--output", required=True, help="Path to write seasons JSON")
    args = parser.parse_args()
    build_seasons(args.input, args.output)


if __name__ == "__main__":
    main()