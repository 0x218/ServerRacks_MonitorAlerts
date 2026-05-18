import os
import sys
import configparser


# =========================================================
# BASE PATH
# =========================================================
def get_base_path():

    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)

    return os.path.dirname(os.path.abspath(__file__))



BASE_PATH = get_base_path()

CONFIG_FILE_PATH = os.path.join(
    BASE_PATH,
    "config.ini"
)


# =========================================================
# CONFIG
# =========================================================
def load_config(config_path=CONFIG_FILE_PATH):
    config = configparser.ConfigParser()

    config.read(config_path)

    # RACK PREFIXES
    rack_prefixes = [
        x.strip()
        for x in config["RACKS"]["rack_prefixes"].split(",")
        if x.strip()
    ]

    # DERIVE PODS FROM PREFIXES
    # Example: 6V3 -> 6V
    pod_names = sorted(
        list({
            prefix[:2]
            for prefix in rack_prefixes
        })
    )

    rack_locations = [
        x.strip()
        for x in config["RACK_LOC"]["location"].split(",")
        if x.strip()
    ]

    settings = {
        # IBMRACK
        "base_url": config["IBMRACK"]["base_url"],
        "username": config["IBMRACK"]["username"],
        "password": config["IBMRACK"]["password"],

        # PATHS
        "driver_path": os.path.join(
            BASE_PATH,
            config["PATHS"]["driver_path"]
        ),

        "save_folder": os.path.join(
            BASE_PATH,
            config["PATHS"]["save_folder"]
        ),

        # FILTERS
        "rack_prefixes": rack_prefixes,
        "pod_names": pod_names,
        "rack_locations": rack_locations,

        "network_status_alert": config["ALERT_CONDITION"]["network_status"],
        "power_status_alert": config["ALERT_CONDITION"]["power_status"],
        "test_status_alert": config["ALERT_CONDITION"]["test_status"],
        "idle_time_alert": config["ALERT_CONDITION"]["idle_time"],
        "show_ok_status_aswell": config["ALERT_CONDITION"].getboolean("show_ok_status_aswell",fallback=False)
    }

    print("\nLoaded Rack Prefixes:")
    print(settings["rack_prefixes"])

    print("\nDerived Pods:")
    print(settings["pod_names"])

    print("\nLoaded Rac Locations:")
    print(settings["rack_locations"])

    return settings
