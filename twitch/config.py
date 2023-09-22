import yaml
import json

cfg = None


def load_config():
    global cfg
    if not cfg:
        with open("twitch/config.json", "r") as json_file:
            cfg = json.load(json_file)
    return cfg
