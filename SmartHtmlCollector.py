import os
import csv
import logging
import random
import time
import hashlib
import urllib.request
import urllib.error

import config


def setup_directories():
    """Create html and logs directories if they don't exist."""
    os.makedirs(config.HTML_DIR, exist_ok=True)
    os.makedirs(config.LOGS_DIR, exist_ok=True)


def setup_logging():
    """Configure logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )


def log_failure(url: str, message: str) -> None:
    """Append failed URL and error message to CSV."""
    os.makedirs(os.path.dirname(config.FAILED_URLS_FILE), exist_ok=True)
    file_exists = os.path.exists(config.FAILED_URLS_FILE)

    with open(config.FAILED_URLS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["url", "error_message"])
        writer.writerow([url, message])


def url_to_filename(url: str) -> str:
    """Create a safe filename from URL using SHA-256 hash."""
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return f"{h}.html"


def fetch_and_save(url: str) -> None:
    """Fetch URL and save HTML to file with retry."""
    filename = url_to_filename(url)
    filepath = os.path.join(config.HTML_DIR, filename)

    # すでに取得済みならスキップ
    if os.path.exists(filepath):
        logging.info(f"[SKIP] Already downloaded: {url}")
        return

    headers = getattr(
        config,
        "HEADERS",
        {"User-Agent": "Mozilla/5.0 (compatible; SmartHtmlCollector/1.0)"}
    )
    req = urllib.request.Request(url, headers=headers)

    max_retry = int(getattr(config, "MAX_RETRY", 1))

    for attempt in range(1, max_retry + 1):
        try:
            logging.info(f"[GET] {url} (try {attempt}/{max_retry})")
            with urllib.request.urlopen(req, timeout=config.TIMEOUT) as resp:
                content = resp.read()
            with open(filepath, "wb") as f:
                f.write(content)
            logging.info(f"[OK] Saved to {filepath}")
            return
        except Exception as e:
            msg = f"{type(e).__name__}: {e}"
            logging.warning(f"[NG] {url} -> {msg}")
            if attempt == max_retry:
                log_failure(url, msg)
            else:
                wait = random.uniform(config.MIN_WAIT, config.MAX_WAIT)
                logging.info(f"Retry after {wait:.1f} sec...")
                time.sleep(wait)


def read_urls_from_csv():
    """Read URL list from CSV file specified in config.URLS_CSV."""
    urls = []
    with open(config.URLS_CSV, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            url = row[0].strip()
            if url.lower().startswith("http"):
                urls.append(url)
    return urls


def main():
    print("---- SmartHtml Collector Starting ----")

    setup_directories()
    setup_logging()

    urls = read_urls_from_csv()
    logging.info(f"Total URLs to fetch: {len(urls)}")

    for i, url in enumerate(urls, start=1):
        logging.info(f"=== [{i}/{len(urls)}] {url}")
        fetch_and_save(url)

        wait = random.uniform(config.MIN_WAIT, config.MAX_WAIT)
        logging.info(f"Sleep {wait:.1f} sec...")
        time.sleep(wait)

    logging.info("All done.")
    print("---- SmartHtml Collector Finished ----")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to close...")
