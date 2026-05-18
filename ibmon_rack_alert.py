# ============================================================
# Project : Server Rack Monitoring & Alert System
# File    : ibmnon_rack_alert.py
# Author  : Renjith Kumar
# Created : 
# Purpose : 
#
# Description:
#
#
# ============================================================
import time
from datetime import datetime
from selenium.webdriver.common.by import By

from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException
)
from utils_ibmrack import (
    get_network_status,
    get_power_status,
    create_driver,
    login,
    navigate_to_page,
    expand_pod_if_collapsed,
    get_tooltip,
    close_tooltip,
    parse_tooltip_header,
    is_idle_time_alert,
)

from utils_config import (
    load_config
)

from utils_logger import (
    setup_logger,
    log_alert,
)
from utils_misc import print_execution_seconds

# =========================================================
# PARSE TABLE
# =========================================================
def parse_tooltip_table(
        tooltip,
        logger,
        header_data,
        settings
):
    table_rows = tooltip.find_elements(
        By.CSS_SELECTOR,
        "tbody tr.uut-row"
    )

    for row in table_rows:
        try:
            uut_type = row.get_attribute(
                "data-uut-type"
            )
            if uut_type != "SERVER":
                continue
            tds = row.find_elements(
                By.TAG_NAME,
                "td"
            )
            if len(tds) < 12:
                continue
            loc_value = tds[0].text.strip()
            serial_value = tds[2].text.strip()

            # NETWORK
            network_td = tds[3]

            network_dot = network_td.find_element(
                By.CLASS_NAME,
                "status-dot"
            )
            network_status = get_network_status(network_dot)

            # POWER
            power_td = tds[4]
            power_status = get_power_status(power_td)

            # STATUS
            status_value = tds[9].text.strip()
            station_value = tds[10].text.strip()
            idle_time_value = tds[11].text.strip()

            # ALERT CONDITIONS
            should_alert = False

            if network_status == settings["network_status_alert"]:
                should_alert = True
            if power_status == settings["power_status_alert"]:
                should_alert = True
            if status_value.upper() == settings["test_status_alert"]:
                should_alert = True
            if is_idle_time_alert(
                    idle_time_value,
                    settings["idle_time_alert"]
            ):
                should_alert = True

            if should_alert:
                server_data = {
                    "loc": loc_value,
                    "serial_number": serial_value,
                    "network": network_status,
                    "power": power_status,
                    "status": status_value,
                    "station": station_value,
                    "idle_time": idle_time_value
                }

                log_alert(
                    logger,
                    header_data,
                    server_data
                )

                print(
                    f"ALERT: "
                    f"{loc_value} | "
                    f"{serial_value} | "
                    f"{network_status} | "
                    f"{power_status} | "
                    f"{status_value}"
                )
            else:
                print(
                    f"{loc_value} | All the status are as expected."
                )

        except Exception as e:
            print(f"Failed parsing row: {e}")

