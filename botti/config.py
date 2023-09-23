import json


def load_config(path):
    cfg = None
    if not cfg:
        with open(path, "r") as json_file:
            cfg = json.load(json_file)
    return cfg
