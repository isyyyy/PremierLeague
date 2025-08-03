import json
import argparse
import requests
import time
from collections import defaultdict
from typing import Dict, Any, List, Optional, Set


def load_season_data(path: str) -> List[Dict[str, Any]]:
    """Load player-by-season data from JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_teammate_mapping(records: List[Dict[str, Any]]) -> Dict[int, Set[int]]:
    """
    Build a mapping from playerId to a set of teammate playerIds. Two players
    are considered teammates if they play for the same club in the same season.

    Args:
        records: List of player-season dictionaries.

    Returns:
        A dictionary mapping a playerId to a set of teammate playerIds.
    """
    group: Dict[tuple, List[int]] = defaultdict(list)
    for rec in records:
        player_id = rec.get("playerId")
        club_id = rec.get("currentTeamId")
        season_id = rec.get("seasonId")
        if player_id is None or club_id is None or season_id is None:
            continue
        group[(season_id, club_id)].append(player_id)

    teammates: Dict[int, Set[int]] = defaultdict(set)
    for (_, _), players in group.items():
        for p in players:
            teammates[p].update([t for t in players if t != p])
    return teammates


def fetch_player_variants(session: requests.Session, player_id: int) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch all variants (across competitions and seasons) for a given player.

    Args:
        session: A requests.Session object.
        player_id: The player's unique identifier.

    Returns:
        A list of variant dictionaries, or None if the request fails.
    """
    url = f"https://sdp-prem-prod.premier-league-prod.pulselive.com/api/v1/players/{player_id}"
    try:
        resp = session.get(url)
        resp.raise_for_status()
        data = resp.json()
        # The API returns a list under 'players' or directly as a list
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "players" in data:
            return data["players"]
        return None
    except requests.RequestException:
        return None


def extract_player_details(
    variants: List[Dict[str, Any]], competition_id: int
) -> Optional[Dict[str, Any]]:
    """
    From a list of player variants, extract details specific to the given
    competition. This identifies the earliest and latest seasons the player
    appears in the competition, and derives attributes such as nationality,
    position, etc.

    Args:
        variants: List of player dictionaries across competitions and seasons.
        competition_id: Competition identifier to filter variants.

    Returns:
        A dictionary with aggregated player details, or None if no variants
        match the competition.
    """
    # Filter for the desired competition. Cast both variant and input IDs to strings
    league_variants = [
        v
        for v in variants
        if str(v.get("id", {}).get("competitionId")) == str(competition_id)
    ]
    if not league_variants:
        return None
    # Sort by season
    league_variants.sort(key=lambda x: x.get("id", {}).get("seasonId"))
    # Earliest and latest variants
    first_variant = league_variants[0]
    last_variant = league_variants[-1]
    # Common attributes from last variant (assumed current)
    name = last_variant.get("name") or {}
    country = last_variant.get("country") or {}
    current_team = last_variant.get("currentTeam") or {}
    position = last_variant.get("position")
    preferred_foot = last_variant.get("preferredFoot")
    height_cm = last_variant.get("height")
    weight_kg = last_variant.get("weight")
    dates = last_variant.get("dates", {})
    date_of_birth = dates.get("birth")
    # Compute joinedSeason from earliest variant
    joined_season = first_variant.get("id", {}).get("seasonId")
    return {
        "firstName": name.get("firstName"),
        "lastName": name.get("lastName"),
        "fullName": f"{name.get('firstName')} {name.get('lastName')}".strip(),
        "dateOfBirth": date_of_birth,
        "nationality": country.get("country"),
        "nationalityISO": country.get("isoCode"),
        "demonym": country.get("demonym"),
        "preferredFoot": preferred_foot,
        "heightCm": height_cm,
        "weightKg": weight_kg,
        "position": position,
        "currentTeamId": current_team.get("id"),
        "currentTeamName": current_team.get("name"),
        "currentTeamShortName": current_team.get("shortName"),
        "joinedSeason": joined_season,
    }


def build_players(
    input_path: str, output_path: str, competition_id: int = 8
) -> None:
    """
    Build player data aggregated across seasons. Reads season-level player
    records, collects unique player identifiers, fetches variant details,
    derives joined season and current team, and constructs relationship fields.

    Args:
        input_path: Path to the JSON file containing season-level player data.
        output_path: Path to write the aggregated player data.
        competition_id: The competition ID to filter variants (default 8).
    """
    season_data = load_season_data(input_path)
    # Build teammate mapping before iterating players
    teammate_map = build_teammate_mapping(season_data)
    # Group season records by playerId to access additional fields like shirtNumber
    recs_by_player: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for rec in season_data:
        pid = rec.get("playerId")
        if pid is not None:
            recs_by_player[pid].append(rec)

    unique_player_ids: Set[int] = set(recs_by_player.keys())
    session = requests.Session()

    players_output: List[Dict[str, Any]] = []
    for player_id in sorted(unique_player_ids):
        variants = fetch_player_variants(session, player_id)
        if not variants:
            continue
        details = extract_player_details(variants, competition_id)
        if not details:
            continue
        # Build player record
        # Attempt to determine the shirt number from any season record for this player
        shirt_num = None
        for rec in recs_by_player.get(player_id, []):
            # Some records may store shirt number under 'shirtNumber' or 'shirtNum'
            sn = rec.get("shirtNumber") or rec.get("shirtNum")
            if sn:
                shirt_num = sn
                break

        # Fallback names and other attributes from season records if missing
        # Use the first season record for this player as a fallback for names and nationality
        rec_fallback = recs_by_player.get(player_id, [{}])[0]
        first_name = details.get("firstName") or rec_fallback.get("firstName")
        last_name = details.get("lastName") or rec_fallback.get("lastName")
        full_name = f"{first_name} {last_name}".strip() or rec_fallback.get("fullName") or f"{player_id}"

        nationality = details.get("nationality") or rec_fallback.get("country") or rec_fallback.get("nationality")
        nationality_iso = details.get("nationalityISO") or rec_fallback.get("countryISO")
        demonym = details.get("demonym") or rec_fallback.get("demonym")
        preferred_foot = details.get("preferredFoot") or rec_fallback.get("preferredFoot")
        position = details.get("position") or rec_fallback.get("position")

        player_record = {
            "playerId": player_id,
            "fullName": full_name,
            "firstName": first_name,
            "lastName": last_name,
            "dateOfBirth": details.get("dateOfBirth"),
            "nationality": nationality,
            "nationalityISO": nationality_iso,
            "demonym": demonym,
            "preferredFoot": preferred_foot,
            "heightCm": details.get("heightCm"),
            "weightKg": details.get("weightKg"),
            "position": position,
            "shirtNumber": shirt_num,
            "joinedSeason": details.get("joinedSeason"),
            "totalAppearances": None,
            "totalGoals": None,
            "totalAssists": None,
            # Relationships
            "playsFor": details.get("currentTeamId"),
            "hasPosition": position,
            "hasNationality": nationality,
            "hasSeasonStats": None,
            "teammateWith": sorted(list(teammate_map.get(player_id, []))),
        }
        players_output.append(player_record)

    # Write to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(players_output, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build aggregated player data from season records")
    parser.add_argument("--input", required=True, help="Path to players_by_season JSON file")
    parser.add_argument("--output", required=True, help="Path to write aggregated players JSON")
    parser.add_argument(
        "--competition-id",
        type=int,
        default=8,
        help="Competition ID to filter variants (default 8 for Premier League)",
    )
    args = parser.parse_args()
    build_players(args.input, args.output, args.competition_id)


if __name__ == "__main__":
    main()