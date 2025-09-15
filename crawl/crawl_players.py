import json
import argparse
import requests
import time
from typing import Dict, Any, List, Optional


def fetch_players_for_season(session: requests.Session, competition_id: int, season_id: int) -> List[Dict[str, Any]]:
    """
    Fetch the list of players for a given competition and season using the
    Premier League's SDP API. The API is paginated and returns at most 10
    players per request. This function iterates through all pages and
    accumulates the player entries.

    Args:
        session: A requests.Session object to reuse connections.
        competition_id: Premier League competition identifier (usually 8).
        season_id: The start year of the season (e.g. 2024 for 2024/25).

    Returns:
        A list of player dictionaries as returned by the API.
    """
    base_url = (
        f"https://sdp-prem-prod.premier-league-prod.pulselive.com/api/v1/"
        f"competitions/{competition_id}/seasons/{season_id}/players"
    )
    players: List[Dict[str, Any]] = []
    next_cursor: Optional[str] = None

    while True:
        params: Dict[str, Any] = {"_limit": 20}
        if next_cursor:
            params["_next"] = next_cursor
        try:
            resp = session.get(base_url, params=params)
            resp.raise_for_status()
        except requests.HTTPError as e:
            # If the server returns an error (e.g. 502), retry after a short sleep
            time.sleep(1)
            continue

        data = resp.json()
        players.extend(data.get("data", []))
        pagination = data.get("pagination", {})
        next_cursor = pagination.get("_next")
        if not next_cursor:
            break
    return players


def fetch_player_detail(
    session: requests.Session, competition_id: int, season_id: int, player_id: int
) -> Optional[Dict[str, Any]]:
    """
    Fetch detailed information for a given player within a specific competition
    and season. If a 502 or other server error occurs, the function retries
    up to three times before giving up.

    Args:
        session: A requests.Session object.
        competition_id: Premier League competition identifier.
        season_id: Season identifier.
        player_id: Player identifier.

    Returns:
        A dictionary with detailed player information, or None if the request
        repeatedly fails.
    """
    url = (
        f"https://sdp-prem-prod.premier-league-prod.pulselive.com/api/v1/"
        f"competitions/{competition_id}/seasons/{season_id}/players/{player_id}"
    )
    attempts = 0
    while attempts < 3:
        try:
            r = session.get(url)
            # If the server returns a 502 Bad Gateway, wait and retry
            if r.status_code in (502, 503, 504):
                attempts += 1
                time.sleep(1)
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            attempts += 1
            time.sleep(1)
    return None


def merge_player_info(
    player_entry: Dict[str, Any],
    detail: Optional[Dict[str, Any]],
    season_id: int,
    competition_id: int,
) -> Dict[str, Any]:
    """
    Merge basic player information from the players list with detailed
    information from the player detail endpoint. The resulting dictionary
    contains fields required by the knowledge base definition.

    Args:
        player_entry: The player dictionary from the list endpoint.
        detail: The dictionary from the detail endpoint or None if not available.
        season_id: The season associated with this player entry.
        competition_id: Competition identifier (unused but kept for context).

    Returns:
        A dictionary with unified player information.
    """
    name = player_entry.get("name") or {}
    first_name = name.get("firstName")
    last_name = name.get("lastName")
    full_name = f"{first_name} {last_name}".strip() if first_name or last_name else None
    country = player_entry.get("country") or {}
    current_team = player_entry.get("currentTeam") or {}

    # Extract values from detail if available
    height_cm = None
    weight_kg = None
    date_of_birth = None
    joined_club_date = None
    country_of_birth = None
    preferred_foot = None
    shirt_number = player_entry.get("shirtNum")
    if detail:
        height_cm = detail.get("height")
        weight_kg = detail.get("weight")
        dates = detail.get("dates", {})
        # The detail endpoint nests birth and joined dates under dates
        date_of_birth = dates.get("birth")
        joined_club_date = dates.get("joinedClub")
        # Country of birth can appear at top level or nested; attempt both
        country_of_birth = detail.get("countryOfBirth")
        preferred_foot = detail.get("preferredFoot")
        # In some cases shirt number is provided in the detail endpoint
        if detail.get("shirtNum"):
            shirt_number = detail.get("shirtNum")

    # Position and preferred foot may appear in either entry or detail
    position = player_entry.get("position") or (detail.get("position") if detail else None)
    if not preferred_foot:
        preferred_foot = player_entry.get("preferredFoot")

    return {
        "playerId": player_entry.get("id", {}).get("playerId"),
        "competitionId": competition_id,
        "seasonId": season_id,
        "firstName": first_name,
        "lastName": last_name,
        "fullName": full_name,
        "position": position,
        "preferredFoot": preferred_foot,
        "shirtNumber": shirt_number,
        "heightCm": height_cm,
        "weightKg": weight_kg,
        "dateOfBirth": date_of_birth,
        "joinedClubDate": joined_club_date,
        "country": country.get("country"),
        "countryISO": country.get("isoCode"),
        "demonym": country.get("demonym"),
        "countryOfBirth": country_of_birth,
        "currentTeamId": current_team.get("id"),
        "currentTeamName": current_team.get("name"),
        "currentTeamShortName": current_team.get("shortName"),
    }


