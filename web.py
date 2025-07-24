import json, re, time, logging
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup            # lighter than UnstructuredURLLoader
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm

CSV_PATH = "Data.csv"
OUT_PATH = "web_data.json"

# -----------------------------------------------------------------------------
# 1. Set up a single requests.Session with retry & friendly headers
# -----------------------------------------------------------------------------
session = requests.Session()
session.headers.update({
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0 Safari/537.36"),
})

retry = Retry(
    total=3,           # 3 attempts total
    backoff_factor=1,  # 1s, 2s, 4s between tries
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)
session.mount("https://", HTTPAdapter(max_retries=retry))
session.mount("http://",  HTTPAdapter(max_retries=retry))

# -----------------------------------------------------------------------------
# 2. Read CSV & normalise headers
# -----------------------------------------------------------------------------
df = pd.read_csv(CSV_PATH)
df.columns = df.columns.str.strip().str.lower().str.replace(":", "")

def col_like(name):
    return next(c for c in df.columns if name in c)

first_col, last_col = col_like("first name"), col_like("last name")
url_cols = [c for c in df.columns if any(k in c for k in ("webpage", "other"))]

# -----------------------------------------------------------------------------
# 3. Scrape row-by-row
# -----------------------------------------------------------------------------
output, bad_urls = {}, []

for _, row in tqdm(df.iterrows(), total=len(df), desc="Scraping"):

    fullname = f"{row.get(first_col, '')} {row.get(last_col, '')}".strip()
    if not fullname:
        continue

    # collect URLs
    urls = []
    for col in url_cols:
        cell = str(row.get(col, ""))
        urls += [u.rstrip(").,]") for u in re.findall(r"https?://\S+", cell)]
    urls = list(dict.fromkeys(urls))

    # fetch pages one at a time
    page_texts = []
    for url in urls:
        try:
            resp = session.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            page_texts.append(soup.get_text(separator="\n", strip=True))
            time.sleep(0.5)                # be nice – 2 req/s max
        except Exception as e:
            logging.warning(f"[{fullname}] {url} → {e}")
            bad_urls.append((fullname, url, str(e)))

    output[fullname] = "\n\n".join(page_texts)

# -----------------------------------------------------------------------------
# 4. Save results
# -----------------------------------------------------------------------------
Path(OUT_PATH).write_text(json.dumps(output, ensure_ascii=False, indent=2), "utf-8")
print(f"Done! Scraped {len(output)} people → {OUT_PATH}")

# optional: dump problem links
if bad_urls:
    Path("bad_urls.log").write_text(
        "\n".join(f"{n}\t{u}\t{err}" for n, u, err in bad_urls), "utf-8"
    )
    print(f"{len(bad_urls)} URLs failed – see bad_urls.log")
