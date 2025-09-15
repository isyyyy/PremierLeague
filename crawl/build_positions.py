import json
import argparse
from typing import Dict, Any, List


def load_players(path: str) -> List[Dict[str, Any]]:
    """Load aggregated player data from JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def slugify(name: str) -> str:
    """Convert a position name into a slug suitable for an identifier."""
    return name.lower().replace(" ", "_").replace("-", "_")


def build_positions(input_path: str, output_path: str) -> None:
    """
    Extract unique positions from player data and write them to a JSON file.
    Each position is assigned a slug identifier and retains its original name.

    Args:
        input_path: Path to aggregated players JSON file.
        output_path: Path to write positions JSON file.
    """
    players = load_players(input_path)
    positions: Dict[str, Dict[str, Any]] = {}
    for p in players:
        pos = p.get("position")
        if not pos:
            continue
        normalized = pos.strip().title()
        slug = slugify(normalized)
        if slug not in positions:
            positions[slug] = {
                "positionId": slug,
                "positionName": normalized,
            }
    positions_list = sorted(positions.values(), key=lambda x: x["positionName"])
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(positions_list, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Position records from players data")
    parser.add_argument("--input", required=True, help="Path to aggregated players JSON")
    parser.add_argument("--output", required=True, help="Path to write positions JSON")
    args = parser.parse_args()
    build_positions(args.input, args.output)


if __name__ == "__main__":
    main()