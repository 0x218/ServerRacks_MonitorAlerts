import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# =========================================================
# WAIT
# =========================================================
def wait(seconds):
    time.sleep(seconds)


# =========================================================
# DRIVER
# =========================================================
def create_driver(driver_path):
    options = Options()

    options.add_experimental_option(
        "excludeSwitches",
        ["enable-logging"]
    )

    options.add_argument("--log-level=3")
    options.add_argument("--silent")

    service = Service(driver_path)
    service.creationflags = 0x08000000

    driver = webdriver.Edge(
        service=service,
        options=options
    )

    driver.maximize_window()
    return driver

# =========================================================
# LOGIN
# =========================================================
def login(driver, base_url, username, password):

    driver.get(base_url + "/login.php")

    driver.find_element(
        By.NAME,
        "username"
    ).send_keys(username)

    driver.find_element(
        By.NAME,
        "password"
    ).send_keys(password)

    driver.find_element(
        By.XPATH,
        "//input[@type='submit' and @value='login']"
    ).click()

    time.sleep(5)

    print("Login successful")


# =========================================================
# EXPAND POD
# =========================================================
def expand_pod_if_collapsed(driver, pod_code):
    pod_container_id = f"{pod_code}-pod-container"
    pod = driver.find_element(
        By.ID,
        pod_container_id
    )

    collapsed = pod.get_attribute(
        "data-collapsed"
    )

    if collapsed == "true":
        toggle_button = pod.find_element(
            By.CLASS_NAME,
            "pod-toggle-icon"
        )

        toggle_button.click()
        print(f"Expanded Pod {pod_code}")

        time.sleep(2)
    else:
        print(f"Pod {pod_code} already expanded")
    return pod



# =========================================================
# TOOLTIP
# =========================================================
def get_tooltip(driver):
    wait = WebDriverWait(driver, 20)

    tooltip = wait.until(
        EC.presence_of_element_located(
            (By.CLASS_NAME, "tooltip")
        )
    )

    return tooltip

# =========================================================
# CLOSE TOOLTIP
# =========================================================
def close_tooltip(tooltip):
    try:
        close_button = tooltip.find_element(
            By.CLASS_NAME,
            "tooltip-close"
        )

        close_button.click()
        time.sleep(1)
    except:
        pass


# =========================================================
# PARSE HEADER
# =========================================================
def parse_tooltip_header(tooltip):
    headers = tooltip.find_elements(
        By.CLASS_NAME,
        "tooltip-header"
    )

    location = ""
    serial = ""
    time_in_test = ""

    for header in headers:
        text = header.text.strip()

        if text.startswith("Location:"):
            location = text.replace(
                "Location:",
                ""
            ).strip()

        elif text.startswith("Serial:"):
            serial = text.replace(
                "Serial:",
                ""
            ).strip()
        elif text.startswith("Time in Test:"):
            time_in_test = text.replace(
                "Time in Test:",
                ""
            ).strip()
    return {
        "location": location,
        "rack_serial_number": serial,
        "time_in_test": time_in_test
    }


# =========================================================
# NAVIGATION
# =========================================================
def navigate_to_page(driver, base_url, target_path):
    target_url = base_url + target_path
    driver.get(target_url)
    print("Navigated to:", target_url)

    return target_url

# =========================================================
# NETWORK STATUS
# =========================================================
def get_network_status(element):
    try:
        title = element.get_attribute("title") or ""

        title_lower = title.lower()

        if "offline" in title_lower:
            return "Offline"

        elif "online" in title_lower:
            return "Online"

        elif "warning" in title_lower:
            return "Warning"

        return "Unknown"

    except Exception:
        return "Unknown"


# =========================================================
# POWER STATUS
# =========================================================
def get_power_status(td_element):
    try:
        wrapper = td_element.find_element(
            By.CLASS_NAME,
            "power-icon-wrapper"
        )

        classes = wrapper.get_attribute("class").lower()

        if "offline" in classes:
            return "Offline"

        elif "online" in classes:
            return "Online"

        return "Unknown"

    except Exception:
        return "Unknown"



# =========================================================
# IDLE TIME ALERT
# =========================================================
def is_idle_time_alert(idle_time_value, alert_minutes):

    try:
        total_minutes = 0

        # DAYS
        day_match = re.search(
            r"(\d+)d",
            idle_time_value
        )

        # HOURS
        hour_match = re.search(
            r"(\d+)h",
            idle_time_value
        )

        # MINUTES
        minute_match = re.search(
            r"(\d+)m",
            idle_time_value
        )

        # CONVERT DAYS -> MINUTES
        if day_match:
            total_minutes += (
                int(day_match.group(1)) * 24 * 60
            )

        # CONVERT HOURS -> MINUTES
        if hour_match:
            total_minutes += (
                int(hour_match.group(1)) * 60
            )

        # ADD MINUTES
        if minute_match:
            total_minutes += int(
                minute_match.group(1)
            )

        return total_minutes > int(alert_minutes)

    except Exception as e:
        print(f"Idle time parsing failed: {e}")
        return False

