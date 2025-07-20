import argparse
import json
import os
from datetime import datetime


def validate_args_from_config():
    """
    Validate command line arguments based on config/config_args.json configuration
    """
    config_path = os.path.join("src","config", "config_args.json")

    try:
        with open(config_path, encoding="utf-8") as f:
            json_configuration = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    parser = argparse.ArgumentParser()

    for arg in json_configuration:
        parser.add_argument(
            f"--{arg['name']}",
            help=arg.get("help"),
            required=arg.get("required", False),
            choices=arg.get("choices"),
            default=arg.get("default"),
        )

    args = parser.parse_args()
    config = {}

    for arg in vars(args):
        value = getattr(args, arg)

        # Vérifie le format de start_date si fourni
        if arg == "start_date" and value:
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                parser.error(f"--start_date must be in YYYY-MM-DD format. Got: {value}")

        config[arg] = value
        print(f"{arg}: {value}")

    return config
