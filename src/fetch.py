"""
Fetch GBFS feeds from the ODPT public API and upload to HuggingFace.

Usage:
    python -m src.fetch --frequency realtime
    python -m src.fetch --frequency daily
"""

import argparse
import gzip
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE_URL = "https://api-public.odpt.org/api/v4/gbfs/{slug}/{feed}.json"
CONFIG_PATH = Path(__file__).parent.parent / "config" / "feeds.json"


def fetch_feed(slug: str, feed_name: str, retries: int = 3, timeout: int = 10) -> dict:
    url = BASE_URL.format(slug=slug, feed=feed_name)
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            data["poll_timestamp"] = datetime.now(timezone.utc).isoformat()
            return data
        except Exception as e:
            if attempt == retries:
                raise
            print(f"  Attempt {attempt} failed for {slug}/{feed_name}: {e}. Retrying...")
            time.sleep(2 * attempt)


def compress(data: dict) -> bytes:
    return gzip.compress(json.dumps(data, ensure_ascii=False).encode("utf-8"))


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def run(frequency: str):
    from src.upload import upload

    config = load_config()
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    datetime_str = now.strftime("%Y%m%d_%H%M")

    for provider, provider_cfg in config.items():
        feeds = provider_cfg["feeds"].get(frequency, [])
        if not feeds:
            continue
        for slug in provider_cfg["slugs"]:
            for feed_name in feeds:
                print(f"Fetching {slug}/{feed_name}...")
                try:
                    data = fetch_feed(slug, feed_name)
                    compressed = compress(data)

                    if frequency == "realtime":
                        hf_path = f"data/{slug}/{feed_name}/{datetime_str}.json.gz"
                    else:
                        hf_path = f"data/{slug}/{feed_name}/{date_str}.json.gz"

                    upload(compressed, hf_path)
                    print(f"  Uploaded to {hf_path}")
                except Exception as e:
                    print(f"  ERROR: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--frequency",
        choices=["realtime", "daily"],
        required=True,
        help="Which feeds to poll: realtime (station_status) or daily (static feeds)",
    )
    args = parser.parse_args()
    run(args.frequency)
