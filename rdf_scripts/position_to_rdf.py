"""
Convert positions.json to RDF triples (Turtle format).
"""

import json
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS
import argparse
import os

def convert_positions_to_rdf(input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as f:
        positions = json.load(f)

    EX = Namespace("http://example.org/premierleague/")
    g = Graph()
    g.bind("ex", EX)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)

    for pos in positions:
        pid = pos.get("positionId")
        label = pos.get("positionName")
        if not pid or not label:
            continue
        pos_uri = EX[pid]
        g.add((pos_uri, RDF.type, EX.Position))
        g.add((pos_uri, RDFS.label, Literal(label)))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    g.serialize(destination=output_path, format="turtle")
    print(f"✔ RDF written to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    convert_positions_to_rdf(args.input, args.output)
