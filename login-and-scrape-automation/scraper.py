import csv
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()

URL = os.getenv("SITE_URL", "https://www.saucedemo.com")
EMAIL = os.getenv("SITE_EMAIL")
PASSWORD = os.getenv("SITE_PASSWORD")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
SLOW_DOWN = float(os.getenv("SLOW_DOWN", "6"))

SELECTORS = {
    "email": (By.ID, "user-name"),
    "password": (By.ID, "password"),
    "login_button": (By.ID, "login-button"),
    "item": (By.CLASS_NAME, "inventory_item"),
    "name": (By.CLASS_NAME, "inventory_item_name"),
    "price": (By.CLASS_NAME, "inventory_item_price"),
}

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(OUTPUT_DIR / "run.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)
def pause():
    time.sleep(SLOW_DOWN)

def create_driver():
    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,800")
    return webdriver.Chrome(options=options)

def login(driver, wait):
    log.info("Opening %s", URL)
    driver.get(URL)
    wait.until(EC.presence_of_element_located(SELECTORS["email"])).send_keys(EMAIL)
    driver.find_element(*SELECTORS["password"]).send_keys(PASSWORD)
    driver.find_element(*SELECTORS["login_button"]).click()
    wait.until(EC.presence_of_element_located(SELECTORS["item"]))
    pause() 
    log.info("Login successful")

def extract_items(driver):
    items = []
    for element in driver.find_elements(*SELECTORS["item"]):
        items.append({
            "name": element.find_element(*SELECTORS["name"]).text,
            "price": element.find_element(*SELECTORS["price"]).text,
            "scraped_at": datetime.now().isoformat(timespec="seconds"),
        })
    log.info("Extracted %d items", len(items))
    return items

def save_results(items):
    if not items:
        log.warning("No items to save")
        return

    csv_path = OUTPUT_DIR / f"items_{RUN_ID}.csv"
    json_path = OUTPUT_DIR / f"items_{RUN_ID}.json"

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=items[0].keys())
        writer.writeheader()
        writer.writerows(items)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)

    log.info("Saved %s and %s", csv_path, json_path)

def main():
    if not EMAIL or not PASSWORD:
        raise SystemExit("Set SITE_EMAIL and SITE_PASSWORD in your .env file")

    driver = create_driver()
    wait = WebDriverWait(driver, 10)
    try:
        login(driver, wait)
        items = extract_items(driver)
        save_results(items)
        driver.save_screenshot(str(OUTPUT_DIR / f"page_{RUN_ID}.png"))
    except Exception:
        log.exception("Run failed")
        driver.save_screenshot(str(OUTPUT_DIR / f"error_{RUN_ID}.png"))
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
