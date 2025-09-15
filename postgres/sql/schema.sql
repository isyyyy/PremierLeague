DROP TABLE IF EXISTS season_statistics, player_teammates, player_club_history, clubs, players CASCADE;

CREATE TABLE players (
    player_id TEXT PRIMARY KEY,
    full_name TEXT,
    first_name TEXT,
    last_name TEXT,
    date_of_birth DATE,
    nationality TEXT,
    nationality_iso TEXT,
    demonym TEXT,
    preferred_foot TEXT,
    height_cm FLOAT,
    weight_kg FLOAT,
    position TEXT,
    shirt_number INT,
    joined_season TEXT,
    total_appearances FLOAT,
    total_goals FLOAT,
    total_assists FLOAT,
    has_position TEXT,
    has_nationality TEXT,
    total_seasons INT,
    career_goals FLOAT,
    career_assists FLOAT,
    age INT
);

CREATE TABLE clubs (
    club_id TEXT PRIMARY KEY,
    club_name TEXT,
    foundation_year INT,
    stadium TEXT,
    location TEXT
);

CREATE TABLE player_club_history (
    player_id TEXT,
    club_id TEXT,
    season INT,
    PRIMARY KEY (player_id, club_id, season)
);

CREATE TABLE season_statistics (
    player_season_stats_id TEXT PRIMARY KEY,
    player_id TEXT,
    season_id INT,
    club_id TEXT,
    appearances FLOAT,
    goals FLOAT,
    assists FLOAT,
    expected_goals FLOAT,
    expected_assists FLOAT,
    touches_in_box FLOAT,
    penalties_taken FLOAT,
    hit_woodwork FLOAT,
    free_kicks_scored FLOAT,
    crosses_completed FLOAT,
    minutes_played FLOAT,
    dribbles_completed FLOAT,
    duels_won FLOAT,
    aerial_duels_won FLOAT,
    tackles FLOAT,
    interceptions FLOAT,
    blocks FLOAT,
    red_cards FLOAT,
    yellow_cards FLOAT,
    fouls_committed FLOAT,
    offsides FLOAT,
    own_goals FLOAT,
    corners_taken FLOAT,
    passes_completed FLOAT
);

CREATE TABLE player_teammates (
    player_id TEXT,
    teammate_id TEXT,
    PRIMARY KEY (player_id, teammate_id)
);