def crawl_players(
    competition_id: int,
    start_season: int,
    end_season: int,
    output_path: str,
    delay: float = 0.2,
) -> None:
    """
    Crawl player information for multiple seasons and write the results to a JSON file.

    Args:
        competition_id: Premier League competition ID (8).
        start_season: Start of the season range (inclusive).
        end_season: End of the season range (inclusive).
        output_path: Path to the output JSON file.
        delay: Delay between API calls for player details to avoid rate limiting.
    """
    session = requests.Session()
    all_players: List[Dict[str, Any]] = []
    # Cache to avoid fetching the same player detail multiple times
    detail_cache: Dict[tuple, Optional[Dict[str, Any]]] = {}

    for season in range(start_season, end_season + 1):
        # Fetch list of players for this season
        try:
            players_list = fetch_players_for_season(session, competition_id, season)
        except Exception:
            players_list = []
        for entry in players_list:
            player_id = entry.get("id", {}).get("playerId")
            if player_id is None:
                continue
            cache_key = (player_id, season)
            if cache_key in detail_cache:
                detail = detail_cache[cache_key]
            else:
                detail = fetch_player_detail(session, competition_id, season, player_id)
                detail_cache[cache_key] = detail
                # polite delay
                time.sleep(delay)
            merged = merge_player_info(entry, detail, season, competition_id)
            all_players.append(merged)

    # Write results to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_players, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl Premier League players by season")
    parser.add_argument(
        "--competition-id",
        type=int,
        default=8,
        help="Competition ID (default: 8 for Premier League)",
    )
    parser.add_argument(
        "--season-id",
        type=int,
        help="Single season ID to crawl (e.g. 2024 for 2024/25). If provided, overrides start-season/end-season.",
    )
    parser.add_argument(
        "--start-season",
        type=int,
        default=None,
        help="Start season ID (inclusive) if crawling multiple seasons.",
    )
    parser.add_argument(
        "--end-season",
        type=int,
        default=None,
        help="End season ID (inclusive) if crawling multiple seasons.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to output JSON file.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Delay between detail API calls in seconds (default: 0.2)",
    )
    args = parser.parse_args()

    if args.season_id is not None:
        start_season = end_season = args.season_id
    else:
        if args.start_season is None or args.end_season is None:
            parser.error("Either --season-id or both --start-season and --end-season must be provided.")
        start_season = args.start_season
        end_season = args.end_season

    crawl_players(
        competition_id=args.competition_id,
        start_season=start_season,
        end_season=end_season,
        output_path=args.output,
        delay=args.delay,
    )


if __name__ == "__main__":
    main()