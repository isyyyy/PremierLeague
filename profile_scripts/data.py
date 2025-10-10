import json
import os

def safe(val, default=0):
    return val if val is not None else default

def has_real_stats(stat: dict) -> bool:
    """Check if a season stats entry has at least one meaningful value."""
    keys_to_check = [
        "appearances", "goals", "assists", "minutesPlayed",
        "expectedGoals", "expectedAssists", "touchesInBox",
        "crossesCompleted", "dribblesCompleted", "duelsWon",
        "tackles", "interceptions", "passesCompleted"
    ]
    return any(stat.get(k) not in (None, 0, 0.0) for k in keys_to_check)


def generate_detailed_player_profiles(players_path, stats_path, clubs_path, output_path):
    with open(players_path, "r", encoding="utf-8") as f:
        players = {p["playerId"]: p for p in json.load(f)}

    with open(stats_path, "r", encoding="utf-8") as f:
        stats = json.load(f)

    with open(clubs_path, "r", encoding="utf-8") as f:
        clubs = {c["clubId"]: c.get("clubName", f"Club {c['clubId']}") for c in json.load(f)}

    profiles = []

    for player_id, p in players.items():
        # Filter stats for this player in season 2024
        stats_2024 = [s for s in stats if s.get("playerId") == player_id and s.get("seasonId") == 2024]

        # Skip players without valid stats in 2024
        if not any(has_real_stats(s) for s in stats_2024):
            continue

        parts = []
        parts.append(f"PLAYER: {p.get('fullName')} (ID {p.get('playerId')})")
        parts.append(f"Date of Birth: {p.get('dateOfBirth')} | Nationality: {p.get('nationality')} ({p.get('nationalityISO')})")
        parts.append(f"Position: {p.get('position')} | Preferred Foot: {p.get('preferredFoot')}")
        parts.append(f"Height: {p.get('heightCm')} cm | Weight: {p.get('weightKg')} kg")
        parts.append(f"Shirt Number: {p.get('shirtNumber')} | Joined Season: {p.get('joinedSeason')}")

        current_club_id = p.get("playsFor")
        club_name = clubs.get(current_club_id, f"Club {current_club_id}")
        parts.append(f"Current Club: {club_name} (ID {current_club_id})")

        # Add stats per season
        player_stats = [s for s in stats if s.get("playerId") == player_id]
        for s in player_stats:
            season = s.get("seasonId")
            season_str = f"{season}/{str(season + 1)[-2:]}"
            club = clubs.get(s.get("clubId"), f"Club {s.get('clubId')}")
            parts.append(f"\nSeason {season_str} at {club}:")
            parts.append(f"- Appearances: {safe(s.get('appearances'))} | Goals: {safe(s.get('goals'))} | Assists: {safe(s.get('assists'))}")
            parts.append(f"- Minutes Played: {safe(s.get('minutesPlayed'))} | Passes Completed: {safe(s.get('passesCompleted'))}")
            parts.append(f"- Dribbles Completed: {safe(s.get('dribblesCompleted'))} | Tackles: {safe(s.get('tackles'))} | Interceptions: {safe(s.get('interceptions'))}")
            parts.append(f"- Duels Won: {safe(s.get('duelsWon'))} | Aerial Duels Won: {safe(s.get('aerialDuelsWon'))}")
            parts.append(f"- Expected Goals (xG): {safe(s.get('expectedGoals'))} | Expected Assists (xA): {safe(s.get('expectedAssists'))}")
            parts.append(f"- Yellow Cards: {safe(s.get('yellowCards'))} | Red Cards: {safe(s.get('redCards'))}")
            parts.append(f"- Offsides: {safe(s.get('offsides'))} | Touches in Box: {safe(s.get('touchesInBox'))}")
            parts.append(f"- Crosses Completed: {safe(s.get('crossesCompleted'))} | Hit Woodwork: {safe(s.get('hitWoodwork'))}")

        profiles.append({
            "playerId": player_id,
            "fullName": p.get("fullName"),
            "profile_en": "\n".join(parts)
        })

    print(f"Process {len(profiles)} players with valid 2024 stats")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)

    print(f"✅ Detailed player profiles saved to: {output_path}")

# Example usage:
generate_detailed_player_profiles(
    players_path="raw_data/players.json",
    stats_path="raw_data/player_season_stats.json",
    clubs_path="raw_data/clubs.json",
    output_path="profile_data/player_profiles_detailed.json"
)