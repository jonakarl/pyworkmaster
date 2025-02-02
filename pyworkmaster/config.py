import logging
import os
import yaml
import pprint

from pyworkmaster.layout import parse

_log = logging.getLogger(__name__)

DEFAULT_CONFIG_NAME = "config.yaml"
DEFAULT_LOCAL_CONFIG_NAME = ".workmaster.yml"

HOME = os.path.abspath(os.path.expanduser("~"))
CONFIG_HOME = os.getenv("XDG_CONFIG_HOME", os.path.join(HOME, ".config"))
CONFIG = os.path.join(CONFIG_HOME, "workmaster", DEFAULT_CONFIG_NAME)
LOCALCONFIG = os.path.join(os.path.abspath(os.getcwd()), DEFAULT_LOCAL_CONFIG_NAME)


def translate_loglevel(loglevel):
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError("Invalid log level: %s" % loglevel)
    return numeric_level


ALL_PARAMS = {"log_level": (translate_loglevel("INFO"), int)}


class Config:
    def __init__(self, document=None):
        self.config = {"common": {}}

        for p in ALL_PARAMS:
            self.config["common"][p] = ALL_PARAMS[p]

        yaml_config = None
        if document is not None:
            yaml_config = yaml.safe_load(document)
        elif os.path.isfile(CONFIG):
            with open(CONFIG, "r") as fp:
                yaml_config = yaml.safe_load(fp)
        if yaml_config:
            self.__handle_yaml(yaml_config)

        if os.path.isfile(LOCALCONFIG):
            with open(LOCALCONFIG, "r") as fp:
                yaml_config = yaml.safe_load(fp)
            if yaml_config:
                self.__handle_yaml(yaml_config)

    def __iter__(self):
        return (k for k in self.config if k != "common")

    def __getitem__(self, i):
        return self.config.get(i, {})

    def __contains__(self, i):
        return bool(i in self.config)

    def __repr__(self):
        return pprint.pformat(self.config)

    def get_global(self, i):
        return self.config["common"].get(i)[0]

    def __handle_yaml(self, yaml_config):
        global_vars = {}
        for k, v in yaml_config.get("variables", {}).items():
            global_vars[k] = v.format(**global_vars)

        projects = [k for k in set(yaml_config.keys()) if k != "variables"]
        for project in projects:
            self.config[project] = {}

            y = yaml_config[project]
            p = self.config[project]

            p["variables"] = global_vars.copy()
            p["windows"] = {}

            # layout.
            p["layout"] = parse(y.get("layout"))

            # variables.
            p["variables"]["PROJECT"] = project
            for k, v in y.get("variables", []).items():
                p["variables"][k] = v.format(**p["variables"])

            # windows.
            for k, vs in y.get("windows", {}).items():
                p["windows"][k] = []
                # commands, expand {VARS}
                for v in vs:
                    p["windows"][k].append(v.format(**p["variables"]))
