import json
import argparse
import requests
import time
from typing import Dict, Any, Optional, List


def load_players_by_season(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_player_season_stats(
    session: requests.Session, competition_id: int, season_id: int, player_id: int, delay: float = 0.2
) -> Optional[Dict[str, Any]]:
    """
    Fetch statistics for a given player in a particular season using the v2 stats endpoint.
    Implements basic retry logic to handle occasional 429 or 502 responses.

    Args:
        session: A requests.Session object.
        competition_id: Competition ID (8 for Premier League).
        season_id: Season ID (start year).
        player_id: Player ID.
        delay: Delay between retries in seconds.

    Returns:
        A dictionary of stats if successful, otherwise None.
    """
    url = (
        f"https://sdp-prem-prod.premier-league-prod.pulselive.com/api/v2/"
        f"competitions/{competition_id}/seasons/{season_id}/players/{player_id}/stats"
    )
    attempts = 0
    while attempts < 3:
        try:
            resp = session.get(url)
            if resp.status_code in (502, 503, 504):
                attempts += 1
                time.sleep(delay)
                continue
            if resp.status_code == 429:
                # Too many requests; sleep and retry
                time.sleep(delay * 3)
                attempts += 1
                continue
            resp.raise_for_status()
            data = resp.json()
            return data.get("stats")
        except requests.RequestException:
            attempts += 1
            time.sleep(delay)
    return None


def map_stats(stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map raw stats keys to the ontology-defined fields. Missing keys are
    interpreted as 0.

    Args:
        stats: Raw stats dictionary from the API.

    Returns:
        A dictionary with normalized fields.
    """
    def get(key: str) -> Optional[float]:
        value = stats.get(key)
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    # Helper to sum multiple keys for passes completed
    def sum_keys(keys: List[str]) -> Optional[float]:
        total = 0.0
        any_present = False
        for k in keys:
            v = get(k)
            if v is not None:
                total += v
                any_present = True
        return total if any_present else None

    mapped: Dict[str, Any] = {
        # Attack
        "appearances": get("appearances"),
        "goals": get("goals"),
        "assists": get("assists"),
        "expectedGoals": get("expectedGoals") or get("expectedGoalsOnTargetConceded"),
        "expectedAssists": get("expectedAssists"),
        "touchesInBox": get("touchesInOppositionBox") or get("touches"),
        "penaltiesTaken": get("penaltiesTaken"),
        "hitWoodwork": get("hitWoodwork"),
        "freeKicksScored": get("freeKicksScored"),
        "crossesCompleted": get("successfulCrosses") or get("successfulCrossesAndCorners") or get("successfulCrossesOpenPlay"),
        # Physical
        "minutesPlayed": get("timePlayed"),
        "dribblesCompleted": get("successfulDribbles"),
        "duelsWon": get("duelsWon"),
        "aerialDuelsWon": get("aerialDuelsWon"),
        # Defence
        "tackles": get("totalTackles"),
        "interceptions": get("interceptions"),
        "blocks": get("blocks"),
        # Discipline
        "redCards": get("totalRedCards"),
        "yellowCards": get("yellowCards"),
        "foulsCommitted": get("fouls") or get("foulsCommitted"),
        "offsides": get("offsides"),
        "ownGoals": get("ownGoals"),
        # Possession/Other
        "cornersTaken": get("corners"),
        "passesCompleted": sum_keys([
            "successfulPasses",
            "successfulShortPasses",
            "successfulLongPasses",
            "successfulLaunches",
            "successfulCrosses",
            "successfulCrossesAndCorners",
            "successfulCrossesOpenPlay",
        ]),
    }
    return mapped


def build_player_season_stats(
    input_path: str, output_path: str, competition_id: int = 8, delay: float = 0.2
) -> None:
    """
    Build PlayerSeasonStats records from players_by_season data. For each
    unique (playerId, seasonId, clubId) combination, call the v2 stats
    endpoint and map the returned stats to ontology fields. The function
    writes the resulting list to a JSON file.

    Args:
        input_path: Path to players_by_season JSON file.
        output_path: Path to write PlayerSeasonStats JSON.
        competition_id: Competition ID (default 8).
        delay: Delay between API calls to avoid rate limiting.
    """
    records = load_players_by_season(input_path)
    unique_triples = []
    seen = set()
    for rec in records:
        player_id = rec.get("playerId")
        season_id = rec.get("seasonId")
        club_id = rec.get("currentTeamId")
        if player_id is None or season_id is None or club_id is None:
            continue
        key = (player_id, season_id, club_id)
        if key not in seen:
            seen.add(key)
            unique_triples.append(key)
    session = requests.Session()
    output_records: List[Dict[str, Any]] = []
    for player_id, season_id, club_id in unique_triples:
        stats = fetch_player_season_stats(session, competition_id, season_id, player_id, delay=delay)
        mapped = map_stats(stats) if stats is not None else {k: None for k in [
            "appearances", "goals", "assists", "expectedGoals", "expectedAssists",
            "touchesInBox", "penaltiesTaken", "hitWoodwork", "freeKicksScored", "crossesCompleted",
            "minutesPlayed", "dribblesCompleted", "duelsWon", "aerialDuelsWon",
            "tackles", "interceptions", "blocks",
            "redCards", "yellowCards", "foulsCommitted", "offsides", "ownGoals",
            "cornersTaken", "passesCompleted",
        ]}
        record = {
            "playerSeasonStatsId": f"{player_id}-{season_id}-{club_id}",
            "playerId": player_id,
            "seasonId": season_id,
            "clubId": club_id,
        }
        record.update(mapped)
        output_records.append(record)
        # polite delay
        time.sleep(delay)
    # Write
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_records, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build PlayerSeasonStats using v2 stats endpoint")
    parser.add_argument("--input", required=True, help="Path to players_by_season JSON")
    parser.add_argument("--output", required=True, help="Path to write player season stats JSON")
    parser.add_argument(
        "--competition",
        type=int,
        default=8,
        help="Competition ID (default 8 for Premier League)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Delay between API calls to avoid rate limiting (default 0.2 seconds)",
    )
    args = parser.parse_args()
    build_player_season_stats(args.input, args.output, args.competition, args.delay)


if __name__ == "__main__":
    main()