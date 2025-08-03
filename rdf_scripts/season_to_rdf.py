# Create RDF conversion script for seasons.json
import json
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD
import argparse
import os

def convert_seasons_to_rdf(input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as f:
        seasons = json.load(f)

    EX = Namespace("http://example.org/premierleague/")
    g = Graph()
    g.bind("ex", EX)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)

    for season in seasons:
        sid = season.get("seasonId")
        if not sid:
            continue
        season_uri = EX[f"season_{sid}"]
        g.add((season_uri, RDF.type, EX.Season))

        if name := season.get("seasonName"):
            g.add((season_uri, EX.seasonName, Literal(name)))
        if start := season.get("startYear"):
            g.add((season_uri, EX.startYear, Literal(start, datatype=XSD.gYear)))
        if end := season.get("endYear"):
            g.add((season_uri, EX.endYear, Literal(end, datatype=XSD.gYear)))
        if stats := season.get("includesPlayerSeasonStats"):
            for stat_id in stats:
                g.add((season_uri, EX.includesPlayerSeasonStats, EX[f"stat_{stat_id}"]))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    g.serialize(destination=output_path, format="turtle")
    print(f"✔ RDF written to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    convert_seasons_to_rdf(args.input, args.output)