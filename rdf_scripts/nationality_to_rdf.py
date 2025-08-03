# Create RDF conversion script for nationalities.json
import json
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS
import argparse
import os

def convert_nationalities_to_rdf(input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as f:
        nationalities = json.load(f)

    EX = Namespace("http://example.org/premierleague/")
    g = Graph()
    g.bind("ex", EX)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)

    for country in nationalities:
        cid = country.get("countryId")
        label = country.get("countryName")
        demonym = country.get("demonym")
        if not cid or not label:
            continue
        country_uri = EX[cid]
        g.add((country_uri, RDF.type, EX.Nationality))
        g.add((country_uri, RDFS.label, Literal(label)))
        if demonym:
            g.add((country_uri, EX.demonym, Literal(demonym)))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    g.serialize(destination=output_path, format="turtle")
    print(f"✔ RDF written to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    convert_nationalities_to_rdf(args.input, args.output)