# =========================================================
# PROCESS POD
# =========================================================
def process_pod(
        driver,
        pod_name,
        rack_locations,
        logger,
        settings
):

    # EXPAND POD
    pod_container = expand_pod_if_collapsed(
        driver,
        pod_name
    )
    # GET ALL SPACES
    spaces = pod_container.find_elements(
        By.CSS_SELECTOR,
        "div.space.flex.occupied"
    )

    print(
        f"{pod_name}: "
        f"Found {len(spaces)} spaces"
    )

    # BUILD TARGET LOCATIONS
    target_locations = [
        rack
        for rack in rack_locations
        if rack.startswith(pod_name)
    ]

    print(
        f"{pod_name}: "
        f"Target locations -> "
        f"{target_locations}"
    )

    # PROCESS EACH TARGET LOCATION
    for target_location in target_locations:
        try:
            # REFIND POD
            pod_container = driver.find_element(
                By.ID,
                f"{pod_name}-pod-container"
            )

            # REFIND SPACES
            spaces = pod_container.find_elements(
                By.CSS_SELECTOR,
                "div.space.flex.occupied"
            )

            target_space = None

            # FIND MATCHING SPACE
            for space in spaces:
                try:
                    current_label = space.find_element(
                        By.CLASS_NAME,
                        "space-label"
                    ).text.strip()

                    if current_label.upper() == target_location:
                        target_space = space
                        break
                except Exception:
                    continue

            # NOT FOUND
            if not target_space:
                print(
                    f"{pod_name}: "
                    f"Could not find "
                    f"{target_location}"
                )
                continue
            # VERIFY MODEL
            try:
                rack_model = target_space.find_element(
                    By.CLASS_NAME,
                    "rack-model"
                ).text.strip()

                if rack_model.upper() != "ZORA01":

                    print(
                        f"{target_location}: "
                        f"Skipping non-ZORA01 "
                        f"rack ({rack_model})"
                    )
                    continue
            except Exception:
                print(
                    f"{target_location}: "
                    f"Could not determine "
                    f"rack model"
                )

                continue

            # PROCESS
            print(
                f"{pod_name}: "
                f"Processing "
                f"{target_location}"
            )

            # OPEN TOOLTIP
            driver.execute_script(
                "arguments[0].click();",
                target_space
            )

            # GET TOOLTIP
            tooltip = get_tooltip(driver)

            # WAIT FOR LIVE STATUS
            time.sleep(15)

            # HEADER
            header_data = parse_tooltip_header(
                tooltip
            )

            # TABLE
            parse_tooltip_table(
                tooltip,
                logger,
                header_data,
                settings
            )

            # CLOSE TOOLTIP
            close_tooltip(tooltip)

            # COOL DOWN
            time.sleep(1)

        except (
            StaleElementReferenceException,
            NoSuchElementException,
            TimeoutException
        ) as e:

            print(
                f"{pod_name}: "
                f"Recoverable error "
                f"processing "
                f"{target_location}: {e}"
            )
        except Exception as e:
            print(
                f"{pod_name}: "
                f"Unexpected error "
                f"processing "
                f"{target_location}: {e}"
            )

# =========================================================
# RUN ONE ITERATION
# =========================================================
def run_monitor_cycle(settings, logger):
    driver = create_driver(
        settings["driver_path"]
    )

    try:
        login(
            driver,
            settings["base_url"],
            settings["username"],
            settings["password"]
        )

        navigate_to_page(
            driver,
            settings["base_url"],
            "/module/mapv2/map.php?b=1flex"
        )

        time.sleep(3)

        pod_names = settings["pod_names"]
        rack_locations = settings[
            "rack_locations"
        ]
        # PROCESS PODS
        for pod_name in pod_names:
            print(
                f"\nProcessing Pod "
                f"{pod_name}"
            )

            process_pod(
                driver,
                pod_name,
                rack_locations,
                logger,
                settings
            )
    finally:

        driver.quit()

# =========================================================
# MAIN
# =========================================================

def main():
    print("Running IBMRACK Rack Alert Program")
    settings = load_config()

    logger = setup_logger(
        settings["save_folder"]
    )

    print("\nIBMRACK Alert Monitor Started")
    print(
        "Press CTRL+C to stop\n"
    )
    while True:
        cycle_start = time.time()
        try:

            print(
                f"\nStarting monitoring cycle at "
                f"{datetime.now()}"
            )

            run_monitor_cycle(
                settings,
                logger
            )

            cycle_end = time.time()
            elapsed = (
                cycle_end - cycle_start
            )
            print(
                f"Cycle completed in "
                f"{elapsed:.2f} seconds"
            )
        except Exception as e:
            print(
                f"Main loop error: {e}"
            )
        # WAIT 60 SECONDS
        print(
            "\nCooling off for "
            "1 minute...\n"
        )

        time.sleep(60)

# =========================================================
# START
# =========================================================
if __name__ == "__main__":
    try:
        start_time = time.time()
        main()
        end_time = time.time()
        print_execution_seconds(start_time, end_time)
    except KeyboardInterrupt:
        print(
            "\nProgram stopped by user"
        )
    print("IBMon alert completed successfully!")

