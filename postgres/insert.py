import json
import psycopg2
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

conn = psycopg2.connect(
    host=os.getenv("PG_HOST"),
    port=os.getenv("PG_PORT"),
    database=os.getenv("PG_DB"),
    user=os.getenv("PG_USER"),
    password=os.getenv("PG_PASSWORD")
)
cursor = conn.cursor()

with open(Path(__file__).resolve().parents[1] / "co-working/summary_player_info.json") as f:
    players = json.load(f)

for p in players:
    # Insert player
    cursor.execute("""
        INSERT INTO players (
            player_id, full_name, first_name, last_name, date_of_birth, nationality,
            nationality_iso, demonym, preferred_foot, height_cm, weight_kg,
            position, shirt_number, joined_season, total_appearances,
            total_goals, total_assists, has_position, has_nationality,
            total_seasons, career_goals, career_assists, age
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (player_id) DO NOTHING;
    """, (
        p["playerId"], p["fullName"], p.get("firstName"), p.get("lastName"), p.get("dateOfBirth"),
        p.get("nationality"), p.get("nationalityISO"), p.get("demonym"), p.get("preferredFoot"),
        p.get("heightCm"), p.get("weightKg"), p.get("position"), p.get("shirtNumber"),
        p.get("joinedSeason"), p.get("totalAppearances"), p.get("totalGoals"), p.get("totalAssists"),
        p.get("hasPosition"), p.get("hasNationality"), p.get("total_seasons"), p.get("career_goals"),
        p.get("career_assists"), p.get("age")
    ))

    # Insert club
    club = p.get("current_club")
    if club:
        cursor.execute("""
            INSERT INTO clubs (club_id, club_name, foundation_year, stadium, location)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (club_id) DO NOTHING;
        """, (club["clubId"], club["clubName"], club.get("foundationYear"), club.get("stadium"), club.get("location")))

    # Club history
    for ch in p.get("club_history", []):
        for season in ch.get("seasons", []):
            cursor.execute("""
                INSERT INTO player_club_history (player_id, club_id, season)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (p["playerId"], ch["clubId"], season))

    # Teammates
    for teammate in p.get("teammateWith", []):
        cursor.execute("""
            INSERT INTO player_teammates (player_id, teammate_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """, (p["playerId"], teammate))

    # Season stats
    for stat in p.get("season_statistics", []):
        cursor.execute("""
            INSERT INTO season_statistics (
                player_season_stats_id, player_id, season_id, club_id, appearances, goals, assists,
                expected_goals, expected_assists, touches_in_box, penalties_taken, hit_woodwork,
                free_kicks_scored, crosses_completed, minutes_played, dribbles_completed, duels_won,
                aerial_duels_won, tackles, interceptions, blocks, red_cards, yellow_cards,
                fouls_committed, offsides, own_goals, corners_taken, passes_completed
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (player_season_stats_id) DO NOTHING;
        """, tuple(stat.get(k) for k in [
            "playerSeasonStatsId", "playerId", "seasonId", "clubId", "appearances", "goals", "assists",
            "expectedGoals", "expectedAssists", "touchesInBox", "penaltiesTaken", "hitWoodwork",
            "freeKicksScored", "crossesCompleted", "minutesPlayed", "dribblesCompleted", "duelsWon",
            "aerialDuelsWon", "tackles", "interceptions", "blocks", "redCards", "yellowCards",
            "foulsCommitted", "offsides", "ownGoals", "cornersTaken", "passesCompleted"
        ]))

conn.commit()
cursor.close()
conn.close()