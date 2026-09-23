import argparse
import json
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Export safe model options for the frontend.")
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    metadata = json.loads(args.evaluation.read_text(encoding="utf-8"))
    categories = metadata["observed_categories"]
    cities = []
    for city in categories["city"]:
        cities.append(
            {
                "name": city,
                "neighbourhoods": metadata["city_neighbourhoods"][city],
                "coordinate_range": metadata["city_coordinate_ranges"][city],
                "supported_market_upper_bound": metadata["price_scope"][
                    "city_maximum_supported_price"
                ][city],
            }
        )

    schema = {
        "model_version": metadata["model_version"],
        "cities": cities,
        "property_types": categories["property_type"],
        "room_types": categories["room_type"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"Wrote frontend model schema to {args.output}")


if __name__ == "__main__":
    main()
