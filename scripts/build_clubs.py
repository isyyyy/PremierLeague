import json
import argparse
import requests
from typing import Dict, Any, List, Optional, Tuple, Set


def load_players_by_season(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_team_details(session: requests.Session, team_id: int) -> Optional[Dict[str, Any]]:
    """Fetch team details from the footballapi endpoint. Returns None on failure."""
    url = f"https://footballapi.pulselive.com/football/teams/{team_id}"
    try:
        resp = session.get(url)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return None


def load_club_metadata(session: requests.Session) -> List[Dict[str, Any]]:
    """Load club metadata from the Premier League static resource."""
    url = "https://resources.premierleague.com/premierleague25/config/clubs-metadata.json"
    try:
        resp = session.get(url)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return []


def normalize_name(name: str) -> str:
    """Normalize club names for comparison: lower-case and remove ampersands."""
    return name.lower().replace("&", "and").replace("  ", " ").strip()


def build_clubs(input_path: str, output_path: str) -> None:
    """
    Build club data and relationships from players_by_season data. The function
    groups players by club, fetches club details and metadata, and writes a
    normalized list of club records to a JSON file.

    Args:
        input_path: Path to the players_by_season JSON file.
        output_path: Path to write the clubs JSON file.
    """
    records = load_players_by_season(input_path)
    # Build grouping by club
    clubs: Dict[int, Dict[str, Any]] = {}
    for rec in records:
        club_id = rec.get("currentTeamId")
        club_name = rec.get("currentTeamName") or rec.get("currentTeamShortName")
        season_id = rec.get("seasonId")
        player_id = rec.get("playerId")
        if club_id is None or club_name is None:
            continue
        entry = clubs.setdefault(
            club_id,
            {
                "clubId": club_id,
                "clubName": club_name,
                "foundationYear": None,
                "stadium": None,
                "location": None,
                "hasPlayer": set(),
                "participatesIn": set(),
                "hasSeasonStats": None,
            },
        )
        entry["hasPlayer"].add(player_id)
        entry["participatesIn"].add(season_id)

    session = requests.Session()
    metadata = load_club_metadata(session)
    # Build a lookup map for metadata by normalized name
    metadata_lookup = {normalize_name(item.get("name", "")): item for item in metadata}

    for club in clubs.values():
        club_id = club["clubId"]
        club_name = club["clubName"]
        details = fetch_team_details(session, club_id)
        # Use details if the returned name matches our club name
        valid_details = False
        if details:
            api_name = details.get("name")
            if api_name and normalize_name(api_name) == normalize_name(club_name):
                valid_details = True
        if valid_details:
            grounds = details.get("grounds", [])
            # Choose the first ground as the primary stadium if available
            if grounds:
                ground = grounds[0]
                club["stadium"] = ground.get("name")
                city = ground.get("city")
                # The API may return city as either a dictionary with latitude/longitude
                # or a simple string. Check type before accessing.
                if isinstance(city, dict):
                    lat = city.get("latitude")
                    lon = city.get("longitude")
                    if lat is not None and lon is not None:
                        club["location"] = {"latitude": lat, "longitude": lon}
        else:
            # Fallback to metadata for stadium name
            meta = metadata_lookup.get(normalize_name(club_name))
            if meta:
                club["stadium"] = meta.get("stadium")
        # Convert sets to sorted lists for JSON serialization
        club["hasPlayer"] = sorted(list(club["hasPlayer"]))
        club["participatesIn"] = sorted(list(club["participatesIn"]))

    # Write output
    clubs_list = sorted(clubs.values(), key=lambda x: x["clubName"])
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(clubs_list, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build club data from players_by_season records")
    parser.add_argument("--input", required=True, help="Path to players_by_season JSON file")
    parser.add_argument("--output", required=True, help="Path to write clubs JSON file")
    args = parser.parse_args()
    build_clubs(args.input, args.output)


if __name__ == "__main__":
    main()