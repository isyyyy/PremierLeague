import json
import argparse
from typing import Dict, Any, List


def load_players(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def slugify_country(name: str) -> str:
    """Create a slug from country name if ISO code is missing."""
    return name.lower().replace(" ", "_")


def build_nationalities(input_path: str, output_path: str) -> None:
    """
    Extract unique nationalities from players data and write them to a JSON file.
    Each country includes its name, ISO code and demonym if available.

    Args:
        input_path: Path to aggregated players JSON file.
        output_path: Path to write nationalities JSON file.
    """
    players = load_players(input_path)
    countries: Dict[str, Dict[str, Any]] = {}
    for p in players:
        country_name = p.get("nationality")
        if not country_name:
            continue
        iso_code = p.get("nationalityISO")
        demonym = p.get("demonym")
        # Determine identifier: prefer ISO code, fall back to slug
        country_id = iso_code if iso_code else slugify_country(country_name)
        if country_id not in countries:
            countries[country_id] = {
                "countryId": country_id,
                "countryName": country_name,
                "isoCode": iso_code,
                "demonym": demonym,
            }
    countries_list = sorted(countries.values(), key=lambda x: x["countryName"])
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(countries_list, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Nationality records from players data")
    parser.add_argument("--input", required=True, help="Path to aggregated players JSON")
    parser.add_argument("--output", required=True, help="Path to write nationalities JSON")
    args = parser.parse_args()
    build_nationalities(args.input, args.output)


if __name__ == "__main__":
    main()