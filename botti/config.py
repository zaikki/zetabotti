import yaml
import json

# cfg = None


def load_config(path):
    #global cfg
    cfg = None
    if not cfg:
        with open(path, "r") as json_file:
            cfg = json.load(json_file)
    return cfg
