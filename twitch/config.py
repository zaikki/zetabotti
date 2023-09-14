import yaml

cfg = None


def load_config():
    global cfg
    if not cfg:
        with open("twitch/config.yml", "r") as ymlfile:
            cfg = yaml.unsafe_load(ymlfile)
    return cfg
