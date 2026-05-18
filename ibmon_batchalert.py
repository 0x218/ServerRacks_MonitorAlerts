# ============================================================
# Project : Server Rack Monitoring & Alert System
# File    : ibmnon_batchalert.py
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

            tds = row.find_elements(By.TAG_NAME, "td")

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
                    "\033[1;31m"
                    f"ALERT: {loc_value} | "
                    f"{serial_value} | "
                    f"{network_status} | "
                    f"{power_status} | "
                    f"{status_value} | " 
                    f"{station_value} | "
                    f"{idle_time_value}"
                    "\033[0m"
            else:
                if settings["show_ok_status_aswell"]:
                    print(
                        "\033[32m"
                        f"{loc_value} | All the status are as expected."
                        "\033[0m"
                    )

        except Exception as e:
            print(f"Failed parsing row: {e}")

# =========================================================
# PROCESS POD
# =========================================================
def process_pod(
        driver,
        pod_name,
        rack_prefixes,
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

    print(f"{pod_name}: Found {len(spaces)} spaces")

    # BUILD TARGET RACK LIST FIRST
    target_racks = []

    for space in spaces:
        try:
            # LABEL
            space_label = space.find_element(
                By.CLASS_NAME,
                "space-label"
            ).text.strip()

            # PREFIX FILTER
            if not any(
                    space_label.startswith(prefix)
                    for prefix in rack_prefixes
            ):
                continue

            # MODEL FILTER
            rack_model = space.find_element(
                By.CLASS_NAME,
                "rack-model"
            ).text.strip()

            if rack_model.upper() != "ZORA01":
                continue

            target_racks.append(space_label)

        except Exception:
            continue

    # DEBUG
    print(
        f"{pod_name}: Matching racks -> "
        f"{target_racks}"
    )

    # PROCESS EACH RACK LABEL
    for rack_label in target_racks:
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

                    if current_label == rack_label:
                        target_space = space
                        break

                except Exception:
                    continue

            # NOT FOUND
            if not target_space:
                print(
                    f"{pod_name}: Could not refind "
                    f"{rack_label}"
                )
                continue

            print(
                f"{pod_name}: Processing "
                f"{rack_label}"
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

            # SMALL COOL DOWN
            time.sleep(1)

        except (
            StaleElementReferenceException,
            NoSuchElementException,
            TimeoutException
        ) as e:

            print(
                f"{pod_name}: Recoverable error "
                f"processing {rack_label}: {e}"
            )

        except Exception as e:

            print(
                f"{pod_name}: Unexpected error "
                f"processing {rack_label}: {e}"
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

        rack_prefixes = settings["rack_prefixes"]

        # PROCESS PODS
        for pod_name in pod_names:
            # PREFIXES FOR THIS POD ONLY
            pod_prefixes = [
                prefix
                for prefix in rack_prefixes
                if prefix.startswith(pod_name)
            ]

            print(
                f"\nProcessing {pod_name} "
                f"with prefixes: {pod_prefixes}"
            )

            process_pod(
                driver,
                pod_name,
                pod_prefixes,
                logger,
                settings
            )

    finally:

        driver.quit()

# =========================================================
# MAIN
# =========================================================

def main():
    print ("Running IBMRACK Alert Program")
    settings = load_config()

    logger = setup_logger(
        settings["save_folder"]
    )

    print("\nIBMRACK Alert Monitor Started")
    print("Press CTRL+C to stop\n")

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

            elapsed = cycle_end - cycle_start

            print(
                f"Cycle completed in "
                f"{elapsed:.2f} seconds"
            )

        except Exception as e:

            print(f"Main loop error: {e}")

        # WAIT 60 SECONDS
        print("\nCooling off for 1 minute...\n")

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
        print("\nProgram stopped by user")
        
    print("IBMon alert completed successfully!")
