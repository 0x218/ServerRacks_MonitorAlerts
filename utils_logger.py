import os
import logging
from logging.handlers import RotatingFileHandler


# =========================================================
# LOG ALERT
# =========================================================
def log_alert(
        logger,
        header_data,
        server_data
):
    message = (
        f"{header_data['location']} | "
        f"Rack# {header_data['serial']} | "
        f"CT Loc {server_data['loc']} | "
        f"CT# {server_data['serial_number']} | "
        f"Network={server_data['network']} | "
        f"Power={server_data['power']} | "
        f"Status={server_data['status']} | "
        f"Station={server_data['station']} | "
        f"Idle Time={server_data['idle_time']}"
    )

    logger.info(message)



# =========================================================
# LOGGER
# =========================================================
def setup_logger(save_folder):
    os.makedirs(save_folder, exist_ok=True)

    log_path = os.path.join(
        save_folder,
        "alert.log"
    )

    logger = logging.getLogger("IBMRACK_ALERTS")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=5
    )

    formatter = logging.Formatter(
        "%(message)s"
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

