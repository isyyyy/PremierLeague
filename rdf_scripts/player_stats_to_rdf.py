# Create RDF conversion script for player_season_stats.json

import json
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD
import argparse
import os

def convert_player_stats_to_rdf(input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as f:
        stats = json.load(f)

    EX = Namespace("http://example.org/premierleague/")
    g = Graph()
    g.bind("ex", EX)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)

    for stat in stats:
        sid = stat.get("playerId")
        season = stat.get("seasonId")
        club = stat.get("clubId")
        if not sid or not season:
            continue
        stat_id = f"{sid}-{season}-{club}"
        stat_uri = EX[f"stat_{stat_id}"]
        g.add((stat_uri, RDF.type, EX.PlayerSeasonStats))
        g.add((stat_uri, EX.forPlayer, EX[f"player_{sid}"]))
        if club:
            g.add((stat_uri, EX.forClub, EX[f"club_{club}"]))
        g.add((stat_uri, EX.inSeason, EX[f"season_{season}"]))

        # Add stats if present
        for key, predicate in {
            "appearances": EX.appearances,
            "goals": EX.goals,
            "assists": EX.assists,
            "expectedGoals": EX.expectedGoals,
            "expectedAssists": EX.expectedAssists,
            "touchesInBox": EX.touchesInBox,
            "penaltiesTaken": EX.penaltiesTaken,
            "hitWoodwork": EX.hitWoodwork,
            "freeKicksScored": EX.freeKicksScored,
            "crossesCompleted": EX.crossesCompleted,
            "minutesPlayed": EX.minutesPlayed,
            "dribblesCompleted": EX.dribblesCompleted,
            "duelsWon": EX.duelsWon,
            "aerialDuelsWon": EX.aerialDuelsWon,
            "tackles": EX.tackles,
            "interceptions": EX.interceptions,
            "blocks": EX.blocks,
            "redCards": EX.redCards,
            "yellowCards": EX.yellowCards,
            "foulsCommitted": EX.foulsCommitted,
            "offsides": EX.offsides,
            "ownGoals": EX.ownGoals,
            "cornersTaken": EX.cornersTaken,
            "passesCompleted": EX.passesCompleted,
        }.items():
            value = stat.get(key)
            if value is not None:
                g.add((stat_uri, predicate, Literal(value, datatype=XSD.integer)))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    g.serialize(destination=output_path, format="turtle")
    print(f"✔ RDF written to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    convert_player_stats_to_rdf(args.input, args.output)
