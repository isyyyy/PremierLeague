import json
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD
import os

def convert_profiles_to_rdf(input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as f:
        profiles = json.load(f)

    EX = Namespace("http://example.org/premierleague/")
    g = Graph()
    g.bind("ex", EX)
    g.bind("rdfs", RDFS)

    for p in profiles:
        pid = p.get("playerId")
        full_name = p.get("fullName")
        profile_text = p.get("profile_en")

        if not pid or not profile_text:
            continue

        player_uri = EX[f"player_{pid}"]
        g.add((player_uri, RDF.type, EX.Player))
        g.add((player_uri, EX.hasName, Literal(full_name)))
        g.add((player_uri, EX.profileText, Literal(profile_text, datatype=XSD.string)))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    g.serialize(destination=output_path, format="turtle")
    print(f"✅ RDF profile triples written to {output_path}")

# Example usage
convert_profiles_to_rdf(
    input_path="profile_data/player_profiles_detailed.json",
    output_path="rdf_output/player_profiles.ttl"
)