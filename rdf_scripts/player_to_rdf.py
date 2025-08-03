"""
Convert players.json to RDF triples (Turtle format).
"""

import json
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD
import argparse
import os
import re

def convert_players_to_rdf(input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as f:
        players = json.load(f)

    EX = Namespace("http://example.org/premierleague/")
    g = Graph()
    g.bind("ex", EX)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    for player in players:
        pid = player.get("playerId")
        if not pid:
            continue
        player_uri = EX[f"player_{pid}"]
        g.add((player_uri, RDF.type, EX.Player))
        if name := player.get("fullName"):
            g.add((player_uri, EX.hasName, Literal(name)))
        dob = player.get("dateOfBirth")
        if dob and date_pattern.match(dob):
            g.add((player_uri, EX.dateOfBirth, Literal(dob, datatype=XSD.date)))
        if foot := player.get("preferredFoot"):
            g.add((player_uri, EX.preferredFoot, Literal(foot)))
        if height := player.get("heightCm"):
            g.add((player_uri, EX.height, Literal(height, datatype=XSD.integer)))
        if shirt := player.get("shirtNumber"):
            g.add((player_uri, EX.shirtNumber, Literal(shirt, datatype=XSD.integer)))
        if join := player.get("joinedSeason"):
            g.add((player_uri, EX.joinedSeason, Literal(join)))
        if goals := player.get("totalGoals"):
            g.add((player_uri, EX.totalGoals, Literal(goals, datatype=XSD.integer)))
        if assists := player.get("totalAssists"):
            g.add((player_uri, EX.totalAssists, Literal(assists, datatype=XSD.integer)))
        if apps := player.get("totalAppearances"):
            g.add((player_uri, EX.totalAppearances, Literal(apps, datatype=XSD.integer)))
        if pos := player.get("hasPosition"):
            g.add((player_uri, EX.hasPosition, EX[pos.replace(" ", "_")]))
        if nat := player.get("hasNationality"):
            g.add((player_uri, EX.hasNationality, EX[nat.replace(" ", "_")]))
        if club := player.get("playsFor"):
            g.add((player_uri, EX.playsFor, EX[f"club_{club}"]))
        if teammates := player.get("teammateWith"):
            for tm in teammates:
                g.add((player_uri, EX.teammateWith, EX[f"player_{tm}"]))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    g.serialize(destination=output_path, format="turtle")
    print(f"✔ RDF written to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    convert_players_to_rdf(args.input, args.output)
