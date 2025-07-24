import time
import csv
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

def load_all_publications(driver, max_tries=10):
    """Click 'Show more' until all publications are loaded."""
    attempts = 0
    while attempts < max_tries:
        try:
            btn = driver.find_element(By.ID, "gsc_bpf_more")
            if 'disabled' in btn.get_attribute('class'):
                break
            before = len(driver.find_elements(By.CSS_SELECTOR, ".gsc_a_tr"))
            btn.click()
            time.sleep(2)
            after = len(driver.find_elements(By.CSS_SELECTOR, ".gsc_a_tr"))
            if after == before:
                attempts += 1
            else:
                attempts = 0
        except:
            break

def scrape_scholar_profile(url):
    """
    Scrape a single Google Scholar profile:
      – extract the author's name
      – load all pubs
      – return (name, single string of "Title (Cited by X); Title2 (Cited by Y); …")
    """
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(url)
    time.sleep(3)
    # 1) get the name
    author_name = driver.find_element(By.ID, "gsc_prf_in").text.strip()
    # 2) load all pubs
    load_all_publications(driver)
    # 3) collect and format
    entries = []
    for row in driver.find_elements(By.CSS_SELECTOR, ".gsc_a_tr"):
        title = row.find_element(By.CSS_SELECTOR, ".gsc_a_t a").text.strip()
        try:
            cites = row.find_element(By.CSS_SELECTOR, ".gsc_a_c a").text.strip() or "0"
        except:
            cites = "0"
        entries.append(f"{title} (Cited by {cites})")
    driver.quit()
    return author_name, "; ".join(entries)

if __name__ == "__main__":
    # Prepare output dict
    all_scholars = {}

    # Read URLs from Data.csv
    with open("Data.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            url = row.get("Google Scholar Link", "").strip()
            if not url:
                continue
            print(f"Scraping {url} …")
            name, pubs_str = scrape_scholar_profile(url)
            all_scholars[name] = pubs_str

    # Save everything into one JSON
    os.makedirs("scraped_data", exist_ok=True)
    out_path = "scraped_data/all_scholars.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_scholars, f, ensure_ascii=False, indent=4)

    print(f"\nAll profiles saved to {out_path}")