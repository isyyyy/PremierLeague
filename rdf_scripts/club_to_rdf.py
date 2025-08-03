# Create RDF conversion script for clubs.json
import json
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD
import argparse
import os

def convert_clubs_to_rdf(input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as f:
        clubs = json.load(f)

    EX = Namespace("http://example.org/premierleague/")
    g = Graph()
    g.bind("ex", EX)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)

    for club in clubs:
        cid = club.get("clubId")
        if not cid:
            continue
        club_uri = EX[f"club_{cid}"]
        g.add((club_uri, RDF.type, EX.Club))

        if name := club.get("clubName"):
            g.add((club_uri, EX.clubName, Literal(name)))
        if stadium := club.get("stadium"):
            g.add((club_uri, EX.stadium, Literal(stadium)))
        if location := club.get("location"):
            lat = location.get("latitude")
            lon = location.get("longitude")
            if lat is not None and lon is not None:
                g.add((club_uri, EX.latitude, Literal(lat)))
                g.add((club_uri, EX.longitude, Literal(lon)))
        if seasons := club.get("participatesIn"):
            for season in seasons:
                g.add((club_uri, EX.participatesIn, EX[f"season_{season}"]))
        if players := club.get("hasPlayer"):
            for pid in players:
                g.add((club_uri, EX.hasPlayer, EX[f"player_{pid}"]))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    g.serialize(destination=output_path, format="turtle")
    print(f"✔ RDF written to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    convert_clubs_to_rdf(args.input, args.output)